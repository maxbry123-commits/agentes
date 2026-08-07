"""Observability metrics — OTel-compatible hooks · 0% LLM
SOURCE: P2 · export dict / optional otel
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoopMetrics:
    runs_total: int = 0
    runs_closed: int = 0
    runs_failed: int = 0
    runs_escalated: int = 0
    iterations_total: int = 0
    repairs_total: int = 0
    stalls_total: int = 0
    tokens_total: int = 0
    duration_seg_total: float = 0.0
    by_project: dict[str, int] = field(default_factory=dict)

    def record_run(self, *,
                   closed: bool,
                   state: str,
                   iterations: int = 0,
                   repairs: int = 0,
                   tokens: int = 0,
                   duration_seg: float = 0.0,
                   project_id: str = "",
                   stalled: bool = False) -> None:
        self.runs_total += 1
        if closed and state == "CLOSED":
            self.runs_closed += 1
        if state == "FAILED":
            self.runs_failed += 1
        if state == "ESCALATED":
            self.runs_escalated += 1
        self.iterations_total += iterations
        self.repairs_total += repairs
        self.tokens_total += tokens
        self.duration_seg_total += duration_seg
        if stalled:
            self.stalls_total += 1
        if project_id:
            self.by_project[project_id] = self.by_project.get(project_id, 0) + 1

    def snapshot(self) -> dict[str, Any]:
        success_rate = (self.runs_closed / self.runs_total) if self.runs_total else 0.0
        return {
            "runs_total": self.runs_total,
            "runs_closed": self.runs_closed,
            "runs_failed": self.runs_failed,
            "runs_escalated": self.runs_escalated,
            "success_rate": success_rate,
            "iterations_total": self.iterations_total,
            "repairs_total": self.repairs_total,
            "stalls_total": self.stalls_total,
            "tokens_total": self.tokens_total,
            "duration_seg_total": self.duration_seg_total,
            "by_project": dict(self.by_project),
        }

    def export_otel_attributes(self) -> dict[str, Any]:
        """Atributos listos para span/metric OTel (sin dependencia obligatoria)."""
        s = self.snapshot()
        return {f"loop.{k}": v for k, v in s.items() if not isinstance(v, dict)}


def try_otel_counter(name: str, value: int = 1, attrs: dict | None = None) -> bool:
    """Si opentelemetry está instalado, incrementa counter; si no, no-op."""
    try:
        from opentelemetry import metrics  # type: ignore
        meter = metrics.get_meter("wordflow.loops")
        counter = meter.create_counter(name)
        counter.add(value, attributes=attrs or {})
        return True
    except Exception:
        return False
