from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def save_json(self, run_id: str, kind: str, artifact_id: str, payload: Any) -> Path:
        payload_dict = self._to_jsonable(payload)
        target = self.run_dir(run_id) / "artifacts" / kind / f"{artifact_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload_dict, indent=2, ensure_ascii=False), encoding="utf-8")
        self._append_index(run_id, kind, artifact_id, target)
        return target

    def save_text(self, run_id: str, kind: str, artifact_id: str, text: str, suffix: str = ".md") -> Path:
        target = self.run_dir(run_id) / "artifacts" / kind / f"{artifact_id}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self._append_index(run_id, kind, artifact_id, target)
        return target

    def save_state(self, run_id: str, payload: dict[str, Any]) -> Path:
        target = self.run_dir(run_id) / "state.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    def list_artifacts(self, run_id: str, kind: str) -> list[Path]:
        folder = self.run_dir(run_id) / "artifacts" / kind
        if not folder.exists():
            return []
        return sorted(path for path in folder.iterdir() if path.is_file())

    def _append_index(self, run_id: str, kind: str, artifact_id: str, path: Path) -> None:
        target = self.run_dir(run_id) / "artifact_index.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {"kind": kind, "artifact_id": artifact_id, "path": str(path)}
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _to_jsonable(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return asdict(payload)
        if isinstance(payload, dict):
            return {str(key): self._to_jsonable(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._to_jsonable(value) for value in payload]
        return payload
