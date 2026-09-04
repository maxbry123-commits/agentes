"""ROLLBACK · staging first · Phase 0.

Prefer staging + atomic rename. Full snapshots only when a node sets
needs_snapshot=True (not required in Phase 0).
Destructive ops need NEEDS_CONFIRMATION unless host authorized.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .journal import Journal
from .schema import SCHEMA_VERSION, _utcnow


class RollbackError(Exception):
    pass


@dataclass
class RollbackResult:
    mission_id: str
    ok: bool
    action: str  # staging_cleared|nothing|refused_destructive
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "ok": self.ok,
            "action": self.action,
            "detail": self.detail,
            "schema_version": SCHEMA_VERSION,
            "ts": _utcnow(),
        }


class RollbackService:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.staging_root = self.root / "staging"
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self.journal = Journal(self.root)

    def staging_path(self, mission_id: str) -> Path:
        safe = mission_id.replace("/", "_").replace("..", "_")
        return self.staging_root / safe

    def prepare_staging(self, mission_id: str) -> Path:
        """Create empty staging dir for mission (idempotent)."""
        p = self.staging_path(mission_id)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def clear_staging(self, mission_id: str) -> RollbackResult:
        """Delete staging tree; destination untouched."""
        p = self.staging_path(mission_id)
        if not p.exists():
            return RollbackResult(mission_id, True, "nothing", {"path": str(p)})
        shutil.rmtree(p, ignore_errors=False)
        self.journal.append(
            mission_id,
            "rollback_staging",
            ok=True,
            detail={"path": str(p)},
        )
        return RollbackResult(mission_id, True, "staging_cleared", {"path": str(p)})

    def atomic_promote(
        self,
        mission_id: str,
        dest_root: Path | str,
        *,
        allow_overwrite: bool = False,
    ) -> RollbackResult:
        """Rename staging → dest. Refuses overwrite without allow_overwrite."""
        staging = self.staging_path(mission_id)
        dest = Path(dest_root)
        if not staging.exists():
            return RollbackResult(mission_id, False, "nothing", {"error": "no_staging"})

        if dest.exists() and any(dest.iterdir()):
            if not allow_overwrite:
                self.journal.append(
                    mission_id,
                    "rollback_promote",
                    ok=False,
                    detail={"error": "NEEDS_CONFIRMATION", "dest": str(dest)},
                )
                return RollbackResult(
                    mission_id,
                    False,
                    "refused_destructive",
                    {"error": "NEEDS_CONFIRMATION", "dest": str(dest)},
                )
            # authorized overwrite: clear dest first
            shutil.rmtree(dest)

        dest.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(dest)
        self.journal.append(
            mission_id,
            "rollback_promote",
            ok=True,
            detail={"dest": str(dest)},
        )
        return RollbackResult(mission_id, True, "staging_cleared", {"promoted_to": str(dest)})

    def rollback(
        self,
        mission_id: str,
        *,
        allow_destructive: bool = False,
        dest_root: Path | str | None = None,
    ) -> RollbackResult:
        """Default safe rollback: clear staging only.

        Does not delete dest_root unless allow_destructive and dest provided
        (explicit NEEDS_CONFIRMATION gate).
        """
        if dest_root is not None and allow_destructive:
            d = Path(dest_root)
            if d.exists():
                shutil.rmtree(d)
                self.journal.append(
                    mission_id,
                    "rollback_dest",
                    ok=True,
                    detail={"dest": str(d), "authorized": True},
                )
        elif dest_root is not None and not allow_destructive:
            return RollbackResult(
                mission_id,
                False,
                "refused_destructive",
                {"error": "NEEDS_CONFIRMATION", "dest": str(dest_root)},
            )

        return self.clear_staging(mission_id)
