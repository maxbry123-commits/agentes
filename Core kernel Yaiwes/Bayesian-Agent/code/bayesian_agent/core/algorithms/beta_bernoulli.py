"""Beta-Bernoulli posterior update for Skill success probability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from bayesian_agent.core.evidence import TrajectoryEvidence


@dataclass
class BetaBernoulliState:
    """Conjugate posterior for Bernoulli success/failure evidence."""

    alpha: float = 1.0
    beta: float = 1.0

    @property
    def success_probability(self) -> float:
        denom = self.alpha + self.beta
        return self.alpha / denom if denom else 0.0

    def update(self, event: TrajectoryEvidence) -> "BetaBernoulliState":
        outcome = event.outcome.strip().lower()
        if outcome == "success":
            self.alpha += 1.0
        elif outcome in {"failure", "failed", "error"}:
            self.beta += 1.0
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": float(self.alpha),
            "beta": float(self.beta),
            "posterior_success": self.success_probability,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "BetaBernoulliState":
        return cls(alpha=float(raw.get("alpha", 1.0)), beta=float(raw.get("beta", 1.0)))
