"""SQLite catalog of HuggingFace -> GCS model mirrors.

Records which models have been mirrored from HF to GCS via
``scripts/iris/mirror_hf_to_gcs.py`` so future launches can skip
re-mirroring. Same shape as ``hpc.iris_job_registry``; lives at
``~/.ot-agent/state/model_mirrors.db``.

The on-GCS truth is each repo's ``<gcs_uri>/.mirror_manifest.json``
(written by ``mirror_hf_to_gcs.py``); this module's SQLite is a
local cache + index so the launcher doesn't need to hit GCS on
every submit.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from hpc.local_paths import PATHS, ensure as ensure_local_paths


DB_PATH: Path = PATHS.state / "model_mirrors.db"
MANIFEST_FILENAME = ".mirror_manifest.json"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS mirrors (
    hf_repo        TEXT PRIMARY KEY,
    gcs_uri        TEXT NOT NULL,            -- gs://bucket/prefix/<hf_repo>/
    mirrored_at    TEXT NOT NULL,            -- ISO-8601 UTC
    size_bytes     INTEGER,
    file_count     INTEGER,
    iris_job_id    TEXT,
    notes          TEXT
);
"""


@dataclass(frozen=True)
class MirrorRecord:
    hf_repo: str
    gcs_uri: str
    mirrored_at: str
    size_bytes: Optional[int]
    file_count: Optional[int]
    iris_job_id: Optional[str]
    notes: Optional[str]

    def to_dict(self) -> dict:
        return {
            "hf_repo": self.hf_repo,
            "gcs_uri": self.gcs_uri,
            "mirrored_at": self.mirrored_at,
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
            "iris_job_id": self.iris_job_id,
            "notes": self.notes,
        }


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    ensure_local_paths(PATHS.home, PATHS.state)
    conn = sqlite3.connect(str(DB_PATH), isolation_level=None, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_SCHEMA)
        yield conn
    finally:
        conn.close()


def _row_to_record(row: sqlite3.Row) -> MirrorRecord:
    return MirrorRecord(
        hf_repo=row["hf_repo"],
        gcs_uri=row["gcs_uri"],
        mirrored_at=row["mirrored_at"],
        size_bytes=row["size_bytes"],
        file_count=row["file_count"],
        iris_job_id=row["iris_job_id"],
        notes=row["notes"],
    )


def register(
    *,
    hf_repo: str,
    gcs_uri: str,
    mirrored_at_iso: str,
    size_bytes: Optional[int] = None,
    file_count: Optional[int] = None,
    iris_job_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
    """Insert or replace one mirror entry."""
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO mirrors (
                hf_repo, gcs_uri, mirrored_at, size_bytes,
                file_count, iris_job_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hf_repo) DO UPDATE SET
                gcs_uri=excluded.gcs_uri,
                mirrored_at=excluded.mirrored_at,
                size_bytes=excluded.size_bytes,
                file_count=excluded.file_count,
                iris_job_id=excluded.iris_job_id,
                notes=excluded.notes
            """,
            (
                hf_repo,
                gcs_uri,
                mirrored_at_iso,
                size_bytes,
                file_count,
                iris_job_id,
                notes,
            ),
        )
        conn.execute("COMMIT")


def lookup(hf_repo: str) -> Optional[MirrorRecord]:
    """Return the cached record for an HF repo, or None if unknown."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM mirrors WHERE hf_repo = ?", (hf_repo,)
        ).fetchone()
    return _row_to_record(row) if row else None


def list_all() -> list[MirrorRecord]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM mirrors ORDER BY mirrored_at DESC"
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def forget(hf_repo: str) -> bool:
    """Remove the entry; does NOT delete GCS objects. Returns True if removed."""
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute("DELETE FROM mirrors WHERE hf_repo = ?", (hf_repo,))
        conn.execute("COMMIT")
        return cur.rowcount > 0


def refresh_from_gcs(gcs_prefix: str, *, verbose: bool = False) -> list[MirrorRecord]:
    """Walk a GCS prefix for ``.mirror_manifest.json`` files and register them.

    Use after a manual mirror or to rebuild the local cache from scratch.
    Requires fsspec + gcsfs (already in OT-Agent's deps).
    """
    import gcsfs

    fs = gcsfs.GCSFileSystem()
    gcs_prefix = gcs_prefix.rstrip("/")

    # Walk two levels deep — org/name layout.
    found: list[MirrorRecord] = []
    try:
        manifests = fs.glob(f"{gcs_prefix}/*/*/" + MANIFEST_FILENAME)
    except FileNotFoundError:
        return found

    for path in manifests:
        gs_path = path if path.startswith("gs://") else f"gs://{path}"
        try:
            raw = fs.cat_file(gs_path).decode("utf-8")
            data = json.loads(raw)
        except Exception as e:
            if verbose:
                print(f"[mirror-registry] skip {gs_path}: {e}")
            continue
        hf_repo = data.get("hf_repo")
        if not hf_repo:
            continue
        gcs_uri = gs_path.rsplit("/", 1)[0]  # strip /<manifest>
        record_kwargs = dict(
            hf_repo=hf_repo,
            gcs_uri=gcs_uri,
            mirrored_at_iso=data.get("mirrored_at", ""),
            size_bytes=data.get("size_bytes"),
            file_count=data.get("file_count"),
            iris_job_id=data.get("iris_job_id"),
            notes=data.get("notes"),
        )
        register(**record_kwargs)
        found.append(
            MirrorRecord(
                hf_repo=hf_repo,
                gcs_uri=gcs_uri,
                mirrored_at=record_kwargs["mirrored_at_iso"],
                size_bytes=record_kwargs["size_bytes"],
                file_count=record_kwargs["file_count"],
                iris_job_id=record_kwargs["iris_job_id"],
                notes=record_kwargs["notes"],
            )
        )
        if verbose:
            print(f"[mirror-registry] registered {hf_repo} -> {gcs_uri}")
    return found


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------


def _humanize_bytes(n: Optional[int]) -> str:
    if n is None:
        return "-"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:7.1f} {unit}"
        n //= 1024
    return f"{n} ?"


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(
        prog="python -m hpc.model_mirror_registry",
        description="Local catalog of HuggingFace -> GCS model mirrors.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="Show all registered mirrors.")
    pl.add_argument("--json", action="store_true", help="JSON output.")

    ps = sub.add_parser("show", help="Show one entry by HF repo.")
    ps.add_argument("hf_repo")

    pa = sub.add_parser(
        "add",
        help="Manually register a mirror "
        "(post-hoc, when the mirror job didn't "
        "write a manifest).",
    )
    pa.add_argument("--hf-repo", required=True)
    pa.add_argument(
        "--gcs-uri", required=True, help="gs:// URI of the mirror directory."
    )
    pa.add_argument(
        "--mirrored-at", default=None, help="ISO-8601 timestamp; defaults to now."
    )
    pa.add_argument("--iris-job-id", default=None)
    pa.add_argument("--notes", default=None)

    pf = sub.add_parser("forget", help="Remove an entry (does NOT delete GCS).")
    pf.add_argument("hf_repo")

    pr = sub.add_parser(
        "refresh",
        help="Scan a GCS prefix for .mirror_manifest.json "
        "files and populate the local cache.",
    )
    pr.add_argument("--gcs-prefix", default="gs://marin-eu-west4/ot-agent/models")

    args = p.parse_args(argv)

    if args.cmd == "list":
        rows = list_all()
        if args.json:
            print(json.dumps([r.to_dict() for r in rows], indent=2))
            return 0
        if not rows:
            print("No mirrors registered. Use `add` or `refresh` to populate.")
            return 0
        header = (
            f"{'HF_REPO':<55} {'SIZE':>10}  {'FILES':>6}  {'MIRRORED_AT':<25}  GCS_URI"
        )
        print(header)
        print("-" * len(header))
        for r in rows:
            print(
                f"{r.hf_repo:<55} {_humanize_bytes(r.size_bytes):>10}  "
                f"{(r.file_count if r.file_count is not None else '-'):>6}  "
                f"{r.mirrored_at:<25}  {r.gcs_uri}"
            )
        return 0

    if args.cmd == "show":
        rec = lookup(args.hf_repo)
        if rec is None:
            print(f"Not found: {args.hf_repo}", file=sys.stderr)
            return 1
        print(json.dumps(rec.to_dict(), indent=2))
        return 0

    if args.cmd == "add":
        from datetime import datetime, timezone

        ts = args.mirrored_at or datetime.now(timezone.utc).isoformat()
        register(
            hf_repo=args.hf_repo,
            gcs_uri=args.gcs_uri.rstrip("/"),
            mirrored_at_iso=ts,
            iris_job_id=args.iris_job_id,
            notes=args.notes,
        )
        print(f"Registered {args.hf_repo} -> {args.gcs_uri}")
        return 0

    if args.cmd == "forget":
        ok = forget(args.hf_repo)
        print(("Forgot " if ok else "Not present: ") + args.hf_repo)
        return 0 if ok else 1

    if args.cmd == "refresh":
        found = refresh_from_gcs(args.gcs_prefix, verbose=True)
        print(f"Refreshed {len(found)} entries from {args.gcs_prefix}")
        return 0

    return 2


if __name__ == "__main__":
    import sys

    sys.exit(_main())
