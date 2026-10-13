"""Detectores nativos a partir de historial de progreso · 0% LLM
SOURCE: P1 audit · stall/oscillation/regression/no_progress
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from loops.contracts.types import DetectorResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProgressHistory:
    scores: list[float] = field(default_factory=list)

    def add(self, score: float) -> None:
        self.scores.append(score)


class NativeDetectors:
    def __init__(self, stall_window: int = 3, osc_eps: float = 0.05) -> None:
        self.stall_window = stall_window
        self.osc_eps = osc_eps
        self._hist: dict[str, ProgressHistory] = {}

    def observe(self, run_id: str, score: float) -> list[DetectorResult]:
        h = self._hist.setdefault(run_id, ProgressHistory())
        h.add(score)
        out: list[DetectorResult] = []
        scores = h.scores

        # regression: last delta strongly negative
        if len(scores) >= 2 and scores[-1] - scores[-2] < -0.15:
            out.append(DetectorResult(
                detector="regression",
                severity=min(1.0, abs(scores[-1] - scores[-2])),
                fired_at=_now(),
                run_id=run_id,
                evidence=[{"prev": scores[-2], "cur": scores[-1]}],
                action_hint="repair",
            ))

        # stall: last N scores all below threshold and little variance
        if len(scores) >= self.stall_window:
            window = scores[-self.stall_window :]
            if max(window) - min(window) < self.osc_eps and max(window) < 0.15:
                out.append(DetectorResult(
                    detector="stall",
                    severity=0.75,
                    fired_at=_now(),
                    run_id=run_id,
                    evidence=[{"window": window}],
                    action_hint="change_strategy",
                ))

        # oscillation: alternating up/down beyond eps
        if len(scores) >= 4:
            w = scores[-4:]
            signs = [w[i + 1] - w[i] for i in range(3)]
            if all(abs(s) > self.osc_eps for s in signs):
                if signs[0] * signs[1] < 0 and signs[1] * signs[2] < 0:
                    out.append(DetectorResult(
                        detector="oscillation",
                        severity=0.65,
                        fired_at=_now(),
                        run_id=run_id,
                        evidence=[{"window": w}],
                        action_hint="repair",
                    ))

        # no_progress: many iters near zero
        if len(scores) >= 5 and max(scores[-5:]) < 0.05:
            out.append(DetectorResult(
                detector="no_progress",
                severity=0.85,
                fired_at=_now(),
                run_id=run_id,
                evidence=[{"window": scores[-5:]}],
                action_hint="escalate",
            ))

        return out

    def reset(self, run_id: str) -> None:
        self._hist.pop(run_id, None)
