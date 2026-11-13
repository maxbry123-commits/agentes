import json
from pathlib import Path

from .models import TraceEvent, stable_hash, uid


class TraceStore:
    def __init__(self, root="state/trace"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.last = {}

    def emit(self, mission_id, stage, action, payload, resources=(), evidence=()):
        parent = self.last.get(mission_id)
        event = TraceEvent(
            trace_id=uid("tr"),
            mission_id=mission_id,
            stage=stage,
            action=action,
            parent_trace=parent,
            input_hash=stable_hash(payload.get("input", {})),
            output_hash=stable_hash(payload.get("output", {})) if "output" in payload else None,
            resource_refs=tuple(resources),
            evidence_refs=tuple(evidence),
        )
        path = self.root / f"{mission_id}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.__dict__, sort_keys=True, default=str) + "\n")
        self.last[mission_id] = event.trace_id
        return event

    def read(self, mission_id):
        path = self.root / f"{mission_id}.jsonl"
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
