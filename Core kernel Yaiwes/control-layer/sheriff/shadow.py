"""Shadow ledger · ORANGE / C55 · registra sin promover a prod.

Promotion solo si test_gate + provenance + trust pasan (declarativo).
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ShadowRecord:
    record_id: str
    op_type: str
    set_hash: str
    fingerprint_hash: str
    contracts: tuple[str, ...]
    created_at: float
    promoted: bool = False
    promotion_blocked_reason: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ShadowLedger:
    """Ledger en memoria; persistencia = capa durable (A09)."""

    def __init__(self) -> None:
        self._records: Dict[str, ShadowRecord] = {}

    def append(
        self,
        *,
        op_type: str,
        set_hash: str,
        fingerprint_hash: str,
        contracts: List[str] | tuple[str, ...],
        meta: Optional[dict[str, Any]] = None,
    ) -> ShadowRecord:
        raw = f"{op_type}|{set_hash}|{fingerprint_hash}|{time.time_ns()}"
        rid = "shd_" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        rec = ShadowRecord(
            record_id=rid,
            op_type=op_type,
            set_hash=set_hash,
            fingerprint_hash=fingerprint_hash,
            contracts=tuple(contracts),
            created_at=time.time(),
            meta=dict(meta or {}),
        )
        self._records[rid] = rec
        return rec

    def get(self, record_id: str) -> ShadowRecord | None:
        return self._records.get(record_id)

    def list_pending(self) -> list[ShadowRecord]:
        return [r for r in self._records.values() if not r.promoted]


def promote_candidate(
    ledger: ShadowLedger,
    record_id: str,
    *,
    provenance_ok: bool,
    test_gate_ok: bool,
    trust_ok: bool,
) -> ShadowRecord:
    """C55 path: solo promueve si las 3 puertas están OK."""
    rec = ledger.get(record_id)
    if rec is None:
        raise KeyError(f"shadow_record_not_found:{record_id}")
    if rec.promoted:
        return rec

    if not provenance_ok:
        rec.promotion_blocked_reason = "provenance_failed"
        return rec
    if not test_gate_ok:
        rec.promotion_blocked_reason = "test_gate_failed"
        return rec
    if not trust_ok:
        rec.promotion_blocked_reason = "trust_failed"
        return rec

    rec.promoted = True
    rec.promotion_blocked_reason = None
    return rec
