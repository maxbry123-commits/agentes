"""EvidencePacket — claim sin evidencia = FAIL (RULE-008)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

@dataclass
class EvidencePacket:
    mission_id: str
    task_id: str
    change_id: str
    repository_revision: str
    files_changed: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    verdict: str = "UNKNOWN"  # PASS | FAIL | PARTIAL
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extra: Dict[str, Any] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return bool(
            self.mission_id
            and self.task_id
            and self.change_id
            and self.repository_revision
            and self.verdict in ("PASS", "FAIL", "PARTIAL")
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def require_evidence(packet: Optional[EvidencePacket]) -> None:
    if packet is None or not packet.is_complete():
        raise ValueError("RULE-008 EVIDENCE_REQUIRED: EvidencePacket missing or incomplete")
