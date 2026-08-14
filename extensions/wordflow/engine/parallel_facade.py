# -*- coding: utf-8 -*-
"""parallel_facade — G5. Parallel tasks must route via ExecutionFacade. 0% LLM."""
from __future__ import annotations

from typing import Any

from .execution_facade import ExecutionFacade
from .goal_lock import verify_lock_integrity
from .parallel_runtime import ParallelRuntime


def _payload_kind(payload: dict[str, Any]) -> str:
    return str(payload.get("kind") or payload.get("route_kind") or "").lower()


class ParallelFacadeRuntime(ParallelRuntime):
    """ParallelRuntime that disallows direct engine calls in payload.

    Allowed payload kinds:
      - resource | resource_read | resource_load
      - engine | engine_job  (always via ExecutionFacade → Bus)
      - noop | local        (handler-only, no engine)
    """

    def __init__(self, lock: dict[str, Any], facade: ExecutionFacade, **kwargs: Any):
        super().__init__(**kwargs)
        integ = verify_lock_integrity(lock)
        if not integ.get("ok"):
            raise ValueError(f"lock not intact: {integ}")
        self.lock = lock
        self.facade = facade

    def run_routed(self, *,
                   max_steps: int = 1000) -> dict[str, Any]:
        def handler(ctx: dict[str, Any]) -> bool:
            task = ctx["task"]
            payload = dict(task.get("payload") or {})
            kind = _payload_kind(payload)

            # Explicit ban: direct_engine / bypass_bus flags
            if payload.get("bypass_bus") or payload.get("direct_engine"):
                ctx["route_error"] = "BYPASS_FORBIDDEN"
                return False

            if kind in ("noop", "local", ""):
                return True

            if kind.startswith("resource") or kind in ("engine", "engine_job"):
                result = self.facade.route(
                    self.lock,
                    kind=kind if kind != "engine_job" else "engine",
                    resource_id=payload.get("resource_id"),
                    engine_id=payload.get("engine_id") or "fake_static",
                    prompt=str(payload.get("prompt") or ""),
                    route_name=str(payload.get("route_name") or "ANALYSIS"),
                )
                ctx["facade_result"] = result
                return bool(result.get("ok"))

            ctx["route_error"] = f"UNKNOWN_KIND_{kind}"
            return False

        out = self.run(handler, max_steps=max_steps)
        out["lock_id"] = self.lock.get("lock_id")
        return out
