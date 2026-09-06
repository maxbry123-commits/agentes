"""Fail-closed guard against retrying an already failed strategy/delta.

Provenance pattern:
- Alex-v-p/indexer-core/packages/rag_core/retrieval/retry/rules.py
- source commit: efcfcb20f09117504b00f682ada1bfff2b04b649
- source blob: 7704a6bd73d8b073df88651bbaf232f1f3dbfd6b

Only the generic deterministic invariant is adapted here; no RAG-specific
retrieval code is copied.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


class StrategyDeltaError(RuntimeError):
    """A retry would repeat a failed strategy or material delta."""


def delta_hash(delta: Any) -> str:
    payload = json.dumps(
        delta,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class StrategyDeltaDecision:
    allowed: bool
    strategy_id: str
    delta_hash: str
    reason: str


def validate_strategy_delta(
    *,
    strategy_id: str,
    delta: Any,
    attempted_strategies: Iterable[str] = (),
    failed_delta_hashes: Iterable[str] = (),
) -> StrategyDeltaDecision:
    """Allow only a materially new strategy/delta combination.

    A repeated strategy OR repeated material delta is rejected.  The caller may
    then select another documented alternative; if none exists it must close as
    GAP/INCONCLUSIVE rather than blind-retry.
    """
    if not strategy_id:
        raise StrategyDeltaError("strategy_id must be non-empty")
    fingerprint = delta_hash(delta)
    attempted = {str(item) for item in attempted_strategies}
    failed = {str(item) for item in failed_delta_hashes}
    if strategy_id in attempted:
        return StrategyDeltaDecision(
            False, strategy_id, fingerprint, "strategy_already_attempted"
        )
    if fingerprint in failed:
        return StrategyDeltaDecision(
            False, strategy_id, fingerprint, "delta_already_failed"
        )
    return StrategyDeltaDecision(True, strategy_id, fingerprint, "materially_new_delta")


def require_strategy_delta(**kwargs: Any) -> StrategyDeltaDecision:
    decision = validate_strategy_delta(**kwargs)
    if not decision.allowed:
        raise StrategyDeltaError(decision.reason)
    return decision
