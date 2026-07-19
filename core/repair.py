 <stador-universal/orchestrator/repair.py 2>/dev/null
"""
repair.py — F1-F16 Recovery Engine.
"""
import time
from typing import Optional, Callable
from orchestrator.agents import BaseAgent, AgentResult


class RepairEngine:
    """F1-F16: detecta, clasifica, recupera, repara, escala."""

    def __init__(self, mimo_agent: BaseAgent, sentinel=None,
                 on_escalate: Optional[Callable] = None,
                 max_repairs: int = 2):
        self.mimo = mimo_agent
        self.sentinel = sentinel
        self.on_escalate = on_escalate
        self.max_repairs = max_repairs

    def run(self, node_id: str, original_diff: str, error: str,
            state, context: dict) -> dict:
        """F1: detecta tipo de fallo (el caller ya sabe) → arranca F2."""
        # F2: snapshot
        state.persist()
        # F3: clasificar severidad
        severity = self._classify(error)
        if self.sentinel:
            self.sentinel.log({"event": "repair_start", "node_id": node_id,
                               "severity": severity, "error": error[:200]})
        # F10: limpiar artefactos parciales (git stash + tmp files)
        self._cleanup_artifacts(context)
        # F4-F7: el caller ya ramificó, nosotros vamos a F8
        # F8: construir prompt de repair (lo hace mimo.repair internamente)
        # F9-F11: mimo genera nuevo diff
        result = self.mimo.repair(original_diff, error,
                                  {**context, "node_id": node_id})
        if not result.success:
            # F14 + F15
            return self._escalate_or_retry(node_id, original_diff, error, state,
                                           result, context)
        # F12: re-verificar
        verify = self.mimo.verify(result.diff, context)
        if verify.success:
            # F13: continuar
            state.repair_counts[node_id] = state.repair_counts.get(node_id, 0) + 1
            return {"recovered": True, "diff": result.diff, "attempts": state.repair_counts[node_id]}
        # F14: counter++
        new_count = state.repair_counts.get(node_id, 0) + 1
        state.repair_counts[node_id] = new_count
        if new_count >= self.max_repairs:
            # F15
            return self._escalate(node_id, error, state)
        # F16: volver a F7 con nuevo error
        if self.sentinel:
            self.sentinel.log({"event": "repair_retry", "node_id": node_id,
                               "attempt": new_count})
        return self.run(node_id, result.diff, verify.error or "verify_failed",
                        state, context)

    def _cleanup_artifacts(self, context: dict) -> None:
        """F10: limpia artefactos parciales (git stash + tmp files) del sandbox."""
        sandbox = context.get("sandbox")
        if not sandbox:
            return
        try:
            # git stash deja el working tree limpio para re-aplicar el diff
            sandbox.exec("cd /work && git stash 2>&1 || true", timeout=10)
            # limpia temporales del intento previo
            sandbox.exec("cd /work && rm -f /tmp/patch.diff /tmp/repair.diff 2>&1 || true",
                          timeout=10)
            if self.sentinel:
                self.sentinel.log({"event": "artifacts_cleaned", "stage": "F10"})
        except Exception as e:
            if self.sentinel:
                self.sentinel.log({"event": "artifacts_cleanup_failed", "error": str(e)})

    def _classify(self, error: str) -> str:
        e = error.lower()
        if "sandbox" in e or "container" in e or "docker" in e:
            return "sandbox_crash"
        if "timeout" in e:
            return "timeout"
        if "gate" in e or "verdict" in e:
            return "gate_fail"
        return "verify_fail"

    def _escalate(self, node_id: str, error: str, state) -> dict:
        if self.sentinel:
            self.sentinel.log({"event": "repair_escalate", "node_id": node_id})
        if self.on_escalate:
            try:
                self.on_escalate(node_id, state.repair_counts.get(node_id, 0), state)
            except Exception as e:
                if self.sentinel:
                    self.sentinel.log({"event": "escalate_callback_failed", "error": str(e)})
        return {"recovered": False, "escalated": True, "node_id": node_id, "error": error}

    def _escalate_or_retry(self, node_id, original_diff, error, state, result, context) -> dict:
        new_count = state.repair_counts.get(node_id, 0) + 1
        state.repair_counts[node_id] = new_count
        if new_count >= self.max_repairs:
            return self._escalate(node_id, error, state)
        return {"recovered": False, "retry": True, "attempts": new_count,
                "error": result.error}
root@vmi3428294:~# echo 