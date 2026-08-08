"""Mission lock · exclusive RUNNING guard · Phase 0.

locks/{mission_id}.lock — O_EXCL style via atomic create.
Stale locks can be broken with force=True (recover path).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .schema import SCHEMA_VERSION, _utcnow


class LockError(Exception):
    """Raised when mission is already locked."""

    def __init__(self, mission_id: str, holder: dict[str, Any] | None = None) -> None:
        self.mission_id = mission_id
        self.holder = holder or {}
        super().__init__(f"LOCKED:{mission_id}")


@dataclass
class LockInfo:
    mission_id: str
    pid: int
    acquired_at: str
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MissionLock:
    def __init__(self, root: Path | str, *,
                 stale_after_sec: float = 3600.0) -> None:
        self.root = Path(root)
        self.dir = self.root / "locks"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.stale_after_sec = stale_after_sec

    def _path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.dir / f"{safe}.lock"

    def is_locked(self, mission_id: str) -> bool:
        return self._path(mission_id).is_file()

    def read(self, mission_id: str) -> LockInfo | None:
        p = self._path(mission_id)
        if not p.is_file():
            return None
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return LockInfo(
                mission_id=str(d.get("mission_id") or mission_id),
                pid=int(d.get("pid") or 0),
                acquired_at=str(d.get("acquired_at") or ""),
                schema_version=str(d.get("schema_version") or SCHEMA_VERSION),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

    def acquire(self, mission_id: str, *,
                force: bool = False) -> LockInfo:
        p = self._path(mission_id)
        if p.is_file():
            if force or self._is_stale(p):
                self.release(mission_id)
            else:
                holder = {}
                info = self.read(mission_id)
                if info is not None:
                    holder = info.to_dict()
                raise LockError(mission_id, holder)

        info = LockInfo(
            mission_id=mission_id,
            pid=os.getpid(),
            acquired_at=_utcnow(),
        )
        # atomic create: fail if exists
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(p), flags, 0o644)
        except FileExistsError as e:
            raise LockError(mission_id) from e
        try:
            data = json.dumps(info.to_dict(), indent=2, sort_keys=True) + "\n"
            os.write(fd, data.encode("utf-8"))
        finally:
            os.close(fd)
        return info

    def release(self, mission_id: str) -> bool:
        p = self._path(mission_id)
        if not p.is_file():
            return False
        try:
            p.unlink()
            return True
        except OSError:
            return False

    def _is_stale(self, path: Path) -> bool:
        try:
            age = time.time() - path.stat().st_mtime
            return age > self.stale_after_sec
        except OSError:
            return True

    def __enter__(self) -> "MissionLock":  # type: ignore[override]
        return self

    # context manager per mission via helper
    def held(self, mission_id: str, *,
             force: bool = False):
        return _HeldLock(self, mission_id, force=force)


class _HeldLock:
    def __init__(self, lock: MissionLock, mission_id: str, *,
                 force: bool = False) -> None:
        self.lock = lock
        self.mission_id = mission_id
        self.force = force
        self.info: LockInfo | None = None

    def __enter__(self) -> LockInfo:
        self.info = self.lock.acquire(self.mission_id, force=self.force)
        return self.info

    def __exit__(self, exc_type, exc, tb) -> None:
        self.lock.release(self.mission_id)
