from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sqlite3

from schemas.base import utc_now


class SQLiteMemoryStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def write(self, scope: str, kind: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_items (created_at, scope, kind, payload)
                VALUES (?, ?, ?, ?)
                """,
                (utc_now(), scope, kind, json.dumps(payload, ensure_ascii=False)),
            )

    def retrieve(self, scope: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, scope, kind, payload
                FROM memory_items
                WHERE scope = ? AND payload LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (scope, query_like, limit),
            ).fetchall()
        return [
            {
                "created_at": row[0],
                "scope": row[1],
                "kind": row[2],
                "payload": json.loads(row[3]),
            }
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_scope_kind ON memory_items(scope, kind)"
            )
