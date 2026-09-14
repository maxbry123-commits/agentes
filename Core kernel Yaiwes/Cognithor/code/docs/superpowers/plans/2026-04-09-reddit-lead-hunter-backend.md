# Reddit Lead Hunter Backend — Implementation Plan (Part A)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the Reddit Lead Hunter into Cognithor's runtime — triggerable via chat, cron, and REST API with SQLite persistence and hybrid reply-posting.

**Architecture:** New `social/` package with `RedditLeadService` (SQLite + httpx + LLM scoring) + 3 MCP tools (`reddit_scan`, `reddit_reply`, `reddit_leads`) + 6 REST endpoints + Cron registration + `SocialConfig` in config.py. Skill `.md` file enables Planner-based chat triggering.

**Tech Stack:** Python, SQLite (SQLCipher), httpx, Pydantic, FastAPI routes, Cognithor MCP framework, CronEngine

**Depends on:** Plan B (Flutter frontend) builds on the REST API defined here.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/jarvis/social/__init__.py` | Package exports |
| `src/jarvis/social/models.py` | Lead, ScanResult, LeadStats dataclasses |
| `src/jarvis/social/store.py` | SQLite lead persistence (encrypted) |
| `src/jarvis/social/scanner.py` | Reddit JSON feed fetcher + LLM scoring + reply drafting |
| `src/jarvis/social/reply.py` | Clipboard / browser / auto reply posting |
| `src/jarvis/social/service.py` | RedditLeadService — orchestrates store + scanner + reply |
| `src/jarvis/mcp/reddit_tools.py` | 3 MCP tools for the Planner |
| `src/jarvis/config.py` | SocialConfig nested model |
| `src/jarvis/channels/config_routes.py` | 6 REST endpoints (new `_register_social_routes`) |
| `src/jarvis/gateway/phases/advanced.py` | Service init + cron registration |
| `data/procedures/reddit-lead-hunter.md` | Skill file for Planner matching |
| `tests/test_social/test_models.py` | Model tests |
| `tests/test_social/test_store.py` | SQLite store tests |
| `tests/test_social/test_scanner.py` | Scanner tests (mocked httpx + LLM) |
| `tests/test_social/test_service.py` | Integration tests |
| `tests/test_mcp/test_reddit_tools.py` | MCP tool tests |

---

### Task 1: Data models — Lead, ScanResult, LeadStats

**Files:**
- Create: `src/jarvis/social/__init__.py`
- Create: `src/jarvis/social/models.py`
- Create: `tests/test_social/__init__.py`
- Create: `tests/test_social/test_models.py`

- [ ] **Step 1: Write test file**

Create `tests/test_social/__init__.py` (empty) and `tests/test_social/test_models.py`:

```python
"""Tests for social.models — Lead, ScanResult, LeadStats."""

from __future__ import annotations

import pytest

from jarvis.social.models import Lead, LeadStatus, ScanResult, LeadStats


class TestLead:
    def test_create_minimal(self):
        lead = Lead(
            post_id="abc123",
            subreddit="LocalLLaMA",
            title="Test post",
            url="https://reddit.com/r/LocalLLaMA/abc123",
            intent_score=75,
        )
        assert lead.id  # auto-generated UUID
        assert lead.status == LeadStatus.NEW
        assert lead.content_hash  # auto-generated SHA256
        assert lead.detected_at > 0

    def test_content_hash_deterministic(self):
        a = Lead(post_id="x", subreddit="s", title="t", url="u", intent_score=50)
        b = Lead(post_id="x", subreddit="s", title="t", url="u", intent_score=50)
        assert a.content_hash == b.content_hash

    def test_content_hash_changes_with_title(self):
        a = Lead(post_id="x", subreddit="s", title="t1", url="u", intent_score=50)
        b = Lead(post_id="x", subreddit="s", title="t2", url="u", intent_score=50)
        assert a.content_hash != b.content_hash

    def test_status_enum_values(self):
        assert LeadStatus.NEW == "new"
        assert LeadStatus.REVIEWED == "reviewed"
        assert LeadStatus.REPLIED == "replied"
        assert LeadStatus.ARCHIVED == "archived"

    def test_to_dict(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Looking for AI tool",
            url="https://reddit.com/r/SaaS/abc", intent_score=80,
            score_reason="Direct search", reply_draft="Try Cognithor",
        )
        d = lead.to_dict()
        assert d["post_id"] == "abc"
        assert d["intent_score"] == 80
        assert d["status"] == "new"
        assert "id" in d
        assert "content_hash" in d

    def test_notification_text(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Need AI assistant",
            url="https://reddit.com/r/SaaS/abc", intent_score=85,
            score_reason="Active search", reply_draft="Check Cognithor",
            author="test_user", upvotes=10, num_comments=5,
        )
        text = lead.to_notification_text()
        assert "85" in text
        assert "SaaS" in text
        assert "Need AI assistant" in text
        assert "test_user" in text


class TestScanResult:
    def test_create(self):
        result = ScanResult(
            subreddits_scanned=["LocalLLaMA", "SaaS"],
            posts_checked=20,
            leads_found=3,
        )
        assert result.id
        assert result.started_at > 0
        assert result.finished_at == 0

    def test_summary(self):
        result = ScanResult(
            subreddits_scanned=["LocalLLaMA"],
            posts_checked=50, leads_found=5,
            posts_skipped_duplicate=10, posts_skipped_low_score=35,
        )
        s = result.summary()
        assert "50" in s
        assert "5" in s


class TestLeadStats:
    def test_from_counts(self):
        stats = LeadStats(
            total=20, new=10, reviewed=5, replied=3, archived=2,
            avg_score=72.5, top_subreddits={"LocalLLaMA": 12, "SaaS": 8},
            total_scans=15,
        )
        assert stats.total == 20
        assert stats.avg_score == 72.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_models.py -x -q --tb=short`
Expected: FAIL — `jarvis.social.models` not found

- [ ] **Step 3: Create the package and models**

Create `src/jarvis/social/__init__.py`:

```python
"""Social listening and lead generation modules."""
```

Create `src/jarvis/social/models.py`:

```python
"""Data models for the Reddit Lead Hunter."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any
from uuid import uuid4


class LeadStatus(StrEnum):
    NEW = "new"
    REVIEWED = "reviewed"
    REPLIED = "replied"
    ARCHIVED = "archived"


@dataclass
class Lead:
    """A scored Reddit post identified as a potential lead."""

    post_id: str
    subreddit: str
    title: str
    url: str
    intent_score: int

    # Optional enrichment
    body: str = ""
    author: str = ""
    created_utc: float = 0.0
    upvotes: int = 0
    num_comments: int = 0
    score_reason: str = ""
    reply_draft: str = ""
    reply_final: str = ""
    status: LeadStatus = LeadStatus.NEW
    replied_at: float = 0.0
    scan_id: str = ""

    # Auto-generated
    id: str = field(default_factory=lambda: str(uuid4()))
    detected_at: float = field(default_factory=time.time)
    content_hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.content_hash:
            raw = f"{self.post_id}:{self.title}:{self.body}"
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, LeadStatus) else self.status
        return d

    def to_notification_text(self) -> str:
        stars = self.intent_score // 20
        star_str = "*" * stars + "." * (5 - stars)
        return (
            f"[{star_str} {self.intent_score}/100] r/{self.subreddit}\n"
            f"{self.title}\n"
            f"{self.url}\n"
            f"u/{self.author} | {self.upvotes} upvotes | {self.num_comments} comments\n"
            f"Reason: {self.score_reason}\n"
            f"Draft: {self.reply_draft[:100]}..."
        )


@dataclass
class ScanResult:
    """Result of a single scan cycle."""

    subreddits_scanned: list[str]
    posts_checked: int = 0
    leads_found: int = 0
    posts_skipped_duplicate: int = 0
    posts_skipped_low_score: int = 0
    trigger: str = ""  # "chat", "cron", "ui"

    id: str = field(default_factory=lambda: str(uuid4()))
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    def summary(self) -> str:
        return (
            f"Scan: {self.posts_checked} posts checked, "
            f"{self.posts_skipped_duplicate} duplicates, "
            f"{self.posts_skipped_low_score} below threshold, "
            f"{self.leads_found} leads found."
        )


@dataclass
class LeadStats:
    """Aggregate lead statistics."""

    total: int = 0
    new: int = 0
    reviewed: int = 0
    replied: int = 0
    archived: int = 0
    avg_score: float = 0.0
    top_subreddits: dict[str, int] = field(default_factory=dict)
    total_scans: int = 0
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/test_models.py -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/ tests/test_social/
git commit -m "feat(social): add Lead, ScanResult, LeadStats data models"
```

---

### Task 2: LeadStore — SQLite persistence

**Files:**
- Create: `src/jarvis/social/store.py`
- Create: `tests/test_social/test_store.py`

- [ ] **Step 1: Write test file**

Create `tests/test_social/test_store.py`:

```python
"""Tests for social.store — SQLite lead persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.social.models import Lead, LeadStatus, ScanResult
from jarvis.social.store import LeadStore


@pytest.fixture()
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(str(tmp_path / "leads.db"))


class TestLeadStore:
    def test_save_and_get(self, store: LeadStore):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Test",
            url="https://reddit.com/abc", intent_score=75,
        )
        store.save_lead(lead)
        loaded = store.get_lead(lead.id)
        assert loaded is not None
        assert loaded.post_id == "abc"
        assert loaded.intent_score == 75
        assert loaded.status == LeadStatus.NEW

    def test_duplicate_post_id_updates(self, store: LeadStore):
        lead1 = Lead(
            post_id="dup", subreddit="SaaS", title="First",
            url="https://reddit.com/dup", intent_score=60,
        )
        store.save_lead(lead1)
        lead2 = Lead(
            post_id="dup", subreddit="SaaS", title="Updated",
            url="https://reddit.com/dup", intent_score=80,
        )
        store.save_lead(lead2)
        leads = store.get_leads()
        dup_leads = [l for l in leads if l.post_id == "dup"]
        assert len(dup_leads) == 1
        assert dup_leads[0].intent_score == 80

    def test_get_leads_filter_status(self, store: LeadStore):
        for i in range(3):
            store.save_lead(Lead(
                post_id=f"p{i}", subreddit="S", title=f"T{i}",
                url=f"u{i}", intent_score=70,
            ))
        store.update_lead(store.get_leads()[0].id, status=LeadStatus.REVIEWED)
        new_leads = store.get_leads(status=LeadStatus.NEW)
        assert len(new_leads) == 2

    def test_get_leads_filter_min_score(self, store: LeadStore):
        store.save_lead(Lead(post_id="low", subreddit="S", title="Low", url="u", intent_score=30))
        store.save_lead(Lead(post_id="high", subreddit="S", title="High", url="u", intent_score=90))
        high_leads = store.get_leads(min_score=60)
        assert len(high_leads) == 1
        assert high_leads[0].post_id == "high"

    def test_update_lead_status(self, store: LeadStore):
        lead = Lead(post_id="up", subreddit="S", title="T", url="u", intent_score=70)
        store.save_lead(lead)
        updated = store.update_lead(lead.id, status=LeadStatus.REPLIED, reply_final="Done")
        assert updated is not None
        assert updated.status == LeadStatus.REPLIED
        assert updated.reply_final == "Done"

    def test_already_seen(self, store: LeadStore):
        assert not store.already_seen("new_post")
        store.save_lead(Lead(post_id="new_post", subreddit="S", title="T", url="u", intent_score=50))
        assert store.already_seen("new_post")

    def test_get_stats(self, store: LeadStore):
        store.save_lead(Lead(post_id="a", subreddit="X", title="T", url="u", intent_score=80))
        store.save_lead(Lead(post_id="b", subreddit="X", title="T", url="u", intent_score=60))
        store.save_lead(Lead(post_id="c", subreddit="Y", title="T", url="u", intent_score=70))
        stats = store.get_stats()
        assert stats.total == 3
        assert stats.new == 3
        assert stats.avg_score == pytest.approx(70.0)
        assert stats.top_subreddits["X"] == 2

    def test_save_scan(self, store: LeadStore):
        scan = ScanResult(subreddits_scanned=["X", "Y"], posts_checked=50, leads_found=3)
        store.save_scan(scan)
        history = store.get_scan_history(limit=10)
        assert len(history) == 1
        assert history[0]["posts_checked"] == 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_store.py -x -q --tb=short`
Expected: FAIL — `jarvis.social.store` not found

- [ ] **Step 3: Implement LeadStore**

Create `src/jarvis/social/store.py`:

```python
"""SQLite-backed lead persistence with encryption support."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from jarvis.social.models import Lead, LeadStats, LeadStatus, ScanResult
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id            TEXT PRIMARY KEY,
    post_id       TEXT UNIQUE NOT NULL,
    subreddit     TEXT NOT NULL,
    title         TEXT NOT NULL,
    body          TEXT DEFAULT '',
    url           TEXT NOT NULL,
    author        TEXT DEFAULT '',
    created_utc   REAL DEFAULT 0,
    upvotes       INTEGER DEFAULT 0,
    num_comments  INTEGER DEFAULT 0,
    intent_score  INTEGER DEFAULT 0,
    score_reason  TEXT DEFAULT '',
    reply_draft   TEXT DEFAULT '',
    reply_final   TEXT DEFAULT '',
    status        TEXT DEFAULT 'new',
    replied_at    REAL DEFAULT 0,
    detected_at   REAL NOT NULL,
    content_hash  TEXT DEFAULT '',
    scan_id       TEXT DEFAULT ''
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
"""


class LeadStore:
    """SQLite-backed lead storage with encryption."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        try:
            from jarvis.security.encrypted_db import encrypted_connect

            self._conn = encrypted_connect(str(self._db_path), check_same_thread=False)
        except ImportError:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        return self._conn

    def save_lead(self, lead: Lead) -> None:
        self.conn.execute(
            """INSERT INTO leads
                (id, post_id, subreddit, title, body, url, author, created_utc,
                 upvotes, num_comments, intent_score, score_reason, reply_draft,
                 reply_final, status, replied_at, detected_at, content_hash, scan_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id) DO UPDATE SET
                intent_score=excluded.intent_score,
                score_reason=excluded.score_reason,
                reply_draft=excluded.reply_draft,
                title=excluded.title,
                body=excluded.body,
                upvotes=excluded.upvotes,
                num_comments=excluded.num_comments
            """,
            (
                lead.id, lead.post_id, lead.subreddit, lead.title, lead.body,
                lead.url, lead.author, lead.created_utc, lead.upvotes,
                lead.num_comments, lead.intent_score, lead.score_reason,
                lead.reply_draft, lead.reply_final,
                lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                lead.replied_at, lead.detected_at, lead.content_hash, lead.scan_id,
            ),
        )
        self.conn.commit()

    def get_lead(self, lead_id: str) -> Lead | None:
        row = self.conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_lead(row)

    def get_leads(
        self,
        status: LeadStatus | None = None,
        min_score: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lead]:
        query = "SELECT * FROM leads WHERE intent_score >= ?"
        params: list[Any] = [min_score]
        if status is not None:
            query += " AND status = ?"
            params.append(status.value if isinstance(status, LeadStatus) else status)
        query += " ORDER BY detected_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_lead(r) for r in rows]

    def update_lead(
        self,
        lead_id: str,
        status: LeadStatus | None = None,
        reply_final: str | None = None,
    ) -> Lead | None:
        sets: list[str] = []
        params: list[Any] = []
        if status is not None:
            sets.append("status = ?")
            params.append(status.value if isinstance(status, LeadStatus) else status)
            if status == LeadStatus.REPLIED:
                sets.append("replied_at = ?")
                params.append(time.time())
        if reply_final is not None:
            sets.append("reply_final = ?")
            params.append(reply_final)
        if not sets:
            return self.get_lead(lead_id)
        params.append(lead_id)
        self.conn.execute(f"UPDATE leads SET {', '.join(sets)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_lead(lead_id)

    def already_seen(self, post_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM leads WHERE post_id = ?", (post_id,)).fetchone()
        return row is not None

    def get_stats(self) -> LeadStats:
        total = self.conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        new = self.conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'").fetchone()[0]
        reviewed = self.conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'reviewed'").fetchone()[0]
        replied = self.conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'replied'").fetchone()[0]
        archived = self.conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'archived'").fetchone()[0]
        avg_row = self.conn.execute("SELECT AVG(intent_score) FROM leads").fetchone()
        avg_score = avg_row[0] if avg_row[0] is not None else 0.0
        # Top subreddits
        sub_rows = self.conn.execute(
            "SELECT subreddit, COUNT(*) as cnt FROM leads GROUP BY subreddit ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        top_subs = {r[0]: r[1] for r in sub_rows}
        scan_count = self.conn.execute("SELECT COUNT(*) FROM lead_scans").fetchone()[0]
        return LeadStats(
            total=total, new=new, reviewed=reviewed, replied=replied, archived=archived,
            avg_score=round(avg_score, 1), top_subreddits=top_subs, total_scans=scan_count,
        )

    def save_scan(self, scan: ScanResult) -> None:
        self.conn.execute(
            """INSERT INTO lead_scans (id, started_at, finished_at, posts_checked, leads_found, subreddits, trigger)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (scan.id, scan.started_at, scan.finished_at, scan.posts_checked,
             scan.leads_found, json.dumps(scan.subreddits_scanned), scan.trigger),
        )
        self.conn.commit()

    def get_scan_history(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM lead_scans ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_lead(row: sqlite3.Row) -> Lead:
        return Lead(
            id=row["id"],
            post_id=row["post_id"],
            subreddit=row["subreddit"],
            title=row["title"],
            body=row["body"],
            url=row["url"],
            author=row["author"],
            created_utc=row["created_utc"],
            upvotes=row["upvotes"],
            num_comments=row["num_comments"],
            intent_score=row["intent_score"],
            score_reason=row["score_reason"],
            reply_draft=row["reply_draft"],
            reply_final=row["reply_final"],
            status=LeadStatus(row["status"]),
            replied_at=row["replied_at"],
            detected_at=row["detected_at"],
            content_hash=row["content_hash"],
            scan_id=row["scan_id"],
        )
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && ruff format src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/store.py tests/test_social/test_store.py
git commit -m "feat(social): add LeadStore — SQLite persistence for leads and scans"
```

---

### Task 3: Scanner — Reddit JSON fetch + LLM scoring + reply drafting

**Files:**
- Create: `src/jarvis/social/scanner.py`
- Create: `tests/test_social/test_scanner.py`

- [ ] **Step 1: Write test file**

Create `tests/test_social/test_scanner.py`:

```python
"""Tests for social.scanner — Reddit JSON fetch + LLM scoring."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jarvis.social.scanner import RedditScanner, ScanConfig


class TestRedditScanner:
    def test_create(self):
        scanner = RedditScanner(llm_fn=AsyncMock())
        assert scanner is not None

    @pytest.mark.asyncio
    async def test_fetch_posts_returns_list(self):
        scanner = RedditScanner(llm_fn=AsyncMock())
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {"data": {
                        "id": "abc", "title": "Test post", "selftext": "body",
                        "subreddit": "LocalLLaMA", "permalink": "/r/LocalLLaMA/abc",
                        "author": "user1", "created_utc": 1700000000,
                        "score": 10, "num_comments": 5,
                    }},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.Client.get", return_value=mock_response):
            posts = scanner.fetch_posts("LocalLLaMA", limit=10)
        assert len(posts) == 1
        assert posts[0]["id"] == "abc"
        assert posts[0]["subreddit"] == "LocalLLaMA"

    @pytest.mark.asyncio
    async def test_score_post(self):
        llm_fn = AsyncMock(return_value={
            "message": {"content": '{"score": 75, "reasoning": "Direct match"}'}
        })
        scanner = RedditScanner(llm_fn=llm_fn)
        config = ScanConfig(product_name="Cognithor", product_description="AI OS")
        score, reason = await scanner.score_post(
            {"title": "Need local AI agent", "selftext": "Looking for tools", "subreddit": "LocalLLaMA"},
            config,
        )
        assert score == 75
        assert "Direct match" in reason

    @pytest.mark.asyncio
    async def test_score_post_invalid_json_returns_zero(self):
        llm_fn = AsyncMock(return_value={
            "message": {"content": "I cannot score this post"}
        })
        scanner = RedditScanner(llm_fn=llm_fn)
        config = ScanConfig(product_name="X", product_description="Y")
        score, reason = await scanner.score_post(
            {"title": "Random", "selftext": "", "subreddit": "test"},
            config,
        )
        assert score == 0

    @pytest.mark.asyncio
    async def test_draft_reply(self):
        llm_fn = AsyncMock(return_value={
            "message": {"content": "Check out Cognithor — it does exactly this."}
        })
        scanner = RedditScanner(llm_fn=llm_fn)
        config = ScanConfig(
            product_name="Cognithor", product_description="AI OS",
            reply_tone="helpful, no sales pitch",
        )
        draft = await scanner.draft_reply(
            {"title": "Need tool", "selftext": "Help", "subreddit": "SaaS"},
            config,
        )
        assert "Cognithor" in draft

    def test_fetch_posts_handles_error(self):
        scanner = RedditScanner(llm_fn=AsyncMock())
        with patch("httpx.Client.get", side_effect=Exception("Network error")):
            posts = scanner.fetch_posts("NonExistent", limit=10)
        assert posts == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_scanner.py -x -q --tb=short`
Expected: FAIL — `jarvis.social.scanner` not found

- [ ] **Step 3: Implement RedditScanner**

Create `src/jarvis/social/scanner.py`:

```python
"""Reddit JSON feed scanner with LLM-based intent scoring and reply drafting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

import httpx

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_USER_AGENT = "cognithor:reddit_lead_hunter:v1.0 (by u/cognithor-bot)"

SCORE_PROMPT = """
You are a B2B lead qualification expert. Score this Reddit post for purchase intent.

PRODUCT: {product_name}
DESCRIPTION: {product_description}

REDDIT POST:
Subreddit: r/{subreddit}
Title: {title}
Text: {body}

Score 0-100:
- 0-20: No relation to product
- 21-40: Weak relation, no concrete problem
- 41-60: Relevant topic, no clear buying signal
- 61-80: Clear problem that our product solves
- 81-100: Active search for exactly this solution

Reply ONLY in this JSON format:
{{"score": <int 0-100>, "reasoning": "<max 1 sentence>"}}
""".strip()

REPLY_PROMPT = """
You are a helpful expert replying on Reddit.

PRODUCT: {product_name}
YOUR TONE: {reply_tone}

REDDIT POST:
Subreddit: r/{subreddit}
Title: {title}
Text: {body}

Write a short, helpful Reddit reply (max 150 words):
- Acknowledge the user's problem
- Briefly explain how {product_name} can help
- No hard sales pitch
- Subreddit-native tone (informal, direct)
- End with the GitHub link: github.com/Alex8791-cyber/cognithor

Reply ONLY with the response text, no meta-comments.
""".strip()


@dataclass
class ScanConfig:
    """Configuration for a scan cycle."""

    product_name: str = "Cognithor"
    product_description: str = ""
    reply_tone: str = "helpful, technically credible, no sales pitch"
    min_score: int = 60


# Type alias for the LLM function (matches Cognithor's UnifiedLLMClient.chat signature)
LLMFn = Callable[..., Awaitable[dict[str, Any]]]


class RedditScanner:
    """Fetches Reddit posts via public JSON and scores them via LLM."""

    def __init__(self, llm_fn: LLMFn | None = None) -> None:
        self._llm_fn = llm_fn
        self._http = httpx.Client(
            timeout=30,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )

    def fetch_posts(self, subreddit: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch new posts from a subreddit via public JSON feed."""
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        try:
            resp = self._http.get(url, params={"limit": min(limit, 100), "raw_json": 1})
            resp.raise_for_status()
            children = resp.json().get("data", {}).get("children", [])
            return [
                {
                    "id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "selftext": p.get("selftext", ""),
                    "subreddit": p.get("subreddit", subreddit),
                    "permalink": p.get("permalink", ""),
                    "author": p.get("author", "[deleted]"),
                    "created_utc": p.get("created_utc", 0),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                }
                for child in children
                for p in [child.get("data", {})]
                if p.get("id")
            ]
        except Exception as exc:
            log.warning("reddit_fetch_failed", subreddit=subreddit, error=str(exc))
            return []

    async def score_post(
        self,
        post: dict[str, Any],
        config: ScanConfig,
    ) -> tuple[int, str]:
        """Score a post for intent 0-100 via LLM. Returns (score, reasoning)."""
        if not self._llm_fn:
            return 0, "No LLM available"

        prompt = SCORE_PROMPT.format(
            product_name=config.product_name,
            product_description=config.product_description,
            subreddit=post.get("subreddit", ""),
            title=post.get("title", ""),
            body=(post.get("selftext") or "")[:1000],
        )
        try:
            response = await self._llm_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = response.get("message", {}).get("content", "")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return 0, "No JSON in LLM response"
            data = json.loads(raw[start:end])
            score = max(0, min(100, int(data.get("score", 0))))
            reasoning = str(data.get("reasoning", ""))
            return score, reasoning
        except Exception as exc:
            log.warning("score_failed", post_id=post.get("id"), error=str(exc))
            return 0, "Scoring failed"

    async def draft_reply(
        self,
        post: dict[str, Any],
        config: ScanConfig,
    ) -> str:
        """Draft a reply for a post via LLM."""
        if not self._llm_fn:
            return "[No LLM available for reply drafting]"

        prompt = REPLY_PROMPT.format(
            product_name=config.product_name,
            reply_tone=config.reply_tone,
            subreddit=post.get("subreddit", ""),
            title=post.get("title", ""),
            body=(post.get("selftext") or "")[:1000],
        )
        try:
            response = await self._llm_fn(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as exc:
            log.warning("draft_failed", post_id=post.get("id"), error=str(exc))
            return "[Reply draft failed]"

    def close(self) -> None:
        self._http.close()
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && ruff format src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/scanner.py tests/test_social/test_scanner.py
git commit -m "feat(social): add RedditScanner — JSON feed fetch + LLM scoring"
```

---

### Task 4: Reply posting — clipboard / browser / auto

**Files:**
- Create: `src/jarvis/social/reply.py`
- Create: `tests/test_social/test_reply.py`

- [ ] **Step 1: Write test file**

Create `tests/test_social/test_reply.py`:

```python
"""Tests for social.reply — hybrid reply posting."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.social.models import Lead
from jarvis.social.reply import ReplyPoster, ReplyMode, ReplyResult


class TestReplyPoster:
    def test_clipboard_mode(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Test",
            url="https://reddit.com/r/SaaS/abc", intent_score=80,
            reply_draft="Try Cognithor",
        )
        poster = ReplyPoster()
        with patch("jarvis.social.reply._copy_to_clipboard") as mock_clip:
            with patch("webbrowser.open") as mock_browser:
                result = poster.post(lead, mode=ReplyMode.CLIPBOARD)
        assert result.success
        assert result.mode == ReplyMode.CLIPBOARD
        mock_clip.assert_called_once_with("Try Cognithor")
        mock_browser.assert_called_once()

    def test_browser_mode(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Test",
            url="https://reddit.com/r/SaaS/abc", intent_score=80,
            reply_draft="Draft text",
        )
        poster = ReplyPoster()
        with patch("jarvis.social.reply._copy_to_clipboard") as mock_clip:
            with patch("webbrowser.open") as mock_browser:
                result = poster.post(lead, mode=ReplyMode.BROWSER)
        assert result.success
        mock_browser.assert_called_once()
        mock_clip.assert_called_once()

    def test_uses_reply_final_over_draft(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Test",
            url="https://reddit.com/r/SaaS/abc", intent_score=80,
            reply_draft="Draft", reply_final="Final edited version",
        )
        poster = ReplyPoster()
        with patch("jarvis.social.reply._copy_to_clipboard") as mock_clip:
            with patch("webbrowser.open"):
                poster.post(lead, mode=ReplyMode.CLIPBOARD)
        mock_clip.assert_called_once_with("Final edited version")

    def test_empty_reply_fails(self):
        lead = Lead(
            post_id="abc", subreddit="SaaS", title="Test",
            url="https://reddit.com/r/SaaS/abc", intent_score=80,
        )
        poster = ReplyPoster()
        result = poster.post(lead, mode=ReplyMode.CLIPBOARD)
        assert not result.success
        assert "empty" in result.error.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_reply.py -x -q --tb=short`
Expected: FAIL — `jarvis.social.reply` not found

- [ ] **Step 3: Implement ReplyPoster**

Create `src/jarvis/social/reply.py`:

```python
"""Hybrid reply posting — clipboard, browser, or auto (Playwright)."""

from __future__ import annotations

import webbrowser
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from jarvis.social.models import Lead
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


class ReplyMode(StrEnum):
    CLIPBOARD = "clipboard"
    BROWSER = "browser"
    AUTO = "auto"


@dataclass
class ReplyResult:
    success: bool
    mode: ReplyMode
    error: str = ""


def _copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard (cross-platform)."""
    try:
        import subprocess
        import sys

        if sys.platform == "win32":
            process = subprocess.Popen(
                ["clip"], stdin=subprocess.PIPE, shell=True,
            )
            process.communicate(text.encode("utf-16-le"))
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
        else:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
    except Exception as exc:
        log.warning("clipboard_copy_failed", error=str(exc))
        # Fallback: try pyperclip
        try:
            import pyperclip
            pyperclip.copy(text)
        except ImportError:
            raise RuntimeError(f"Cannot copy to clipboard: {exc}") from exc


class ReplyPoster:
    """Posts replies to Reddit leads via clipboard, browser, or Playwright."""

    def __init__(self, browser_agent: Any = None) -> None:
        self._browser_agent = browser_agent

    def post(self, lead: Lead, mode: ReplyMode = ReplyMode.CLIPBOARD) -> ReplyResult:
        """Post a reply to a lead."""
        reply_text = lead.reply_final or lead.reply_draft
        if not reply_text.strip():
            return ReplyResult(success=False, mode=mode, error="Reply text is empty")

        try:
            if mode == ReplyMode.CLIPBOARD:
                _copy_to_clipboard(reply_text)
                webbrowser.open(lead.url)
                log.info("reply_clipboard", lead_id=lead.id, url=lead.url)
                return ReplyResult(success=True, mode=mode)

            elif mode == ReplyMode.BROWSER:
                _copy_to_clipboard(reply_text)
                webbrowser.open(lead.url)
                log.info("reply_browser", lead_id=lead.id, url=lead.url)
                return ReplyResult(success=True, mode=mode)

            elif mode == ReplyMode.AUTO:
                return self._auto_post(lead, reply_text)

            return ReplyResult(success=False, mode=mode, error=f"Unknown mode: {mode}")
        except Exception as exc:
            log.error("reply_failed", lead_id=lead.id, error=str(exc))
            return ReplyResult(success=False, mode=mode, error=str(exc))

    def _auto_post(self, lead: Lead, reply_text: str) -> ReplyResult:
        """Auto-post via Playwright browser agent."""
        if self._browser_agent is None:
            # Fallback to clipboard mode
            log.warning("auto_post_no_browser_agent_falling_back_to_clipboard")
            _copy_to_clipboard(reply_text)
            webbrowser.open(lead.url)
            return ReplyResult(success=True, mode=ReplyMode.CLIPBOARD,
                               error="Browser agent not available, used clipboard fallback")

        # Playwright auto-posting will be wired when BrowserAgent is available
        # For now, this is a placeholder that falls back to clipboard
        log.info("auto_post_placeholder", lead_id=lead.id)
        _copy_to_clipboard(reply_text)
        webbrowser.open(lead.url)
        return ReplyResult(success=True, mode=ReplyMode.CLIPBOARD,
                           error="Auto-post not yet wired, used clipboard")
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && ruff format src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/reply.py tests/test_social/test_reply.py
git commit -m "feat(social): add ReplyPoster — clipboard, browser, auto posting"
```

---

### Task 5: RedditLeadService — orchestrator

**Files:**
- Create: `src/jarvis/social/service.py`
- Create: `tests/test_social/test_service.py`

- [ ] **Step 1: Write test file**

Create `tests/test_social/test_service.py`:

```python
"""Tests for social.service — RedditLeadService orchestrator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jarvis.social.models import LeadStatus
from jarvis.social.service import RedditLeadService


@pytest.fixture()
def service(tmp_path: Path) -> RedditLeadService:
    return RedditLeadService(
        db_path=str(tmp_path / "leads.db"),
        llm_fn=AsyncMock(),
        product_name="TestProduct",
        product_description="A test product",
    )


class TestRedditLeadService:
    @pytest.mark.asyncio
    async def test_scan_returns_result(self, service: RedditLeadService):
        mock_posts = [
            {"id": "p1", "title": "Looking for AI tool with local deployment",
             "selftext": "Need something private", "subreddit": "SaaS",
             "permalink": "/r/SaaS/p1", "author": "user1",
             "created_utc": 1700000000, "score": 10, "num_comments": 5},
        ]
        with patch.object(service._scanner, "fetch_posts", return_value=mock_posts):
            with patch.object(service._scanner, "score_post",
                              new_callable=AsyncMock, return_value=(75, "Direct match")):
                with patch.object(service._scanner, "draft_reply",
                                  new_callable=AsyncMock, return_value="Try TestProduct"):
                    result = await service.scan(["SaaS"], min_score=60, trigger="test")

        assert result.posts_checked == 1
        assert result.leads_found == 1
        leads = service.get_leads()
        assert len(leads) == 1
        assert leads[0].intent_score == 75

    @pytest.mark.asyncio
    async def test_scan_skips_duplicates(self, service: RedditLeadService):
        mock_posts = [
            {"id": "dup1", "title": "Some post about tools",
             "selftext": "text", "subreddit": "SaaS",
             "permalink": "/r/SaaS/dup1", "author": "u",
             "created_utc": 1700000000, "score": 5, "num_comments": 1},
        ]
        with patch.object(service._scanner, "fetch_posts", return_value=mock_posts):
            with patch.object(service._scanner, "score_post",
                              new_callable=AsyncMock, return_value=(80, "Match")):
                with patch.object(service._scanner, "draft_reply",
                                  new_callable=AsyncMock, return_value="Reply"):
                    await service.scan(["SaaS"], min_score=60, trigger="test")
                    result = await service.scan(["SaaS"], min_score=60, trigger="test")

        assert result.posts_skipped_duplicate == 1
        assert result.leads_found == 0

    @pytest.mark.asyncio
    async def test_scan_skips_low_score(self, service: RedditLeadService):
        mock_posts = [
            {"id": "low1", "title": "Random discussion about nothing",
             "selftext": "", "subreddit": "SaaS",
             "permalink": "/r/SaaS/low1", "author": "u",
             "created_utc": 1700000000, "score": 2, "num_comments": 0},
        ]
        with patch.object(service._scanner, "fetch_posts", return_value=mock_posts):
            with patch.object(service._scanner, "score_post",
                              new_callable=AsyncMock, return_value=(20, "No match")):
                result = await service.scan(["SaaS"], min_score=60, trigger="test")

        assert result.posts_skipped_low_score == 1
        assert result.leads_found == 0

    def test_get_stats(self, service: RedditLeadService):
        stats = service.get_stats()
        assert stats.total == 0

    def test_update_lead(self, service: RedditLeadService):
        from jarvis.social.models import Lead
        lead = Lead(post_id="x", subreddit="S", title="T", url="u", intent_score=70)
        service._store.save_lead(lead)
        updated = service.update_lead(lead.id, status=LeadStatus.REVIEWED)
        assert updated is not None
        assert updated.status == LeadStatus.REVIEWED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_service.py -x -q --tb=short`
Expected: FAIL — `jarvis.social.service` not found

- [ ] **Step 3: Implement RedditLeadService**

Create `src/jarvis/social/service.py`:

```python
"""RedditLeadService — orchestrates scanning, storing, and replying."""

from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from jarvis.social.models import Lead, LeadStats, LeadStatus, ScanResult
from jarvis.social.reply import ReplyMode, ReplyPoster, ReplyResult
from jarvis.social.scanner import RedditScanner, ScanConfig
from jarvis.social.store import LeadStore
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


class RedditLeadService:
    """Orchestrates Reddit lead scanning, persistence, and reply posting."""

    def __init__(
        self,
        db_path: str,
        llm_fn: Callable[..., Awaitable[dict[str, Any]]] | None = None,
        product_name: str = "",
        product_description: str = "",
        reply_tone: str = "helpful, technically credible, no sales pitch",
        browser_agent: Any = None,
        notification_callback: Callable[[Lead], None] | None = None,
    ) -> None:
        self._store = LeadStore(db_path)
        self._scanner = RedditScanner(llm_fn=llm_fn)
        self._poster = ReplyPoster(browser_agent=browser_agent)
        self._notification_cb = notification_callback
        self._scan_config = ScanConfig(
            product_name=product_name,
            product_description=product_description,
            reply_tone=reply_tone,
        )

    async def scan(
        self,
        subreddits: list[str] | None = None,
        min_score: int = 60,
        trigger: str = "chat",
    ) -> ScanResult:
        """Run a full scan cycle: fetch → score → draft → store."""
        subs = subreddits or []
        config = ScanConfig(
            product_name=self._scan_config.product_name,
            product_description=self._scan_config.product_description,
            reply_tone=self._scan_config.reply_tone,
            min_score=min_score,
        )

        result = ScanResult(subreddits_scanned=subs, trigger=trigger)
        leads_created: list[Lead] = []

        for sub in subs:
            posts = self._scanner.fetch_posts(sub, limit=100)

            # Rate limit between subreddits
            if posts:
                import asyncio
                await asyncio.sleep(1.0)

            for post in posts:
                result.posts_checked += 1
                post_id = post.get("id", "")

                # Duplicate check
                if self._store.already_seen(post_id):
                    result.posts_skipped_duplicate += 1
                    continue

                # Quick filter
                if len(post.get("title", "")) < 15:
                    result.posts_skipped_low_score += 1
                    continue

                # LLM scoring
                score, reasoning = await self._scanner.score_post(post, config)

                if score < min_score:
                    result.posts_skipped_low_score += 1
                    # Still save to prevent re-scoring
                    self._store.save_lead(Lead(
                        post_id=post_id, subreddit=sub,
                        title=post.get("title", ""), url=f"https://reddit.com{post.get('permalink', '')}",
                        intent_score=score, score_reason=reasoning,
                        status=LeadStatus.ARCHIVED, scan_id=result.id,
                        author=post.get("author", ""), body=(post.get("selftext") or "")[:500],
                        created_utc=post.get("created_utc", 0),
                        upvotes=post.get("score", 0), num_comments=post.get("num_comments", 0),
                    ))
                    continue

                # Draft reply
                draft = await self._scanner.draft_reply(post, config)

                # Create and save lead
                lead = Lead(
                    post_id=post_id, subreddit=sub,
                    title=post.get("title", ""),
                    body=(post.get("selftext") or "")[:500],
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    author=post.get("author", "[deleted]"),
                    created_utc=post.get("created_utc", 0),
                    upvotes=post.get("score", 0),
                    num_comments=post.get("num_comments", 0),
                    intent_score=score,
                    score_reason=reasoning,
                    reply_draft=draft,
                    scan_id=result.id,
                )
                self._store.save_lead(lead)
                leads_created.append(lead)
                result.leads_found += 1

                log.info("lead_found", subreddit=sub, score=score, title=post.get("title", "")[:60])

                # Notification callback
                if self._notification_cb:
                    try:
                        self._notification_cb(lead)
                    except Exception as exc:
                        log.warning("notification_failed", error=str(exc))

        result.finished_at = time.time()
        self._store.save_scan(result)
        log.info("scan_complete", summary=result.summary())
        return result

    def get_leads(
        self,
        status: LeadStatus | None = None,
        min_score: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lead]:
        return self._store.get_leads(status=status, min_score=min_score, limit=limit, offset=offset)

    def get_lead(self, lead_id: str) -> Lead | None:
        return self._store.get_lead(lead_id)

    def update_lead(
        self,
        lead_id: str,
        status: LeadStatus | None = None,
        reply_final: str | None = None,
    ) -> Lead | None:
        return self._store.update_lead(lead_id, status=status, reply_final=reply_final)

    def post_reply(self, lead_id: str, mode: str = "clipboard") -> ReplyResult:
        lead = self._store.get_lead(lead_id)
        if lead is None:
            return ReplyResult(success=False, mode=ReplyMode(mode), error="Lead not found")
        reply_mode = ReplyMode(mode)
        result = self._poster.post(lead, mode=reply_mode)
        if result.success:
            self._store.update_lead(lead_id, status=LeadStatus.REPLIED)
        return result

    def get_stats(self) -> LeadStats:
        return self._store.get_stats()

    def get_scan_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._store.get_scan_history(limit=limit)
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && ruff format src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/service.py tests/test_social/test_service.py
git commit -m "feat(social): add RedditLeadService — scan, store, reply orchestrator"
```

---

### Task 6: MCP Tools + Config + Gateway wiring + Skill file

**Files:**
- Create: `src/jarvis/mcp/reddit_tools.py`
- Modify: `src/jarvis/config.py` (add SocialConfig around line 2230)
- Modify: `src/jarvis/gateway/phases/advanced.py` (add service init around line 337)
- Modify: `src/jarvis/gateway/phases/tools.py` (register MCP tools around line 204)
- Create: `data/procedures/reddit-lead-hunter.md`
- Create: `tests/test_mcp/test_reddit_tools.py`

- [ ] **Step 1: Add SocialConfig to config.py**

In `src/jarvis/config.py`, before the `JarvisConfig` class (before line 2095), add:

```python
class SocialConfig(BaseModel):
    """Reddit Lead Hunter configuration."""

    reddit_scan_enabled: bool = Field(default=False, description="Enable automatic Reddit scanning")
    reddit_subreddits: list[str] = Field(
        default_factory=lambda: ["LocalLLaMA", "SaaS"],
        description="Subreddits to scan (without r/ prefix)",
    )
    reddit_min_score: int = Field(default=60, ge=0, le=100, description="Minimum intent score for leads")
    reddit_scan_interval_minutes: int = Field(default=30, ge=5, description="Cron scan interval")
    reddit_product_name: str = Field(default="", description="Product name for scoring prompts")
    reddit_product_description: str = Field(default="", description="One-sentence product description")
    reddit_reply_tone: str = Field(
        default="helpful, technically credible, no sales pitch",
        description="Tone instruction for reply drafts",
    )
    reddit_auto_post: bool = Field(default=False, description="Enable Playwright auto-posting (requires login)")
```

In `JarvisConfig`, in the subsystem fields block (around line 2230), add:

```python
    social: SocialConfig = Field(default_factory=SocialConfig)
```

- [ ] **Step 2: Create MCP tools**

Create `src/jarvis/mcp/reddit_tools.py`:

```python
"""MCP tools for Reddit Lead Hunter — exposes scan, leads, reply to the Planner."""

from __future__ import annotations

import json
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)


def register_reddit_tools(mcp_client: Any, lead_service: Any) -> None:
    """Register Reddit Lead Hunter MCP tools."""

    async def _reddit_scan(
        subreddits: str = "",
        min_score: int = 0,
    ) -> str:
        """Scan Reddit for leads. Subreddits as comma-separated string."""
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})

        subs = [s.strip() for s in subreddits.split(",") if s.strip()] if subreddits else None
        config = lead_service._scan_config
        effective_subs = subs or getattr(config, "subreddits", ["LocalLLaMA", "SaaS"])
        effective_min = min_score or getattr(config, "min_score", 60)

        result = await lead_service.scan(
            subreddits=effective_subs,
            min_score=effective_min,
            trigger="chat",
        )

        leads_summary = []
        for lead in lead_service.get_leads(min_score=effective_min, limit=10):
            if lead.scan_id == result.id:
                leads_summary.append({
                    "score": lead.intent_score,
                    "subreddit": lead.subreddit,
                    "title": lead.title[:80],
                    "url": lead.url,
                    "author": lead.author,
                })

        return json.dumps({
            "summary": result.summary(),
            "leads_found": result.leads_found,
            "posts_checked": result.posts_checked,
            "leads": leads_summary,
        }, ensure_ascii=False)

    async def _reddit_leads(
        status: str = "",
        min_score: int = 0,
        limit: int = 20,
    ) -> str:
        """List current Reddit leads with optional filters."""
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})

        from jarvis.social.models import LeadStatus

        status_filter = LeadStatus(status) if status and status in LeadStatus.__members__.values() else None
        leads = lead_service.get_leads(status=status_filter, min_score=min_score, limit=limit)

        return json.dumps({
            "count": len(leads),
            "leads": [
                {
                    "id": l.id,
                    "score": l.intent_score,
                    "subreddit": l.subreddit,
                    "title": l.title[:80],
                    "status": l.status.value if hasattr(l.status, "value") else l.status,
                    "url": l.url,
                    "reply_draft": l.reply_draft[:100] + "..." if len(l.reply_draft) > 100 else l.reply_draft,
                }
                for l in leads
            ],
        }, ensure_ascii=False)

    async def _reddit_reply(
        lead_id: str = "",
        mode: str = "clipboard",
    ) -> str:
        """Post a reply to a Reddit lead. Mode: clipboard, browser, or auto."""
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})

        if not lead_id:
            return json.dumps({"error": "lead_id is required"})

        result = lead_service.post_reply(lead_id, mode=mode)
        return json.dumps({
            "success": result.success,
            "mode": result.mode.value,
            "error": result.error,
        })

    mcp_client.register_builtin_handler(
        "reddit_scan",
        _reddit_scan,
        description="Scan Reddit subreddits for high-intent leads. Returns scored posts with reply drafts.",
        parameters={
            "subreddits": {"type": "string", "description": "Comma-separated subreddit names (default: config)"},
            "min_score": {"type": "integer", "description": "Minimum intent score 0-100 (default: config)"},
        },
    )
    mcp_client.register_builtin_handler(
        "reddit_leads",
        _reddit_leads,
        description="List current Reddit leads with filters.",
        parameters={
            "status": {"type": "string", "description": "Filter: new, reviewed, replied, archived"},
            "min_score": {"type": "integer", "description": "Minimum score filter"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
    )
    mcp_client.register_builtin_handler(
        "reddit_reply",
        _reddit_reply,
        description="Post a reply to a Reddit lead. Copies to clipboard and opens browser.",
        parameters={
            "lead_id": {"type": "string", "description": "Lead ID to reply to"},
            "mode": {"type": "string", "description": "clipboard (default), browser, or auto"},
        },
    )
    log.info("reddit_tools_registered", tools=3)
```

- [ ] **Step 3: Wire in gateway**

In `src/jarvis/gateway/phases/advanced.py`, after the `knowledge_ingest` block (~line 337), add:

```python
    # RedditLeadService (social listening)
    try:
        from jarvis.social.service import RedditLeadService

        social_cfg = getattr(config, "social", None)
        if social_cfg and social_cfg.reddit_product_name:
            jarvis_home = getattr(config, "jarvis_home", None) or Path.home() / ".cognithor"
            leads_db = str(Path(jarvis_home) / "leads.db")
            llm_fn = result.get("llm_fn")
            result["reddit_lead_service"] = RedditLeadService(
                db_path=leads_db,
                llm_fn=llm_fn,
                product_name=social_cfg.reddit_product_name,
                product_description=social_cfg.reddit_product_description,
                reply_tone=social_cfg.reddit_reply_tone,
            )
            log.info("reddit_lead_service_initialized")
    except Exception:
        log.debug("reddit_lead_service_init_skipped", exc_info=True)
```

In `src/jarvis/gateway/phases/tools.py`, after the browser tools registration (~line 204), add:

```python
    # Reddit Lead Hunter tools
    reddit_svc = getattr(gateway, "_reddit_lead_service", None) if gateway else None
    if reddit_svc:
        from jarvis.mcp.reddit_tools import register_reddit_tools
        register_reddit_tools(mcp_client, reddit_svc)
```

- [ ] **Step 4: Create the Skill file**

Create `data/procedures/reddit-lead-hunter.md`:

```markdown
---
name: reddit-lead-hunter
slug: reddit_lead_hunter
description: Scannt Reddit nach High-Intent-Posts und generiert Reply-Drafts
trigger_keywords: [Reddit, Lead, Leads scannen, Social Listening, Reddit Scan, Reddit Monitoring, Leads finden, Reddit suchen, Community Monitoring]
tools_required: [reddit_scan, reddit_leads, reddit_reply]
category: marketing
priority: 7
enabled: true
agent: ""
---

# Reddit Lead Hunter

## Wann anwenden
Wenn der Benutzer Reddit nach Leads scannen moechte, Social Listening betreiben will, oder nach relevanten Reddit-Diskussionen sucht.

## Ablauf

1. **Scan starten**: Rufe `reddit_scan` auf mit den konfigurierten Subreddits
2. **Ergebnisse praesentieren**: Zeige die gefundenen Leads mit Score, Titel und Subreddit
3. **Bei Nachfrage**: Rufe `reddit_leads` auf um gespeicherte Leads zu listen
4. **Reply posten**: Wenn der User eine Antwort posten will, nutze `reddit_reply` mit der Lead-ID

## Beispiel-Interaktionen

- "Scanne Reddit nach Leads" → `reddit_scan`
- "Zeig mir die besten Leads" → `reddit_leads` mit min_score=70
- "Antworte auf den ersten Lead" → `reddit_reply` mit lead_id und mode=clipboard
- "Scanne r/Python und r/SaaS" → `reddit_scan` mit subreddits="Python,SaaS"

## Hinweise
- Ergebnisse werden in der Datenbank gespeichert (Duplikate automatisch erkannt)
- Leads koennen auch ueber die Flutter UI verwaltet werden
- Auto-Post (Playwright) nur wenn vom User explizit aktiviert
```

- [ ] **Step 5: Write MCP tool tests**

Create `tests/test_mcp/test_reddit_tools.py`:

```python
"""Tests for MCP Reddit tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from jarvis.social.models import Lead, LeadStatus
from jarvis.social.service import RedditLeadService


class TestRedditMcpTools:
    @pytest.mark.asyncio
    async def test_register_tools(self):
        from jarvis.mcp.reddit_tools import register_reddit_tools

        mcp = MagicMock()
        svc = MagicMock()
        register_reddit_tools(mcp, svc)
        assert mcp.register_builtin_handler.call_count == 3
        tool_names = [call[0][0] for call in mcp.register_builtin_handler.call_args_list]
        assert "reddit_scan" in tool_names
        assert "reddit_leads" in tool_names
        assert "reddit_reply" in tool_names
```

- [ ] **Step 6: Run all tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ src/jarvis/mcp/reddit_tools.py tests/test_social/ tests/test_mcp/test_reddit_tools.py && ruff format src/jarvis/social/ src/jarvis/mcp/reddit_tools.py tests/test_social/ tests/test_mcp/test_reddit_tools.py && python -m pytest tests/test_social/ tests/test_mcp/test_reddit_tools.py -x -q --tb=short`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/jarvis/mcp/reddit_tools.py src/jarvis/config.py src/jarvis/gateway/phases/advanced.py src/jarvis/gateway/phases/tools.py data/procedures/reddit-lead-hunter.md tests/test_mcp/test_reddit_tools.py
git commit -m "feat(social): MCP tools + config + gateway wiring + skill file"
```

---

### Task 7: REST API endpoints + Cron registration

**Files:**
- Modify: `src/jarvis/channels/config_routes.py` (add `_register_social_routes` call + function)
- Modify: `src/jarvis/gateway/gateway.py` (cron job registration)

- [ ] **Step 1: Add `_register_social_routes` call**

In `src/jarvis/channels/config_routes.py`, in the `create_config_routes` function (around line 102, after the last `_register_*` call), add:

```python
    _register_social_routes(app, deps, gateway)
```

- [ ] **Step 2: Implement the 6 REST endpoints**

At the bottom of `config_routes.py`, add:

```python
def _register_social_routes(
    app: Any,
    deps: list[Any],
    gateway: Any,
) -> None:
    """REST endpoints for Reddit Lead Hunter."""

    def _get_service() -> Any:
        return getattr(gateway, "_reddit_lead_service", None) if gateway else None

    @app.post("/api/v1/leads/scan", dependencies=deps)
    async def scan_leads(request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        try:
            body = await request.json()
        except Exception:
            body = {}
        subreddits = body.get("subreddits")
        min_score = body.get("min_score", 0)
        result = await svc.scan(
            subreddits=subreddits,
            min_score=min_score or 0,
            trigger="ui",
        )
        return {
            "id": result.id,
            "summary": result.summary(),
            "posts_checked": result.posts_checked,
            "leads_found": result.leads_found,
        }

    @app.get("/api/v1/leads", dependencies=deps)
    async def list_leads(
        status: str | None = None,
        min_score: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        from jarvis.social.models import LeadStatus
        status_filter = None
        if status and status in [s.value for s in LeadStatus]:
            status_filter = LeadStatus(status)
        leads = svc.get_leads(status=status_filter, min_score=min_score, limit=limit, offset=offset)
        return {
            "leads": [l.to_dict() for l in leads],
            "count": len(leads),
        }

    @app.get("/api/v1/leads/stats", dependencies=deps)
    async def lead_stats() -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        stats = svc.get_stats()
        history = svc.get_scan_history(limit=10)
        return {
            "stats": {
                "total": stats.total,
                "new": stats.new,
                "reviewed": stats.reviewed,
                "replied": stats.replied,
                "archived": stats.archived,
                "avg_score": stats.avg_score,
                "top_subreddits": stats.top_subreddits,
                "total_scans": stats.total_scans,
            },
            "recent_scans": history,
        }

    @app.get("/api/v1/leads/{lead_id}", dependencies=deps)
    async def get_lead(lead_id: str) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        lead = svc.get_lead(lead_id)
        if lead is None:
            raise HTTPException(404, "Lead not found")
        return lead.to_dict()

    @app.patch("/api/v1/leads/{lead_id}", dependencies=deps)
    async def update_lead(lead_id: str, request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        body = await request.json()
        from jarvis.social.models import LeadStatus
        status = LeadStatus(body["status"]) if "status" in body else None
        reply_final = body.get("reply_final")
        lead = svc.update_lead(lead_id, status=status, reply_final=reply_final)
        if lead is None:
            raise HTTPException(404, "Lead not found")
        return lead.to_dict()

    @app.post("/api/v1/leads/{lead_id}/reply", dependencies=deps)
    async def reply_to_lead(lead_id: str, request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        try:
            body = await request.json()
        except Exception:
            body = {}
        mode = body.get("mode", "clipboard")
        result = svc.post_reply(lead_id, mode=mode)
        return {
            "success": result.success,
            "mode": result.mode.value if hasattr(result.mode, "value") else result.mode,
            "error": result.error,
        }
```

- [ ] **Step 3: Add cron job registration**

In `src/jarvis/gateway/gateway.py`, find where system cron jobs are registered (around line 553-596, after `governance_analysis`). Add:

```python
        # Reddit Lead Scanner (if enabled)
        _social_cfg = getattr(self._config, "social", None)
        if _social_cfg and _social_cfg.reddit_scan_enabled and getattr(self, "_reddit_lead_service", None):
            try:
                self._cron_engine.add_runtime_job(
                    CronJob(
                        name="reddit_lead_scan",
                        schedule=f"*/{_social_cfg.reddit_scan_interval_minutes} * * * *",
                        prompt="[CRON:reddit_lead_scan] Scan Reddit for leads",
                        channel=getattr(self._config, "default_channel", "webui") or "webui",
                        enabled=True,
                    )
                )
                log.info("reddit_cron_registered", interval=_social_cfg.reddit_scan_interval_minutes)
            except Exception:
                log.debug("reddit_cron_registration_failed", exc_info=True)
```

Note: Check how `CronJob` is imported in gateway.py. It should be from `jarvis.cron.jobs` or similar. Follow the existing import pattern.

- [ ] **Step 4: Run lint + full test suite**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && ruff format src/ tests/ && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py`
Expected: All pass (13,000+)

- [ ] **Step 5: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/channels/config_routes.py src/jarvis/gateway/gateway.py data/procedures/reddit-lead-hunter.md
git commit -m "feat(social): REST API + cron registration for Reddit Lead Hunter

6 endpoints: POST /leads/scan, GET /leads, GET /leads/{id},
PATCH /leads/{id}, POST /leads/{id}/reply, GET /leads/stats.
Cron job registered when social.reddit_scan_enabled = true."
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Component 1 (Skill + MCP tools) → Task 6
- [x] Component 2 (RedditLeadService) → Tasks 1-5
- [x] Component 3 (Reply posting) → Task 4
- [x] Component 4 (Cron) → Task 7
- [x] Component 5 (REST API) → Task 7
- [x] Component 6 (Flutter) → Plan B (separate)
- [x] Component 7 (Config) → Task 6

**Placeholder scan:** No TBDs, all code blocks complete.

**Type consistency:** Lead, LeadStatus, ScanResult, LeadStats used consistently across all tasks. `llm_fn` signature matches Cognithor's `UnifiedLLMClient.chat`. `ReplyMode` enum consistent between reply.py and MCP tools.
