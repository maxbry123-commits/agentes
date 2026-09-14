from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Protocol

import yaiwes_coda_bus_v7 as v7

DB_SCHEMA_VERSION = 1


def _dump(value: Any) -> str:
    return json.dumps(v7._jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(raw: str | None, default: Any = None) -> Any:
    if raw is None:
        return default
    return json.loads(raw)


class PersistenceBackend(Protocol):
    def begin_workflow(self, workflow_id: str, task: dict[str, Any]) -> dict[str, Any]: ...
    def cached_report(self, workflow_id: str) -> dict[str, Any] | None: ...
    def load_completed(self, workflow_id: str) -> list[dict[str, Any]]: ...
    def append_event(self, workflow_id: str, component: int | None, event_type: str, payload: Any) -> None: ...
    def checkpoint(self, workflow_id: str, ordinal: int, label: str, evidence: dict[str, Any], internal_state: dict[str, Any], output: Any, research: dict[str, Any]) -> None: ...
    def mark_interrupted(self, workflow_id: str, ordinal: int, error: Exception) -> None: ...
    def complete_workflow(self, workflow_id: str, report: dict[str, Any]) -> None: ...


class SQLiteDurableStore:
    """Durable CODA state using stdlib SQLite.

    Design goals:
    - WAL journaling and explicit transactions.
    - One idempotent workflow row per workflow_id.
    - One committed checkpoint per CODA component.
    - Append-only event journal for replay/audit.
    - Persistent metadata memory for discovered tools/plugins.
    - Durable queue with leases so interrupted workers can be recovered.

    JSON evidence remains in the existing filesystem. SQLite is the durable
    coordination plane, not a replacement for component-internal workflows.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_lock = threading.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_schema(self) -> None:
        with self._init_lock:
            conn = self._connect()
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    INSERT INTO meta(key, value) VALUES ('schema_version', '1')
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value;

                    CREATE TABLE IF NOT EXISTS workflows (
                        workflow_id TEXT PRIMARY KEY,
                        task_hash TEXT NOT NULL,
                        task_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        current_component INTEGER NOT NULL DEFAULT 0,
                        current_output_json TEXT,
                        report_json TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS checkpoints (
                        workflow_id TEXT NOT NULL,
                        component INTEGER NOT NULL,
                        label TEXT NOT NULL,
                        status TEXT NOT NULL,
                        input_hash TEXT NOT NULL,
                        output_hash TEXT NOT NULL,
                        evidence_json TEXT NOT NULL,
                        internal_state_json TEXT NOT NULL,
                        output_json TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        PRIMARY KEY(workflow_id, component),
                        FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_component
                        ON checkpoints(workflow_id, component);

                    CREATE TABLE IF NOT EXISTS event_journal (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workflow_id TEXT NOT NULL,
                        component INTEGER,
                        event_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_event_journal_workflow
                        ON event_journal(workflow_id, id);

                    CREATE TABLE IF NOT EXISTS tool_memory (
                        workflow_id TEXT NOT NULL,
                        component INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        capability TEXT NOT NULL,
                        source TEXT NOT NULL,
                        risk TEXT NOT NULL,
                        executable INTEGER NOT NULL,
                        metadata_json TEXT NOT NULL,
                        first_seen REAL NOT NULL,
                        last_seen REAL NOT NULL,
                        PRIMARY KEY(workflow_id, component, name, capability, source)
                    );

                    CREATE TABLE IF NOT EXISTS queue_items (
                        task_id TEXT PRIMARY KEY,
                        payload_json TEXT NOT NULL,
                        priority INTEGER NOT NULL DEFAULT 5,
                        status TEXT NOT NULL DEFAULT 'QUEUED',
                        lease_owner TEXT,
                        lease_until REAL,
                        attempts INTEGER NOT NULL DEFAULT 0,
                        last_error TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_queue_status_priority
                        ON queue_items(status, priority, created_at);
                    """
                )
            finally:
                conn.close()

    def workflow(self, workflow_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def begin_workflow(self, workflow_id: str, task: dict[str, Any]) -> dict[str, Any]:
        now = time.time()
        task_hash = v7._digest(task)
        task_json = _dump(task)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """INSERT OR IGNORE INTO workflows
                   (workflow_id, task_hash, task_json, status, current_component, created_at, updated_at)
                   VALUES (?, ?, ?, 'RUNNING', 0, ?, ?)""",
                (workflow_id, task_hash, task_json, now, now),
            )
            row = conn.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,)).fetchone()
            if row is None:
                raise RuntimeError("workflow row missing after insert")
            if row["task_hash"] != task_hash:
                raise ValueError(f"workflow_id reused with different task: {workflow_id}")
            if row["status"] != "COMPLETED":
                conn.execute(
                    "UPDATE workflows SET status='RUNNING', updated_at=? WHERE workflow_id=?",
                    (now, workflow_id),
                )
            conn.execute(
                "INSERT INTO event_journal(workflow_id, component, event_type, payload_json, created_at) VALUES (?, NULL, 'WORKFLOW_OPEN', ?, ?)",
                (workflow_id, _dump({"task_hash": task_hash}), now),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
        return self.workflow(workflow_id) or {}

    def cached_report(self, workflow_id: str) -> dict[str, Any] | None:
        row = self.workflow(workflow_id)
        if not row or row["status"] != "COMPLETED" or not row["report_json"]:
            return None
        return _load(row["report_json"], None)

    def load_completed(self, workflow_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE workflow_id=? ORDER BY component ASC",
                (workflow_id,),
            ).fetchall()
        finally:
            conn.close()
        out = [
            {
                "component": row["component"],
                "label": row["label"],
                "status": row["status"],
                "input_hash": row["input_hash"],
                "output_hash": row["output_hash"],
                "evidence": _load(row["evidence_json"], {}),
                "internal_state": _load(row["internal_state_json"], {}),
                "output": _load(row["output_json"], {}),
            }
            for row in rows
        ]
        actual = [x["component"] for x in out]
        expected = list(range(1, len(out) + 1))
        if actual != expected:
            raise RuntimeError(f"non-contiguous durable checkpoints: {actual}")
        return out

    def append_event(self, workflow_id: str, component: int | None, event_type: str, payload: Any) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO event_journal(workflow_id, component, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (workflow_id, component, event_type, _dump(payload), time.time()),
            )
        finally:
            conn.close()

    def checkpoint(
        self,
        workflow_id: str,
        ordinal: int,
        label: str,
        evidence: dict[str, Any],
        internal_state: dict[str, Any],
        output: Any,
        research: dict[str, Any],
    ) -> None:
        now = time.time()
        input_hash = str(internal_state.get("input_hash") or "")
        output_hash = str(internal_state.get("output_hash") or v7._digest(output))
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """INSERT INTO checkpoints
                   (workflow_id, component, label, status, input_hash, output_hash,
                    evidence_json, internal_state_json, output_json, created_at)
                   VALUES (?, ?, ?, 'COMPLETED', ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(workflow_id, component) DO UPDATE SET
                     label=excluded.label,
                     status='COMPLETED',
                     input_hash=excluded.input_hash,
                     output_hash=excluded.output_hash,
                     evidence_json=excluded.evidence_json,
                     internal_state_json=excluded.internal_state_json,
                     output_json=excluded.output_json,
                     created_at=excluded.created_at""",
                (
                    workflow_id,
                    ordinal,
                    label,
                    input_hash,
                    output_hash,
                    _dump(evidence),
                    _dump(internal_state),
                    _dump(output),
                    now,
                ),
            )
            conn.execute(
                "UPDATE workflows SET status='RUNNING', current_component=?, current_output_json=?, updated_at=? WHERE workflow_id=?",
                (ordinal, _dump(output), now, workflow_id),
            )
            conn.execute(
                "INSERT INTO event_journal(workflow_id, component, event_type, payload_json, created_at) VALUES (?, ?, 'COMPONENT_COMMITTED', ?, ?)",
                (workflow_id, ordinal, _dump({"input_hash": input_hash, "output_hash": output_hash}), now),
            )
            for tool in research.get("tool_candidates", []) or []:
                if not isinstance(tool, dict):
                    continue
                conn.execute(
                    """INSERT INTO tool_memory
                       (workflow_id, component, name, capability, source, risk, executable,
                        metadata_json, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(workflow_id, component, name, capability, source)
                       DO UPDATE SET risk=excluded.risk, executable=excluded.executable,
                                     metadata_json=excluded.metadata_json, last_seen=excluded.last_seen""",
                    (
                        workflow_id,
                        ordinal,
                        str(tool.get("name") or ""),
                        str(tool.get("capability") or ""),
                        str(tool.get("source") or ""),
                        str(tool.get("risk") or "unknown"),
                        1 if tool.get("executable") else 0,
                        _dump(tool.get("metadata") or {}),
                        now,
                        now,
                    ),
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def mark_interrupted(self, workflow_id: str, ordinal: int, error: Exception) -> None:
        now = time.time()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE workflows SET status='INTERRUPTED', updated_at=? WHERE workflow_id=?",
                (now, workflow_id),
            )
            conn.execute(
                "INSERT INTO event_journal(workflow_id, component, event_type, payload_json, created_at) VALUES (?, ?, 'COMPONENT_INTERRUPTED', ?, ?)",
                (workflow_id, ordinal, _dump({"error": str(error)[:2000]}), now),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def complete_workflow(self, workflow_id: str, report: dict[str, Any]) -> None:
        now = time.time()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE workflows SET status='COMPLETED', current_component=24, report_json=?, updated_at=? WHERE workflow_id=?",
                (_dump(report), now, workflow_id),
            )
            conn.execute(
                "INSERT INTO event_journal(workflow_id, component, event_type, payload_json, created_at) VALUES (?, 24, 'WORKFLOW_COMPLETED', ?, ?)",
                (workflow_id, _dump({"status": report.get("status")}), now),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def events(self, workflow_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM event_journal WHERE workflow_id=? ORDER BY id",
                    (workflow_id,),
                ).fetchall()
            ]
        finally:
            conn.close()

    def tool_memory(self, workflow_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM tool_memory WHERE workflow_id=? ORDER BY component, name",
                    (workflow_id,),
                ).fetchall()
            ]
        finally:
            conn.close()

    def enqueue(self, task_id: str, payload: dict[str, Any], priority: int = 5) -> None:
        now = time.time()
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO queue_items(task_id, payload_json, priority, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'QUEUED', ?, ?)
                   ON CONFLICT(task_id) DO UPDATE SET
                     payload_json=CASE WHEN queue_items.status IN ('FAILED','QUEUED') THEN excluded.payload_json ELSE queue_items.payload_json END,
                     priority=CASE WHEN queue_items.status IN ('FAILED','QUEUED') THEN excluded.priority ELSE queue_items.priority END,
                     status=CASE WHEN queue_items.status='FAILED' THEN 'QUEUED' ELSE queue_items.status END,
                     updated_at=excluded.updated_at""",
                (task_id, _dump(payload), int(priority), now, now),
            )
        finally:
            conn.close()

    def claim(self, worker_id: str, *, allowed_task_ids: Iterable[str] | None = None, lease_seconds: int = 120) -> dict[str, Any] | None:
        now = time.time()
        allowed = list(allowed_task_ids or [])
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE queue_items SET status='QUEUED', lease_owner=NULL, lease_until=NULL, updated_at=? WHERE status='RUNNING' AND lease_until IS NOT NULL AND lease_until < ?",
                (now, now),
            )
            where = "status='QUEUED'"
            params: list[Any] = []
            if allowed:
                marks = ",".join("?" for _ in allowed)
                where += f" AND task_id IN ({marks})"
                params.extend(allowed)
            row = conn.execute(
                f"SELECT * FROM queue_items WHERE {where} ORDER BY priority ASC, created_at ASC LIMIT 1",
                params,
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None
            changed = conn.execute(
                "UPDATE queue_items SET status='RUNNING', lease_owner=?, lease_until=?, attempts=attempts+1, updated_at=? WHERE task_id=? AND status='QUEUED'",
                (worker_id, now + lease_seconds, now, row["task_id"]),
            ).rowcount
            if changed != 1:
                conn.execute("ROLLBACK")
                return None
            conn.execute("COMMIT")
            return {
                "task_id": row["task_id"],
                "payload": _load(row["payload_json"], {}),
                "priority": row["priority"],
            }
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def finish_queue(self, task_id: str, success: bool, error: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE queue_items SET status=?, lease_owner=NULL, lease_until=NULL, last_error=?, updated_at=? WHERE task_id=?",
                ("DONE" if success else "FAILED", error, time.time(), task_id),
            )
        finally:
            conn.close()

    def queue_state(self, task_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM queue_items WHERE task_id=?", (task_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
