"""W15 · Output Contract subset ejecutable (8 campos núcleo)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

REQUIRED_FIELDS = (
    "goal",
    "result",
    "evidence",
    "limitations",
    "next_state",
    "termination",
)


@dataclass
class OutputContract:
    goal: str = ""
    scope: str = ""
    result: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    next_state: dict[str, Any] = field(default_factory=dict)
    termination: str = ""  # complete|partial|failed|escalated

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OutputValidation:
    ok: bool
    missing: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def validate_output(payload: Mapping[str, Any] | OutputContract | None) -> OutputValidation:
    if payload is None:
        return OutputValidation(False, missing=list(REQUIRED_FIELDS), reasons=["empty"])
    data = payload.to_dict() if isinstance(payload, OutputContract) else dict(payload)
    missing: list[str] = []
    for k in REQUIRED_FIELDS:
        v = data.get(k)
        if v is None or v == "" or v == {} or v == []:
            missing.append(k)
    reasons: list[str] = []
    term = str(data.get("termination") or "")
    if term and term not in ("complete", "partial", "failed", "escalated"):
        reasons.append("invalid_termination")
    ok = len(missing) == 0 and len(reasons) == 0
    return OutputValidation(ok=ok, missing=missing, reasons=reasons)


def compile_output(
    *,
    goal: str,
    result: str,
    evidence: dict | None = None,
    limitations: list[str] | None = None,
    assumptions: list[str] | None = None,
    scope: str = "",
    next_state: dict | None = None,
    termination: str = "complete",
) -> tuple[OutputContract, OutputValidation]:
    oc = OutputContract(
        goal=goal,
        scope=scope,
        result=result,
        evidence=dict(evidence or {}),
        limitations=list(limitations or []),
        assumptions=list(assumptions or []),
        next_state=dict(next_state or {}),
        termination=termination,
    )
    return oc, validate_output(oc)
