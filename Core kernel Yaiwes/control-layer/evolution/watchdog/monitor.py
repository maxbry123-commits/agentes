"""Watchdog · fallos → rollback ledger."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Callable

@dataclass
class WatchEvent:
    type: str
    capability: str = ""
    plugin_id: str = ""
    mutation_id: str = ""
    detail: str = ""
    action: str = ""
    def to_dict(self): return asdict(self)

class Watchdog:
    def __init__(self, fail_threshold=3):
        self.fail_threshold = fail_threshold
        self.fail_counts = {}
        self.events = []
        self._rollback_cb = None
    def set_rollback_handler(self, fn):
        self._rollback_cb = fn
    def on_invoke_result(self, capability, result, plugin_id=""):
        if result.get("ok"):
            self.fail_counts[capability] = 0; return None
        self.fail_counts[capability] = self.fail_counts.get(capability, 0) + 1
        action = "rollback_propose" if self.fail_counts[capability] >= self.fail_threshold else "alert"
        ev = WatchEvent("invoke_fail", capability, plugin_id, detail=str(result.get("error") or "invoke_failed"), action=action)
        self.events.append(ev); return ev
    def on_evolve_result(self, result):
        if result.get("ok"): return None
        ev = WatchEvent("evolve_fail", plugin_id=str(result.get("plugin_id") or ""), mutation_id=str(result.get("mutation_id") or ""), detail=str(result.get("error") or "evolve_failed"), action="alert")
        self.events.append(ev); return ev
    def propose_rollback(self, mutation_id):
        ok = bool(self._rollback_cb(mutation_id)) if self._rollback_cb and mutation_id else False
        ev = WatchEvent("threshold", mutation_id=mutation_id, action="rollback_executed" if ok else "rollback_failed", detail=f"rollback:{mutation_id}")
        self.events.append(ev)
        return {"ok": ok, "mutation_id": mutation_id, "event": ev.to_dict()}
    def to_dict(self):
        return {"fail_counts": dict(self.fail_counts), "events": [e.to_dict() for e in self.events[-50:]], "threshold": self.fail_threshold}
