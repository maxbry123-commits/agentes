"""Boot hydrate + resume desde PersistenceStore · 0% LLM
SOURCE: mejora F · cero pérdida tras crash
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loops.contracts.types import LoopContext, TERMINAL
from loops.dlq import DeadLetterQueue
from loops.engine import LoopEngine
from loops.persistence_store import PersistenceStore
from loops.registry import LoopRegistry
from loops.replay import EventReplayer
from loops.contracts.types import LoopEvent
from loops.supervisor import LoopSupervisor, SupervisorConfig


@dataclass
class BootstrapReport:
    registry_loaded: int = 0
    dlq_loaded: int = 0
    active_restored: int = 0
    resumed_ids: list[str] = field(default_factory=list)
    replay_ok: dict[str, bool] = field(default_factory=dict)


def _row_to_context(row: dict[str, Any], state_row: dict[str, Any] | None = None) -> LoopContext:
    st = state_row or {}
    return LoopContext(
        run_id=str(row.get("run_id") or ""),
        loop_id=str(row.get("loop_id") or "L01"),
        project_id=str(row.get("project_id") or ""),
        agent_id=str(row.get("agent_id") or ""),
        task_id=str(row.get("task_id") or ""),
        goal_id=str(row.get("goal_id") or st.get("goal_id") or "G"),
        state=str(st.get("state") or row.get("state") or "CREATED"),  # type: ignore[arg-type]
        iteration=int(st.get("iteration") or 0),
        parent_run_id=row.get("parent_run_id"),
        strategy=str(st.get("strategy") or "sequential"),
        created_at=str(st.get("created_at") or ""),
        updated_at=str(st.get("updated_at") or ""),
        recovery_state=dict(st.get("recovery_state") or {"repair_count": 0}),
    )


class Bootstrap:
    """Carga disco → registry/dlq/contexts · reanuda activos no terminales."""

    def __init__(self, persist_dir: str | Path, engine: LoopEngine | None = None) -> None:
        self.root = Path(persist_dir)
        self.store = PersistenceStore(self.root)
        self.engine = engine or LoopEngine.with_default_policy()
        self.replayer = EventReplayer()

    def hydrate_supervisor(self, supervisor: LoopSupervisor | None = None) -> tuple[LoopSupervisor, BootstrapReport]:
        cfg = SupervisorConfig(persist_dir=str(self.root))
        sup = supervisor or LoopSupervisor(engine=self.engine, config=cfg)
        # force same store
        sup.pstore = self.store
        report = BootstrapReport()

        report.registry_loaded = self.store.hydrate_registry(sup.registry)
        report.dlq_loaded = self.store.hydrate_dlq(sup.dlq)

        # last state per run from state.jsonl
        states: dict[str, dict[str, Any]] = {}
        for row in self.store.load_registry():  # may be duplicates; last wins via registry hydrate
            pass
        from loops.persist import JsonlStore
        for row in JsonlStore(self.root / "state.jsonl").read_all():
            rid = row.get("run_id")
            if rid:
                states[str(rid)] = row

        for entry in sup.registry.all():
            if entry.state in TERMINAL:
                continue
            st = states.get(entry.run_id)
            ctx = _row_to_context({
                "run_id": entry.run_id,
                "loop_id": entry.loop_id,
                "project_id": entry.project_id,
                "agent_id": entry.agent_id,
                "task_id": entry.task_id,
                "parent_run_id": entry.parent_run_id,
                "state": entry.state,
            }, st)
            # replay events if any
            ev_rows = self.store.load_events(entry.run_id)
            if ev_rows:
                events = []
                for er in ev_rows:
                    events.append(LoopEvent(
                        event_id=str(er.get("event_id") or ""),
                        run_id=str(er.get("run_id") or ""),
                        type=str(er.get("type") or ""),
                        timestamp=str(er.get("timestamp") or ""),
                        prev_hash=str(er.get("prev_hash") or ""),
                        hash=str(er.get("hash") or ""),
                        phase=er.get("phase"),
                        iteration=er.get("iteration"),
                        payload=er.get("payload") or {},
                    ))
                rr = self.replayer.replay(events)
                report.replay_ok[entry.run_id] = rr.ok
                if rr.final_state and rr.final_state not in TERMINAL:
                    ctx.state = rr.final_state  # type: ignore[assignment]
            # restore into supervisor without re-acquire conflict: direct inject
            sup._contexts[ctx.run_id] = ctx
            try:
                sup.leases.acquire(ctx.run_id, sup.config.worker_id)
            except Exception:
                pass
            sup.heartbeat.beat(ctx.run_id, sup.config.worker_id)
            report.active_restored += 1
            report.resumed_ids.append(ctx.run_id)

        return sup, report

    def resume_all(self, sup: LoopSupervisor, **run_kwargs: Any) -> list[Any]:
        """Ejecuta run_once en todos los activos restaurados."""
        results = []
        for rid in list(sup._contexts.keys()):
            ctx = sup._contexts[rid]
            if ctx.state in TERMINAL:
                continue
            try:
                results.append(sup.run_once(rid, **run_kwargs))
            except Exception as e:  # noqa: BLE001
                results.append({"run_id": rid, "error": str(e)})
        return results
