"""PolicySnapshot — congela contract al inicio de misión (G-W8)."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import json
from .forensic_contract import ForensicCodeContract

@dataclass
class PolicySnapshot:
    mission_id: str
    contract_version: str
    frozen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    contract: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def freeze(cls, mission_id: str, contract: ForensicCodeContract | None = None) -> "PolicySnapshot":
        c = contract or ForensicCodeContract()
        return cls(mission_id=mission_id, contract_version=c.version, contract=c.to_dict())

    def save(self, root: Path) -> Path:
        d = root / "policy_snapshots"
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{self.mission_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path
