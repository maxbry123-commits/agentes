import json
from pathlib import Path

from .models import Checkpoint, stable_hash


class CheckpointStore:
    def __init__(self, root="state/checkpoints"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, mission_id, stage, state):
        cp = Checkpoint(mission_id, stage, state, stable_hash(state))
        (self.root / f"{mission_id}.json").write_text(
            json.dumps(cp.__dict__, sort_keys=True, default=str, indent=2),
            encoding="utf-8",
        )
        return cp

    def load(self, mission_id):
        path = self.root / f"{mission_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
