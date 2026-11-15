"""Persistent checkpoint save/load for session resume.

Extends the existing in-memory CheckpointManager with disk persistence
and a cognithor_resume tool interface. Checkpoints are stored in the
Knowledge Vault under the ``__checkpoints__`` namespace.
"""

from __future__ import annotations

import contextlib
import json
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class PersistentCheckpoint:
    """A checkpoint that can be saved to and loaded from disk."""

    session_id: str
    agent_id: str = ""
    checkpoint_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp_utc: str = ""
    platform: str = field(default_factory=lambda: sys.platform)
    state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp_utc:
            from datetime import UTC, datetime

            self.timestamp_utc = datetime.now(UTC).isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, data: str) -> PersistentCheckpoint:
        d = json.loads(data)
        return cls(**d)


class CheckpointStore:
    """Manages persistent checkpoints on disk.

    Checkpoints are stored as JSON files under:
      ``{cognithor_home}/checkpoints/{session_id}/{checkpoint_id}.json``
    """

    def __init__(self, checkpoints_dir: Path) -> None:
        self._dir = checkpoints_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: PersistentCheckpoint) -> Path:
        """Save a checkpoint to disk. Returns the file path."""
        session_dir = self._dir / checkpoint.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / f"{checkpoint.checkpoint_id}.json"
        path.write_text(checkpoint.to_json(), encoding="utf-8")
        log.info(
            "checkpoint_saved",
            session=checkpoint.session_id[:8],
            checkpoint=checkpoint.checkpoint_id[:8],
        )
        return path

    def load(self, session_id: str, checkpoint_id: str) -> PersistentCheckpoint | None:
        """Load a specific checkpoint."""
        path = self._dir / session_id / f"{checkpoint_id}.json"
        if not path.exists():
            return None
        try:
            return PersistentCheckpoint.from_json(path.read_text(encoding="utf-8"))
        except Exception:
            log.debug("checkpoint_load_failed", exc_info=True)
            return None

    def get_latest(self, session_id: str) -> PersistentCheckpoint | None:
        """Get the most recent checkpoint for a session."""
        session_dir = self._dir / session_id
        if not session_dir.exists():
            return None
        checkpoints: list[PersistentCheckpoint] = []
        for f in session_dir.glob("*.json"):
            try:
                checkpoints.append(PersistentCheckpoint.from_json(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        if not checkpoints:
            return None
        # Sort by timestamp_utc (ISO format, string-sortable)
        checkpoints.sort(key=lambda c: c.timestamp_utc)
        return checkpoints[-1]

    def list_checkpoints(self, session_id: str) -> list[str]:
        """List checkpoint IDs for a session."""
        session_dir = self._dir / session_id
        if not session_dir.exists():
            return []
        return [p.stem for p in sorted(session_dir.glob("*.json"))]

    def clear_session(self, session_id: str) -> int:
        """Delete all checkpoints for a session. Returns count deleted."""
        session_dir = self._dir / session_id
        if not session_dir.exists():
            return 0
        count = 0
        for f in session_dir.glob("*.json"):
            f.unlink()
            count += 1
        with contextlib.suppress(OSError):
            session_dir.rmdir()
        return count


@dataclass
class ResumeResult:
    """Result of a resume operation."""

    success: bool = True
    session_id: str = ""
    checkpoint_id: str = ""
    resumed_state: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
