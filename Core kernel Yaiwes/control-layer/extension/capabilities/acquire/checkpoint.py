"""Checkpoint store · transactional write · Phase 0.

checkpoint.tmp → fsync → rename → checkpoint.json
schema_version + checkpoint_hash + previous_checkpoint_hash
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .schema import Checkpoint, SCHEMA_VERSION, _utcnow


class CheckpointError(Exception):
    pass


class CheckpointStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.dir = self.root / "checkpoints"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.json"

    def load(self, mission_id: str) -> Checkpoint | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            cp = Checkpoint.from_dict(data)
            if cp.checkpoint_hash and cp.checkpoint_hash != cp.compute_hash():
                raise CheckpointError(f"checkpoint_hash_mismatch:{mission_id}")
            return cp
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise CheckpointError(f"checkpoint_corrupt:{mission_id}:{e}") from e

    def save(self, cp: Checkpoint) -> Checkpoint:
        """Atomic transactional save with hash chain."""
        prev = self.load_unchecked(cp.mission_id)
        if prev is not None and prev.checkpoint_hash:
            cp.previous_checkpoint_hash = prev.checkpoint_hash
        cp.schema_version = SCHEMA_VERSION
        cp.updated_at = _utcnow()
        cp.seal()

        p = self._path(cp.mission_id)
        tmp = p.with_suffix(".json.tmp")
        payload = json.dumps(cp.to_dict(), indent=2, sort_keys=True) + "\n"
        # write + fsync
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp), str(p))
        # fsync directory best-effort
        try:
            dir_fd = os.open(str(self.dir), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
        return cp

    def load_unchecked(self, mission_id: str) -> Checkpoint | None:
        """Load without hash verification (for chaining previous hash)."""
        p = self._path(mission_id)
        if not p.is_file():
            return None
        try:
            return Checkpoint.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def init(self, mission_id: str, *,
             nodes_total: int = 0) -> Checkpoint:
        cp = Checkpoint(
            mission_id=mission_id,
            nodes_total=nodes_total,
            status="RUNNABLE",
        )
        return self.save(cp)

    def exists(self, mission_id: str) -> bool:
        return self._path(mission_id).is_file()
