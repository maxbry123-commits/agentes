import json
from pathlib import Path
from dataclasses import asdict
from .models import State, Goal, Task, Event, now


class FileStore:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path = self.root / "events.jsonl"

    def save(self, state: State):
        state.updated_at = now()
        (self.root / "state.json").write_text(
            json.dumps(state.to_dict(), indent=2, default=str), encoding="utf-8"
        )

    def load(self) -> State | None:
        path = self.root / "state.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        goal = Goal(**data["goal"])
        tasks = {k: Task(**v) for k, v in data["tasks"].items()}
        return State(
            schema_version=data["schema_version"],
            goal=goal,
            tasks=tasks,
            iteration=data.get("iteration", 0),
            workflow_version=data.get("workflow_version", 1),
            completion_score=data.get("completion_score", 0.0),
            blockers=data.get("blockers", []),
            started_at=data.get("started_at", now()),
            updated_at=data.get("updated_at", now()),
        )

    def event(self, event: Event):
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")

    def checkpoint(self, state: State):
        cp = self.root / "checkpoints"
        cp.mkdir(exist_ok=True)
        (cp / f"iter_{state.iteration:04d}.json").write_text(
            json.dumps(state.to_dict(), indent=2, default=str), encoding="utf-8"
        )
