"""SQLite-backed lead persistence for the generic cognithor.leads package."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any
from uuid import uuid4

from cognithor.leads.models import Lead, LeadStats, LeadStatus, ScanResult
from cognithor.utils.logging import get_logger

try:
    from cognithor.security.encrypted_db import compatible_row_factory as _row_factory_fn
except ImportError:

    def _row_factory_fn() -> type:  # type: ignore[misc]
        return sqlite3.Row


log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    post_id       TEXT UNIQUE NOT NULL,
    source_id     TEXT NOT NULL DEFAULT 'reddit',
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    body          TEXT DEFAULT '',
    author        TEXT DEFAULT '',
    created_utc   REAL DEFAULT 0,
    intent_score  INTEGER DEFAULT 0,
    score_reason  TEXT DEFAULT '',
    reply_draft   TEXT DEFAULT '',
    status        TEXT DEFAULT 'new',
    scan_id       TEXT DEFAULT '',
    received_at   REAL NOT NULL,
    subreddit     TEXT DEFAULT '',
    upvotes       INTEGER DEFAULT 0,
    num_comments  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lead_scans (
    id              TEXT PRIMARY KEY,
    started_at      REAL NOT NULL,
    finished_at     REAL DEFAULT 0,
    posts_checked   INTEGER DEFAULT 0,
    leads_found     INTEGER DEFAULT 0,
    subreddits      TEXT DEFAULT '',
    trigger         TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(intent_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_post_id ON leads(post_id);
CREATE INDEX IF NOT EXISTS idx_leads_source_id ON leads(source_id);

CREATE TABLE IF NOT EXISTS subreddit_profiles (
    subreddit       TEXT PRIMARY KEY,
    what_works      TEXT DEFAULT '',
    what_fails      TEXT DEFAULT '',
    optimal_length  INTEGER DEFAULT 0,
    optimal_tone    TEXT DEFAULT '',
    best_openings   TEXT DEFAULT '[]',
    avoid_patterns  TEXT DEFAULT '[]',
    sample_size     INTEGER DEFAULT 0,
    updated_at      REAL NOT NULL
);
"""


class LeadStore:
    """SQLite-backed lead storage for the generic leads package."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        try:
            from cognithor.security.encrypted_db import encrypted_connect

            self._conn = encrypted_connect(str(self._db_path), check_same_thread=False)
        except ImportError:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = _row_factory_fn()
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")

        # Back-compat migration for databases created before source_id was added.
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA table_info(leads)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if existing_cols and "source_id" not in existing_cols:
            cursor.execute("ALTER TABLE leads ADD COLUMN source_id TEXT NOT NULL DEFAULT 'reddit'")

        self._conn.executescript(_SCHEMA)
        return self._conn

    def save_lead(self, lead: Lead) -> None:
        """Insert or update a lead (upsert on post_id)."""
        self.conn.execute(
            """INSERT INTO leads
                (post_id, source_id, title, url, body, author, created_utc,
                 intent_score, score_reason, reply_draft, status, scan_id,
                 received_at, subreddit, upvotes, num_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id) DO UPDATE SET
                intent_score=excluded.intent_score,
                score_reason=excluded.score_reason,
                reply_draft=excluded.reply_draft,
                title=excluded.title,
                body=excluded.body,
                upvotes=excluded.upvotes,
                num_comments=excluded.num_comments,
                source_id=excluded.source_id
            """,
            (
                lead.post_id,
                lead.source_id,
                lead.title,
                lead.url,
                lead.body,
                lead.author,
                lead.created_utc,
                lead.intent_score,
                lead.score_reason,
                lead.reply_draft,
                lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                lead.scan_id,
                lead.received_at,
                lead.subreddit,
                lead.upvotes,
                lead.num_comments,
            ),
        )
        self.conn.commit()

    def get_lead(self, post_id: str) -> Lead | None:
        """Fetch a single lead by post_id."""
        row = self.conn.execute("SELECT * FROM leads WHERE post_id = ?", (post_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_lead(row)

    def get_leads(
        self,
        status: LeadStatus | None = None,
        min_score: int = 0,
        limit: int = 50,
        offset: int = 0,
        source_id: str | None = None,
    ) -> list[Lead]:
        """Return leads ordered by received_at DESC with optional filters."""
        query = "SELECT * FROM leads WHERE intent_score >= ?"
        params: list[Any] = [min_score]
        if status is not None:
            query += " AND status = ?"
            params.append(status.value if isinstance(status, LeadStatus) else status)
        if source_id is not None:
            query += " AND source_id = ?"
            params.append(source_id)
        query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_lead(r) for r in rows]

    def already_seen(self, post_id: str) -> bool:
        """Return True if a lead with this post_id already exists."""
        row = self.conn.execute("SELECT 1 FROM leads WHERE post_id = ?", (post_id,)).fetchone()
        return row is not None

    def get_stats(self) -> LeadStats:
        """Return aggregate statistics over all leads and scans."""
        total = self.conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        new = self.conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'").fetchone()[0]
        reviewed = self.conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'reviewed'"
        ).fetchone()[0]
        replied = self.conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'replied'"
        ).fetchone()[0]
        archived = self.conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'archived'"
        ).fetchone()[0]
        avg_row = self.conn.execute("SELECT AVG(intent_score) FROM leads").fetchone()
        avg_score = avg_row[0] if avg_row[0] is not None else 0.0
        sub_rows = self.conn.execute(
            "SELECT subreddit, COUNT(*) as cnt FROM leads"
            " GROUP BY subreddit ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        top_subs = [(r[0], r[1]) for r in sub_rows]
        scan_count = self.conn.execute("SELECT COUNT(*) FROM lead_scans").fetchone()[0]
        return LeadStats(
            total=total,
            new=new,
            reviewed=reviewed,
            replied=replied,
            archived=archived,
            avg_score=round(avg_score, 1),
            top_subreddits=top_subs,
            total_scans=scan_count,
        )

    def save_scan(self, scan: ScanResult) -> None:
        """Persist a completed ScanResult."""
        self.conn.execute(
            """INSERT INTO lead_scans
                (id, started_at, finished_at, posts_checked, leads_found, subreddits, trigger)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                scan.id,
                scan.started_at,
                scan.finished_at,
                scan.posts_checked,
                scan.leads_found,
                json.dumps(scan.subreddits_scanned),
                scan.trigger,
            ),
        )
        self.conn.commit()

    def get_scan_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent scan records as plain dicts."""
        rows = self.conn.execute(
            "SELECT * FROM lead_scans ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_top_performers(self, subreddit: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return top-performing leads for a subreddit, ranked by intent_score."""
        rows = self.conn.execute(
            """SELECT * FROM leads WHERE subreddit = ?
            ORDER BY intent_score DESC LIMIT ?""",
            (subreddit, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def save_profile(
        self,
        subreddit: str,
        what_works: str = "",
        what_fails: str = "",
        optimal_length: int = 0,
        optimal_tone: str = "",
        best_openings: str = "[]",
        avoid_patterns: str = "[]",
        sample_size: int = 0,
    ) -> None:
        """Insert or fully replace a subreddit style profile."""
        self.conn.execute(
            """INSERT INTO subreddit_profiles
                (subreddit, what_works, what_fails, optimal_length, optimal_tone,
                 best_openings, avoid_patterns, sample_size, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subreddit) DO UPDATE SET
                what_works=excluded.what_works, what_fails=excluded.what_fails,
                optimal_length=excluded.optimal_length, optimal_tone=excluded.optimal_tone,
                best_openings=excluded.best_openings, avoid_patterns=excluded.avoid_patterns,
                sample_size=excluded.sample_size, updated_at=excluded.updated_at""",
            (
                subreddit,
                what_works,
                what_fails,
                optimal_length,
                optimal_tone,
                best_openings,
                avoid_patterns,
                sample_size,
                time.time(),
            ),
        )
        self.conn.commit()

    def get_profile(self, subreddit: str) -> dict[str, Any] | None:
        """Fetch a subreddit style profile, or None if not found."""
        row = self.conn.execute(
            "SELECT * FROM subreddit_profiles WHERE subreddit = ?", (subreddit,)
        ).fetchone()
        return dict(row) if row else None

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _row_to_lead(row: Any) -> Lead:
        """Convert a sqlite3.Row to a Lead dataclass."""
        try:
            source_id = row["source_id"]
        except (IndexError, KeyError):
            source_id = "reddit"
        return Lead(
            post_id=row["post_id"],
            source_id=source_id,
            title=row["title"],
            url=row["url"],
            body=row["body"],
            author=row["author"],
            created_utc=row["created_utc"],
            intent_score=row["intent_score"],
            score_reason=row["score_reason"],
            reply_draft=row["reply_draft"],
            status=LeadStatus(row["status"]),
            scan_id=row["scan_id"],
            received_at=row["received_at"],
            subreddit=row["subreddit"],
            upvotes=row["upvotes"],
            num_comments=row["num_comments"],
        )


# Suppress unused import warning — uuid4 is used in save_template if ever re-added
__all__ = ["LeadStore"]
_ = uuid4  # keep import live for future template methods
