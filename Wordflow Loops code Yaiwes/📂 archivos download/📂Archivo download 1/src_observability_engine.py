"""
Observability Engine Module - PECP-MAXBRY-100x (Nodo T-015)
Registro determinista de eventos, trazas en formato JSONL y métricas del sistema.
"""

from typing import Dict, Any, List
import json
import time


class ObservabilityEngine:
    """Administra el registro de auditoría, eventos de misión y métricas de ejecución."""

    def __init__(self) -> None:
        self.traces: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "total_events": 0,
            "errors_count": 0,
            "execution_times_ms": []
        }

    def log_event(self, mission_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra un evento con marca de tiempo e identificador de misión.
        """
        if not mission_id:
            raise ValueError("mission_id es obligatorio para todos los eventos de observabilidad.")

        event_record = {
            "mission_id": mission_id,
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": payload
        }

        self.traces.append(event_record)
        self.metrics["total_events"] += 1

        if "error" in event_type.lower():
            self.metrics["errors_count"] += 1

        return event_record

    def record_metric(self, name: str, value: float) -> None:
        """Suma o actualiza métricas clave del runtime."""
        if name not in self.metrics:
            self.metrics[name] = 0
        self.metrics[name] += value

    def export_traces_jsonl(self) -> str:
        """Exporta las trazas en formato JSONL estandarizado."""
        return "\n".join([json.dumps(t) for t in self.traces])


if __name__ == "__main__":
    print("=== TEST NODO T-015: OBSERVABILITY ENGINE ===")
    obs = ObservabilityEngine()
    obs.log_event("M-101", "node.start", {"nodo_id": "T-015"})
    obs.log_event("M-101", "node.done", {"nodo_id": "T-015", "score": 89})
    obs.record_metric("execution_time_ms", 35.5)

    print("Metrics Summary:", json.dumps(obs.metrics, indent=2))
    print("JSONL Output Preview:")
    print(obs.export_traces_jsonl())