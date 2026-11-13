"""Journal · append-only event log · Phase 0.

journal/{mission_id}.jsonl — never rewrite history.
Not injected into LLM context; MEMORY ops is the resume surface.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .schema import JournalEvent, SCHEMA_VERSION, _utcnow


class Journal:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "journal"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.jsonl"

    def append(
        self,
        mission_id: str,
        op: str,
        *,
        ok: bool,
        node_id: str | None = None,
        evidence_hash: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> JournalEvent:
        ev = JournalEvent(
            mission_id=mission_id,
            op=op,
            ok=ok,
            node_id=node_id,
            evidence_hash=evidence_hash,
            detail=dict(detail or {}),
            ts=_utcnow(),
            schema_version=SCHEMA_VERSION,
        )
        p = self._path(mission_id)
        line = json.dumps(ev.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        with open(p, "a", encoding="utf-8") as f:
            f.write(line)
        return ev

    def append_event(self, event: JournalEvent) -> JournalEvent:
        event.schema_version = SCHEMA_VERSION
        if not event.ts:
            event.ts = _utcnow()
        p = self._path(event.mission_id)
        line = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        with open(p, "a", encoding="utf-8") as f:
            f.write(line)
        return event

    def iter_events(self, mission_id: str) -> Iterator[JournalEvent]:
        p = self._path(mission_id)
        if not p.is_file():
            return
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield JournalEvent.from_dict(json.loads(line))
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

    def tail(self, mission_id: str, n: int = 20) -> list[JournalEvent]:
        events = list(self.iter_events(mission_id))
        if n <= 0:
            return events
        return events[-n:]

    def count(self, mission_id: str) -> int:
        return sum(1 for _ in self.iter_events(mission_id))

    def exists(self, mission_id: str) -> bool:
        return self._path(mission_id).is_file()
