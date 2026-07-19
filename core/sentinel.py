 <ador-universal/orchestrator/sentinel.py 2>/dev/null
"""
sentinel.py — Observabilidad: eventos, loops, deadlocks, métricas.
"""
import time
from collections import deque
from typing import Dict, List, Optional
from threading import Lock


class Sentinel:
    LOOP_THRESHOLD = 10
    DEADLOCK_THRESHOLD = 20
    MAX_EVENTS = 5000

    def __init__(self):
        self.events: deque = deque(maxlen=self.MAX_EVENTS)
        self.node_executions: Dict[str, int] = {}
        self.sandbox_health: Dict[str, str] = {}
        self.start_time = time.time()
        self._lock = Lock()

    def log(self, event: dict) -> None:
        event["ts"] = time.time()
        with self._lock:
            self.events.append(event)
            nid = event.get("node_id") or event.get("sandbox_id")
            if nid:
                self.node_executions[nid] = self.node_executions.get(nid, 0) + 1
                if self.node_executions[nid] > self.DEADLOCK_THRESHOLD:
                    event["deadlock_warning"] = True

    def detect_loops(self) -> List[str]:
        return [n for n, c in self.node_executions.items() if c > 3]

    def detect_deadlocks(self) -> List[str]:
        return [n for n, c in self.node_executions.items() if c > self.DEADLOCK_THRESHOLD]

    def set_sandbox_health(self, sandbox_id: str, status: str) -> None:
        with self._lock:
            self.sandbox_health[sandbox_id] = status
        self.log({"event": "sandbox_health", "sandbox_id": sandbox_id, "status": status})

    def get_metrics(self) -> dict:
        with self._lock:
            return {
                "total_events": len(self.events),
                "node_executions": dict(self.node_executions),
                "sandbox_health": dict(self.sandbox_health),
                "loops": self.detect_loops(),
                "deadlocks": self.detect_deadlocks(),
                "uptime_s": round(time.time() - self.start_time, 3),
            }

    def watch_openmanus(self, state) -> dict:
        """OpenManus: watchdog de tendencias, no eventos puntuales."""
        now = time.time()
        elapsed = now - self.start_time
        rate = len(self.events) / max(elapsed, 1.0)
        alerts = []
        if rate > 100:  # >100 eventos/s es sospechoso
            alerts.append({"type": "high_event_rate", "rate_per_s": round(rate, 2)})
        for nid, count in self.node_executions.items():
            if count > self.LOOP_THRESHOLD:
                alerts.append({"type": "node_loop", "node_id": nid, "count": count})
        return {
            "ts": now,
            "rate_per_s": round(rate, 3),
            "alerts": alerts,
            "healthy": len(alerts) == 0,
        }
root@vmi3428294:~# echo 