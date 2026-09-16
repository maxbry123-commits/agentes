from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from typing import Iterable, Mapping

CONTRACT = "yaiwes.truth_reconciliation/v1"
REQUIRED_TRUTHS = (
    "README", "STATE", "CHECKPOINT", "BITACORA", "GAPS", "HANDOFF", "PLAN", "RECOVERY",
)
ANCHORS = ("STATE", "CHECKPOINT")
_CHECKPOINT_RE = re.compile(r"WFLOOP-CODE-GRAPH-\d{8}-\d{4}")
_CANONICAL_CHECKPOINT_RE = re.compile(
    r"Checkpoint\s+can[oó]nico\s*:\s*`?(WFLOOP-CODE-GRAPH-\d{8}-\d{4})`?",
    re.IGNORECASE,
)

class TruthReconciliationError(ValueError):
    pass

@dataclass(frozen=True)
class TruthRecord:
    name: str
    checkpoint_id: str
    content_sha256: str

@dataclass(frozen=True)
class ReconciliationReport:
    contract: str
    status: str
    canonical_checkpoint: str | None
    drift: tuple[str, ...]
    conflicts: tuple[str, ...]
    missing: tuple[str, ...]
    write_authorized: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

def _checkpoint_from_text(text: str) -> str:
    canonical_matches = sorted(set(_CANONICAL_CHECKPOINT_RE.findall(text)))
    if len(canonical_matches) > 1:
        raise TruthReconciliationError(
            f"conflicting canonical checkpoint markers: {len(canonical_matches)}"
        )
    if len(canonical_matches) == 1:
        return canonical_matches[0]

    matches = sorted(set(_CHECKPOINT_RE.findall(text)))
    if len(matches) != 1:
        raise TruthReconciliationError(
            "expected one checkpoint reference or one explicit 'Checkpoint canónico' marker"
        )
    return matches[0]

def _checkpoint_from_json(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TruthReconciliationError("invalid JSON truth source") from exc
    value = data.get("checkpoint_id")
    if not isinstance(value, str) or not _CHECKPOINT_RE.fullmatch(value):
        raise TruthReconciliationError("missing/invalid checkpoint_id")
    return value

def build_record(name: str, text: str, sha256_hex: str) -> TruthRecord:
    if name not in REQUIRED_TRUTHS:
        raise TruthReconciliationError(f"unknown truth source: {name}")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256_hex):
        raise TruthReconciliationError("sha256 must be lowercase 64-hex")
    checkpoint = _checkpoint_from_json(text) if name in ANCHORS else _checkpoint_from_text(text)
    return TruthRecord(name=name, checkpoint_id=checkpoint, content_sha256=sha256_hex)

def reconcile(records: Iterable[TruthRecord]) -> ReconciliationReport:
    by_name: dict[str, TruthRecord] = {}
    conflicts: list[str] = []
    for record in records:
        if record.name in by_name:
            conflicts.append(f"DUPLICATE_SOURCE:{record.name}")
        else:
            by_name[record.name] = record
    missing = tuple(name for name in REQUIRED_TRUTHS if name not in by_name)
    if missing:
        return ReconciliationReport(CONTRACT, "FAIL_CLOSED_MISSING_TRUTH", None, (), tuple(sorted(conflicts)), missing)
    anchor_values = {by_name[name].checkpoint_id for name in ANCHORS}
    if len(anchor_values) != 1:
        conflicts.append("ANCHOR_CHECKPOINT_CONFLICT")
        return ReconciliationReport(CONTRACT, "FAIL_CLOSED_CONFLICT", None, (), tuple(sorted(conflicts)), ())
    canonical = next(iter(anchor_values))
    drift = tuple(name for name in REQUIRED_TRUTHS if by_name[name].checkpoint_id != canonical)
    if conflicts:
        status = "FAIL_CLOSED_CONFLICT"
    elif drift:
        status = "DRIFT_RECONCILE_REQUIRED"
    else:
        status = "CONSISTENT"
    return ReconciliationReport(CONTRACT, status, canonical, drift, tuple(sorted(conflicts)), ())

def validate_reconciliation_plan(report: ReconciliationReport, proposed_updates: Mapping[str, str]) -> bool:
    if report.status != "DRIFT_RECONCILE_REQUIRED":
        return False
    if set(proposed_updates) != set(report.drift):
        return False
    return all(value == report.canonical_checkpoint for value in proposed_updates.values())
