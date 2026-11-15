"""
Rate Limit Governor Module - PECP-MAXBRY-100x (Nodo T-007)
Gobernador de tasa de peticiones con algoritmo de ventana y cálculo de backoff.
"""

from typing import Dict, Any
import time
import json


class RateLimitGovernor:
    """Controla el flujo de peticiones salientes para evitar saturación o bloqueos por API."""

    def __init__(self, default_limit: int = 100, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.request_counters: Dict[str, int] = {}
        self.last_reset: Dict[str, float] = {}

    def _check_window(self, provider: str) -> None:
        """Reinicia el contador si la ventana de tiempo ha expirado."""
        now = time.time()
        if provider not in self.last_reset or (now - self.last_reset[provider]) > self.window_seconds:
            self.request_counters[provider] = 0
            self.last_reset[provider] = now

    def acquire_slot(self, provider: str) -> Dict[str, Any]:
        """
        Informa si una petición puede proceder o calcula el tiempo de espera (backoff).
        """
        self._check_window(provider)
        current_count = self.request_counters.get(provider, 0)

        if current_count < self.default_limit:
            self.request_counters[provider] = current_count + 1
            return {
                "provider": provider,
                "allowed": True,
                "backoff_ms": 0,
                "remaining_slots": self.default_limit - (current_count + 1)
            }

        # Calcular backoff determinista si se superó el límite
        backoff_ms = 1000  # Backoff estándar
        return {
            "provider": provider,
            "allowed": False,
            "backoff_ms": backoff_ms,
            "remaining_slots": 0
        }


if __name__ == "__main__":
    print("=== TEST NODO T-007: RATE LIMIT GOVERNOR ===")
    governor = RateLimitGovernor(default_limit=2)
    p1 = governor.acquire_slot("github")
    p2 = governor.acquire_slot("github")
    p3 = governor.acquire_slot("github")
    print(json.dumps({"peticion_1": p1, "peticion_2": p2, "peticion_3_bloqueada": p3}, indent=2))
