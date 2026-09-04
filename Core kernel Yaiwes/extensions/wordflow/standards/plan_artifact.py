"""Plan artifact por misión (paridad Cursor plan) — P2."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
import json

@dataclass
class PlanArtifact:
    mission_id: str
    task_id: str
    goal: str
    steps: List[str] = field(default_factory=list)
    copy_first_sources: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def save(self, root: Path) -> Path:
        d = root / "plans"
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{self.mission_id}_{self.task_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path
