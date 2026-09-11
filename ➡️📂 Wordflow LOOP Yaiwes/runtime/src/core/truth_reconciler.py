"""Deterministic source-of-truth drift detector/reconciler."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class ReconcileResult:
    canonical: Dict[str, Any]
    conflicts: Dict[str, Tuple[Tuple[str, Any], ...]]
    missing_sources: Tuple[str, ...]
    status: str


def reconcile_sources(
    sources: Dict[str, Dict[str, Any]],
    required_sources: Iterable[str],
    precedence: Tuple[str, ...],
    keys: Tuple[str, ...],
) -> ReconcileResult:
    missing = tuple(sorted(set(required_sources) - set(sources)))
    canonical: Dict[str, Any] = {}
    conflicts: Dict[str, Tuple[Tuple[str, Any], ...]] = {}
    for key in keys:
        values = tuple(
            (name, sources[name].get(key))
            for name in sources
            if key in sources[name]
        )
        if len({repr(value) for _, value in values}) > 1:
            conflicts[key] = values
        for source in precedence:
            if source in sources and key in sources[source]:
                canonical[key] = sources[source][key]
                break
    if missing:
        status = "MISSING_SOURCE_GAP"
    elif conflicts:
        status = "DRIFT_DETECTED"
    else:
        status = "RECONCILED"
    return ReconcileResult(canonical, conflicts, missing, status)
