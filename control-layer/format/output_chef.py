"""Output formatter · CHEF B (2D + 1P) · 0% LLM en collect/detect.

Pass 1 collect: reúne hechos del runtime/sentinela/sheriff.
Pass 2 detect: lista huecos (campos required vacíos / inconsistencias).
Pass 3 fill: solo si hay huecos; por defecto rellena placeholders deterministas
             (el host puede inyectar LLM callback opcional).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

REQUIRED = ("mission_id", "status", "summary", "evidence_hash")


@dataclass
class ChefResult:
    output: dict[str, Any]
    gaps: tuple[str, ...]
    pass_reached: str  # collect | detect | fill
    used_llm: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _collect(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Pass 1 · determinista."""
    out: dict[str, Any] = {
        "mission_id": facts.get("mission_id") or "",
        "status": facts.get("status") or "RUNNING",
        "summary": facts.get("summary") or "",
        "goal_restated": facts.get("goal") or facts.get("goal_restated") or "",
        "steps_done": list(facts.get("steps_done") or []),
        "steps_pending": list(facts.get("steps_pending") or []),
        "artifacts": list(facts.get("artifacts") or []),
        "contracts_active": list(facts.get("contracts_active") or []),
        "sheriff_state": facts.get("sheriff_state") or "GREEN",
        "risk_score": int(facts.get("risk_score") or 0),
        "evidence_hash": facts.get("evidence_hash") or "",
        "set_hash": facts.get("set_hash") or "",
        "errors": list(facts.get("errors") or []),
        "warnings": list(facts.get("warnings") or []),
        "next_action": facts.get("next_action") or "",
        "blocked_reason": facts.get("blocked_reason"),
        "signals_pending": int(facts.get("signals_pending") or 0),
        "mode": facts.get("mode") or "dual",
        "chef_pass": "collect",
        "raw_refs": list(facts.get("raw_refs") or []),
    }
    return out


def _detect(out: dict[str, Any]) -> list[str]:
    """Pass 2 · determinista."""
    gaps: list[str] = []
    for k in REQUIRED:
        v = out.get(k)
        if v is None or v == "" or v == []:
            gaps.append(f"missing:{k}")
    if out.get("status") == "BLOCKED" and not out.get("blocked_reason"):
        gaps.append("missing:blocked_reason")
    if out.get("sheriff_state") in ("RED", "BLACK") and not out.get("errors"):
        gaps.append("missing:errors_on_block")
    # duplicados triviales en steps
    done = out.get("steps_done") or []
    pend = out.get("steps_pending") or []
    dup = set(done) & set(pend)
    if dup:
        gaps.append(f"duplicate_steps:{sorted(dup)}")
    return gaps


def _fill_deterministic(out: dict[str, Any], gaps: Sequence[str]) -> dict[str, Any]:
    """Pass 3 fallback sin LLM: placeholders honestos."""
    o = dict(out)
    for g in gaps:
        if g == "missing:summary":
            o["summary"] = (
                f"mission={o.get('mission_id')} status={o.get('status')} "
                f"sheriff={o.get('sheriff_state')} risk={o.get('risk_score')}"
            )
        elif g == "missing:evidence_hash":
            o["evidence_hash"] = o.get("set_hash") or "sha256:pending"
        elif g == "missing:mission_id":
            o["mission_id"] = "unknown"
        elif g == "missing:status":
            o["status"] = "RUNNING"
        elif g == "missing:blocked_reason":
            o["blocked_reason"] = "blocked_without_detail"
        elif g == "missing:errors_on_block":
            o["errors"] = list(o.get("errors") or []) + ["sheriff_block"]
        elif g.startswith("duplicate_steps:"):
            # quitar de pending los que ya están done
            done = set(o.get("steps_done") or [])
            o["steps_pending"] = [s for s in (o.get("steps_pending") or []) if s not in done]
    o["chef_pass"] = "fill"
    return o


def chef_b_pipeline(
    facts: Mapping[str, Any],
    *,
    llm_fill: Optional[Callable[[dict[str, Any], Sequence[str]], dict[str, Any]]] = None,
) -> ChefResult:
    """Ejecuta CHEF B. llm_fill solo se llama si hay gaps."""
    collected = _collect(facts)
    gaps = _detect(collected)
    if not gaps:
        collected["chef_pass"] = "detect"
        return ChefResult(output=collected, gaps=(), pass_reached="detect", used_llm=False)

    used_llm = False
    if llm_fill is not None:
        filled = llm_fill(collected, gaps)
        used_llm = True
    else:
        filled = _fill_deterministic(collected, gaps)
    # re-detect post-fill
    gaps2 = _detect(filled)
    filled["chef_pass"] = "fill"
    return ChefResult(
        output=filled,
        gaps=tuple(gaps2),
        pass_reached="fill",
        used_llm=used_llm,
    )


def format_output(facts: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Atajo: devuelve solo el dict de salida."""
    return chef_b_pipeline(facts, **kwargs).output
