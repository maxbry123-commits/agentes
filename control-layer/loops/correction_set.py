"""CorrectionSet · rebuild input de la MISMA mission · 0% LLM.

Flujo:
  InputBlock(CORRECTION) → classify → signal durable → rebuild cursor/goal_view
  Nunca crea mission nueva. GOAL_LOCK se mantiene (mission_id inmutable).
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any, List, Mapping, Optional, Sequence

from inputblock.classifier import InputKind, classify
from inputblock.store import Criticality, InputBlock, InputStore
from runtime.durable import DurableRuntime, MissionState, SignalKind


@dataclass
class CorrectionSet:
    """Conjunto de correcciones aplicadas a una mission."""

    mission_id: str
    items: list[dict[str, Any]] = field(default_factory=list)
    rebuilt_at: float | None = None
    rebuild_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RebuildResult:
    mission_id: str
    same_mission: bool
    applied_signals: int
    status: str
    phase: str
    cursor: dict[str, Any]
    rebuild_hash: str
    rejected_new_task: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_rebuild(mission_id: str, items: Sequence[dict[str, Any]]) -> str:
    raw = mission_id + "|" + str(len(items)) + "|" + str(items)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def apply_correction(
    *,
    runtime: DurableRuntime,
    mission_id: str,
    content: str,
    store: InputStore | None = None,
    criticality: Criticality = Criticality.ORDEN,
    meta: Mapping[str, Any] | None = None,
) -> RebuildResult:
    """Clasifica input, encola signal si same_mission, aplica y checkpoint.

    Si NEW_TASK → no toca la mission; retorna rejected_new_task=True.
    """
    state = runtime.load(mission_id)
    if state is None:
        raise KeyError(f"mission_not_found:{mission_id}")

    meta_map = dict(meta or {})
    meta_map["active_mission_id"] = mission_id
    result = classify(content, meta=meta_map)
    notes: list[str] = list(result.reasons)

    if result.kind == InputKind.NEW_TASK or not result.same_mission:
        return RebuildResult(
            mission_id=mission_id,
            same_mission=False,
            applied_signals=0,
            status=state.status.value,
            phase=state.phase,
            cursor=dict(state.cursor),
            rebuild_hash="",
            rejected_new_task=True,
            notes=tuple(notes + ["rejected_new_task_use_create_mission"]),
        )

    # literal append opcional al InputStore
    if store is not None:
        store.append(
            content,
            criticality=criticality,
            mission_id=mission_id,
            meta={"kind": result.kind.value, **meta_map},
        )

    kind = (
        SignalKind.CORRECTION
        if result.kind == InputKind.CORRECTION
        else SignalKind.UPDATE
    )
    payload = {
        "text": content,
        "kind": result.kind.value,
        "patch": meta_map.get("patch") or {"note": content[:500]},
    }
    runtime.enqueue_signal(mission_id, kind, payload)
    applied = 0
    while True:
        sig = runtime.apply_next_signal(mission_id)
        if sig is None:
            break
        applied += 1

    # checkpoint post-rebuild
    state2 = runtime.load(mission_id)
    assert state2 is not None
    cs = CorrectionSet(mission_id=mission_id)
    cs.items.append({"kind": result.kind.value, "at": time.time()})
    cs.rebuilt_at = time.time()
    cs.rebuild_hash = _hash_rebuild(mission_id, cs.items)
    state2.meta["correction_set"] = cs.to_dict()
    runtime.save(state2)
    runtime.checkpoint(
        mission_id,
        phase=state2.phase or "rebuilt",
        cursor=state2.cursor,
        evidence_hash=cs.rebuild_hash,
    )
    final = runtime.load(mission_id)
    assert final is not None

    return RebuildResult(
        mission_id=mission_id,
        same_mission=True,
        applied_signals=applied,
        status=final.status.value,
        phase=final.phase,
        cursor=dict(final.cursor),
        rebuild_hash=cs.rebuild_hash or "",
        rejected_new_task=False,
        notes=tuple(notes),
    )


def rebuild_from_pending_signals(
    runtime: DurableRuntime,
    mission_id: str,
) -> RebuildResult:
    """Aplica todos los signals pendientes (p.ej. tras resume de 24h)."""
    state = runtime.load(mission_id)
    if state is None:
        raise KeyError(f"mission_not_found:{mission_id}")
    applied = 0
    while True:
        sig = runtime.apply_next_signal(mission_id)
        if sig is None:
            break
        applied += 1
    final = runtime.resume(mission_id)
    h = _hash_rebuild(mission_id, [{"n": applied}])
    return RebuildResult(
        mission_id=mission_id,
        same_mission=True,
        applied_signals=applied,
        status=final.status.value,
        phase=final.phase,
        cursor=dict(final.cursor),
        rebuild_hash=h,
        rejected_new_task=False,
        notes=("rebuild_from_pending",),
    )
