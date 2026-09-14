from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ComponentState:
    task_id: str
    status: str = "PENDING"
    cursor: int = 0
    checkpoints: list | None = None
    evidence: list | None = None
    def __post_init__(self):
        self.checkpoints = [] if self.checkpoints is None else self.checkpoints
        self.evidence = [] if self.evidence is None else self.evidence

class PersistenceRuntime:
    def __init__(self, component_root: str | Path, state_path: str | Path):
        self.component_root = Path(component_root)
        self.state_path = Path(state_path)
        self.manifest_path = self.component_root / "INTERNAL-SURGICAL-MANIFEST-V5.json"
    def _manifest(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "yaiwes.internal.surgical/v5": raise ValueError("bad v5 manifest")
        return data
    def load(self, task_id):
        if not self.state_path.exists(): return ComponentState(task_id)
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return ComponentState(**data) if data.get("task_id") == task_id else ComponentState(task_id)
    def save(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)
        return state
    def run(self, task_id, payload=None):
        state = self.load(task_id); state.status = "CLAIMED"; manifest = self._manifest()
        links = [x for x in manifest["files"] if x["decision"] in {"BLOCK_OFFENSIVE","REVIEW_FAIL_CLOSED"}]
        for idx, link in enumerate(links, 1):
            state.status = "CHECKPOINTED"; state.cursor = idx
            state.checkpoints.append({"order":idx,"path":link["path"],"decision":link["decision"],"active_sha256":link["active_sha256"],"payload":dict(payload or {})})
            self.save(state)
        state.status = "VERIFIED"; state.evidence.append({"component":manifest["component"],"links":len(links),"version":manifest["version"]}); self.save(state)
        state.status = "RELEASED"; return self.save(state)
