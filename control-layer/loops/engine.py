"""Loop Engine — + progress from phase outputs (E) · 0% LLM control flow
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loops.budget_governor import BudgetGovernor, budget_from_level
from loops.contracts.types import DetectorResult, LoopContext, LoopEvent, PolicyDecision, can_transition
from loops.detectors import NativeDetectors
from loops.event_chain import verify_chain
from loops.phases import PhaseRunner, PhaseResult
from loops.plugins.base import GraphPlugin, MemoryPlugin, NoOpGraphPlugin, NoOpMemoryPlugin
from loops.policy.engine import PolicyEngine, PolicyInput
from loops.progress import AdaptiveIterationController, ProgressEvaluator
from loops.progress_from_phases import progress_from_phases
from loops.recovery import RecoveryEngine, RecoveryResult
from loops.result_cache import ResultCache, fingerprint
from loops.risk import HumanGate, RiskEngine
from loops.state_machine import StateMachine
from loops.strategy_memory import StrategyMemory, StrategyRecord


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LoopRunResult:
    ctx: LoopContext
    events: list[LoopEvent] = field(default_factory=list)
    phase_results: list[PhaseResult] = field(default_factory=list)
    last_decision: PolicyDecision | None = None
    recovery: RecoveryResult | None = None
    closed: bool = False
    progress_score: float | None = None
    cache_hit: bool = False
    chain_ok: bool | None = None


class LoopEngine:
    def __init__(
        self,
        *,
        policy: PolicyEngine | None = None,
        memory: MemoryPlugin | None = None,
        graph: GraphPlugin | None = None,
        phase_handlers: dict | None = None,
        budget_governor: BudgetGovernor | None = None,
        strategy_memory: StrategyMemory | None = None,
        result_cache: ResultCache | None = None,
        risk_engine: RiskEngine | None = None,
        human_gate: HumanGate | None = None,
        progress_eval: ProgressEvaluator | None = None,
        adaptive: AdaptiveIterationController | None = None,
        native_detectors: NativeDetectors | None = None,
    ):
        self.sm = StateMachine()
        self.phases = PhaseRunner(handlers=phase_handlers)
        self.policy = policy or PolicyEngine()
        self.recovery = RecoveryEngine()
        self.memory = memory or NoOpMemoryPlugin()
        self.graph = graph or NoOpGraphPlugin()
        self.budget = budget_governor or BudgetGovernor(budget_from_level("tarea"))
        self.strategy_memory = strategy_memory or StrategyMemory()
        self.cache = result_cache or ResultCache()
        self.risk = risk_engine or RiskEngine()
        self.gate = human_gate or HumanGate()
        self.progress_eval = progress_eval or ProgressEvaluator()
        self.adaptive = adaptive or AdaptiveIterationController(max_iter=8)
        self.native = native_detectors or NativeDetectors()
        self._seen_idempotency: set[str] = set()
        self._prev_progress: dict[str, float] = {}
        self._event_log: dict[str, list[LoopEvent]] = {}

    @classmethod
    def with_default_policy(cls, policy_yaml: str | Path | None = None, **kwargs: Any) -> "LoopEngine":
        if policy_yaml is None:
            policy_yaml = Path(__file__).parent / "policy" / "default_policy.yaml"
        try:
            pol = PolicyEngine.from_yaml(policy_yaml)
        except Exception:
            pol = PolicyEngine()
        return cls(policy=pol, **kwargs)

    def _emit(self, ev: LoopEvent) -> None:
        self.memory.append_event(ev)
        self.graph.on_event(ev)
        self._event_log.setdefault(ev.run_id, []).append(ev)

    def verify_events(self, run_id: str) -> tuple[bool, str]:
        return verify_chain(self._event_log.get(run_id, []))

    def apply_strategy_hint(self, ctx: LoopContext, task_type: str = "") -> LoopContext:
        tt = task_type or ctx.loop_id or "default"
        ctx.strategy = self.strategy_memory.suggest_strategy(tt, default=ctx.strategy or "sequential")
        return ctx

    def start(self, ctx: LoopContext, *, task_type: str = "") -> tuple[LoopContext, list[LoopEvent]]:
        events: list[LoopEvent] = []
        if task_type or not ctx.strategy:
            ctx = self.apply_strategy_hint(ctx, task_type)
        if ctx.state == "CREATED":
            ctx, ev = self.sm.transition(ctx, "LOCKED", event_type="LOOP_LOCKED")
            events.append(ev)
            self._emit(ev)
            ctx, ev = self.sm.transition(ctx, "RUNNING", event_type="PHASE_STARTED")
            events.append(ev)
            self._emit(ev)
        return ctx, events

    def run_iteration(
        self,
        ctx: LoopContext,
        *,
        detectors: list[DetectorResult] | None = None,
        goal_complete: bool = False,
        risk_level: str | None = None,
        risk_actions: list[str] | None = None,
        progress_value: Any = None,
        progress_kind: str = "validation",
        charge_tokens: int = 0,
        charge_time_seg: float = 0.0,
        task_type: str = "",
        phase_context: dict[str, Any] | None = None,
    ) -> LoopRunResult:
        events: list[LoopEvent] = []

        if ctx.idempotency_key:
            ik = f"{ctx.run_id}:{ctx.idempotency_key}:{ctx.iteration}"
            if ik in self._seen_idempotency:
                return LoopRunResult(ctx=ctx, events=[], closed=False, cache_hit=True)
            self._seen_idempotency.add(ik)

        fp = fingerprint(ctx.project_id, ctx.task_id, ctx.goal_id, ctx.loop_id, str(ctx.iteration))
        cached = self.cache.get(fp)
        if cached and isinstance(cached, dict) and cached.get("closed"):
            return LoopRunResult(ctx=ctx, events=[], closed=True, cache_hit=True)

        if ctx.state == "CREATED":
            ctx, evs = self.start(ctx, task_type=task_type)
            events.extend(evs)

        if ctx.state not in ("RUNNING", "REPAIRING"):
            return LoopRunResult(
                ctx=ctx, events=events,
                closed=ctx.state in ("CLOSED", "FAILED", "ESCALATED", "CANCELLED"),
            )

        actions = risk_actions or ["plan", "ejecutar"]
        assessment = self.risk.assess(actions)
        gate = self.gate.decide(assessment)
        effective_risk = risk_level or assessment.level
        if gate.pause:
            ctx, ev = self.sm.transition(ctx, "PAUSED", event_type="LOOP_PAUSED", payload={"reason": gate.reason})
            events.append(ev)
            self._emit(ev)
            return LoopRunResult(ctx=ctx, events=events, closed=False)

        br = self.budget.charge(
            tokens=charge_tokens, time_seg=charge_time_seg, iteration=1, run_id=ctx.run_id
        )
        dets = list(detectors or [])
        dets.extend(br.detectors)

        if ctx.state == "REPAIRING":
            ctx, ev = self.sm.transition(ctx, "RUNNING", event_type="REPAIR_COMPLETED")
            events.append(ev)
            self._emit(ev)

        pctx = {
            "run_id": ctx.run_id,
            "iteration": ctx.iteration,
            "strategy": ctx.strategy,
            "inputs": ctx.inputs,
            **(phase_context or {}),
        }
        phase_results, sheriff = self.phases.run(pctx)
        ctx, ev = self.sm.transition(
            ctx, "VALIDATING", event_type="PHASE_COMPLETED", payload={"sheriff_ok": sheriff.ok}
        )
        events.append(ev)
        self._emit(ev)

        phase_outcome = "validation_passed" if sheriff.ok else "validation_failed"
        if not sheriff.ok:
            dets.append(DetectorResult(
                detector="contract_violation", severity=0.95, fired_at=_now(),
                run_id=ctx.run_id, evidence=[sheriff.reason], action_hint="repair",
            ))

        prev = self._prev_progress.get(ctx.run_id)
        if progress_value is not None:
            progress = self.progress_eval.evaluate(
                kind=progress_kind, value=progress_value, prev_score=prev, threshold=0.1
            )
        else:
            # E: derive from phase outputs
            progress = progress_from_phases(
                phase_results, evaluator=self.progress_eval, prev_score=prev, threshold=0.1
            )
        self._prev_progress[ctx.run_id] = progress.progress_score
        advice = self.adaptive.advise(progress, ctx.iteration)
        dets.extend(self.native.observe(ctx.run_id, progress.progress_score))

        if progress.is_stalled() and not any(d.detector == "stall" for d in dets):
            dets.append(DetectorResult(
                detector="stall" if advice.suggest_action != "ESCALATE" else "no_progress",
                severity=0.7, fired_at=_now(), run_id=ctx.run_id,
                evidence=[advice.reason], action_hint=advice.suggest_action.lower(),
            ))

        repair_count = int((ctx.recovery_state or {}).get("repair_count") or 0)
        decision = self.policy.evaluate(PolicyInput(
            run_id=ctx.run_id, iteration=ctx.iteration, repair_count=repair_count,
            phase_outcome=phase_outcome, goal_complete=goal_complete and sheriff.ok,
            risk_level=str(effective_risk), detectors=dets,
        ))
        if decision.action == "CONTINUE" and advice.suggest_action in ("CLOSE", "ESCALATE", "CHANGE_STRATEGY", "REPAIR"):
            if advice.suggest_action == "CLOSE" and goal_complete:
                decision = PolicyDecision(action="CLOSE", run_id=ctx.run_id, reason=advice.reason, decided_at=_now())
            elif advice.suggest_action != "CLOSE":
                decision = PolicyDecision(
                    action=advice.suggest_action,  # type: ignore[arg-type]
                    run_id=ctx.run_id, reason=advice.reason, decided_at=_now(),
                )

        ctx, ev = self.sm.transition(
            ctx, "DECIDING", event_type="POLICY_DECIDED", payload={"action": decision.action}
        )
        events.append(ev)
        self._emit(ev)

        rec = self.recovery.apply(ctx, decision)
        for k, v in (rec.ctx_updates or {}).items():
            if k == "recovery_state" and isinstance(v, dict):
                ctx.recovery_state = {**(ctx.recovery_state or {}), **v}
            elif k == "strategy":
                ctx.strategy = str(v)
            elif hasattr(ctx, k):
                setattr(ctx, k, v)

        target = rec.next_state
        etype = {
            "CLOSED": "LOOP_COMPLETED", "ESCALATED": "LOOP_ESCALATED", "FAILED": "LOOP_FAILED",
            "PAUSED": "LOOP_PAUSED", "CHECKPOINT": "CHECKPOINT_CREATED",
            "REPAIRING": "REPAIR_STARTED", "RUNNING": "LOOP_CONTINUED",
        }.get(target, "DECISION_MADE")

        if not can_transition(ctx.state, target):
            if target not in ("CLOSED", "ESCALATED", "FAILED", "CANCELLED", "PAUSED", "CHECKPOINT", "REPAIRING", "RUNNING"):
                target, etype = "FAILED", "LOOP_FAILED"

        ctx, ev = self.sm.transition(ctx, target, event_type=etype, payload={"action": rec.action_applied})
        events.append(ev)
        self._emit(ev)

        if target == "RUNNING":
            ctx.iteration += 1

        closed = target in ("CLOSED", "FAILED", "ESCALATED", "CANCELLED")
        if closed:
            self.cache.put(fp, {"closed": True, "state": target}, level="L2", ttl_seg=7200)
            self.strategy_memory.record(StrategyRecord(
                task_type=task_type or ctx.loop_id,
                strategy=ctx.strategy or "sequential",
                agent=ctx.agent_id,
                iterations=ctx.iteration,
                success=(target == "CLOSED"),
                quality=progress.progress_score,
            ))
            self.memory.checkpoint(ctx.run_id, {"state": ctx.state, "iteration": ctx.iteration})
            self.native.reset(ctx.run_id)

        chain_ok, _ = self.verify_events(ctx.run_id)
        return LoopRunResult(
            ctx=ctx, events=events, phase_results=phase_results,
            last_decision=decision, recovery=rec, closed=closed,
            progress_score=progress.progress_score, chain_ok=chain_ok,
        )
