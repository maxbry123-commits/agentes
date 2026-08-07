"""Tier 1 SESSION parcial · JSONL por sesión · chain simple."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class SessionEvent:
    event_id: str
    kind: str
    payload: dict[str, Any]
    prev_hash: str
    chain_hash: str
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[SessionEvent] = []
        self._tip = "sha256:" + ("0" * 64)
        if self.path.is_file():
            self._load()

    def _load(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            ev = SessionEvent(
                event_id=str(d["event_id"]),
                kind=str(d["kind"]),
                payload=dict(d.get("payload") or {}),
                prev_hash=str(d["prev_hash"]),
                chain_hash=str(d["chain_hash"]),
                created_at=float(d["created_at"]),
            )
            self._events.append(ev)
            self._tip = ev.chain_hash

    def append(self, kind: str, payload: dict[str, Any] | None = None) -> SessionEvent:
        prev = self._tip
        raw = f"{prev}|{kind}|{json.dumps(payload or {}, sort_keys=True)}|{time.time_ns()}"
        chain = _sha(raw)
        eid = "sev_" + chain[7:19]
        ev = SessionEvent(
            event_id=eid,
            kind=kind,
            payload=dict(payload or {}),
            prev_hash=prev,
            chain_hash=chain,
            created_at=time.time(),
        )
        self._events.append(ev)
        self._tip = chain
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
        return ev

    @property
    def tip_hash(self) -> str:
        return self._tip

    def __len__(self) -> int:
        return len(self._events)
