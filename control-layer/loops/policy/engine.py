"""Policy Engine — DSL YAML → PolicyDecision · 0% LLM
SOURCE: policy_decision.schema · default_policy.yaml
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loops.contracts.types import DetectorResult, PolicyDecision


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PolicyInput:
    run_id: str
    iteration: int = 0
    repair_count: int = 0
    phase_outcome: str | None = None  # validation_passed|validation_failed|...
    goal_complete: bool = False
    risk_level: str = "low"  # low|medium|high
    detectors: list[DetectorResult] = field(default_factory=list)


class PolicyEngine:
    def __init__(self, rules: list[dict[str, Any]] | None = None, default_action: str = "CONTINUE", default_reason: str = "no rule matched"):
        self.rules = rules or []
        self.default_action = default_action
        self.default_reason = default_reason

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyEngine":
        import yaml
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            rules=list(data.get("rules") or []),
            default_action=str(data.get("default_action") or "CONTINUE"),
            default_reason=str(data.get("default_reason") or "no rule matched"),
        )

    def evaluate(self, inp: PolicyInput) -> PolicyDecision:
        det_map = {d.detector: d for d in inp.detectors}
        for rule in self.rules:
            if self._match(rule.get("when") or {}, inp, det_map):
                action = str(rule.get("action") or self.default_action)
                return PolicyDecision(
                    action=action,  # type: ignore[arg-type]
                    run_id=inp.run_id,
                    reason=str(rule.get("reason") or rule.get("id") or ""),
                    decided_at=_now(),
                    triggered_by=self._triggered(rule, det_map, inp),
                    params=dict(rule.get("params") or {}),
                    policy_rule_id=str(rule.get("id") or ""),
                )
        return PolicyDecision(
            action=self.default_action,  # type: ignore[arg-type]
            run_id=inp.run_id,
            reason=self.default_reason,
            decided_at=_now(),
            triggered_by=[],
        )

    def _match(self, when: dict[str, Any], inp: PolicyInput, det_map: dict[str, DetectorResult]) -> bool:
        if "detectors" in when:
            names = when["detectors"]
            min_sev = float(when.get("min_severity") or 0)
            hit = False
            for n in names:
                d = det_map.get(n)
                if d and d.severity >= min_sev:
                    hit = True
                    break
            if not hit:
                return False
        if "min_iteration" in when and inp.iteration < int(when["min_iteration"]):
            return False
        if "max_repair" in when and inp.repair_count >= int(when["max_repair"]):
            return False
        if "min_repair" in when and inp.repair_count < int(when["min_repair"]):
            return False
        if "phase_outcome" in when:
            if inp.phase_outcome != when["phase_outcome"]:
                return False
        if "goal_complete" in when:
            if bool(inp.goal_complete) != bool(when["goal_complete"]):
                return False
        if "risk_level" in when:
            if inp.risk_level != when["risk_level"]:
                return False
        return True

    def _triggered(self, rule: dict, det_map: dict[str, DetectorResult], inp: PolicyInput) -> list[str]:
        out: list[str] = []
        when = rule.get("when") or {}
        for n in when.get("detectors") or []:
            if n in det_map:
                out.append(n)
        if when.get("phase_outcome"):
            out.append(str(when["phase_outcome"]))
        return out
