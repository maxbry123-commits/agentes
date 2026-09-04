"""
Recovery Engine Module - PECP-MAXBRY-100x (Nodo T-011)
Protocolo RT-80 para auto-recuperación y escalación determinista.
"""

from typing import Dict, Any
import json
from src.recovery.classifier import FailureClassifier
from src.recovery.checkpoint import CheckpointManager
from src.recovery.reconciliation import ReconciliationEngine


class RecoveryEngine:
    """Orquesta la recuperación ante errores ejecutando la compuerta RT-80."""

    MAX_RETRIES: int = 3

    def __init__(self) -> None:
        self.classifier = FailureClassifier()
        self.checkpoint_mgr = CheckpointManager()
        self.reconciliation = ReconciliationEngine()

    def handle_failure(self, node_id: str, error_msg: str, attempt: int, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el protocolo RT-80: Clasifica -> Intenta recuperación/reconciliación -> Escala si procede.
        """
        classification = self.classifier.classify(error_msg)
        ckp_res = self.checkpoint_mgr.create_checkpoint(f"{node_id}_fail_{attempt}", current_state)

        if classification["is_retryable"] and attempt < self.MAX_RETRIES:
            return {
                "protocol": "RT-80",
                "action": "RETRY",
                "attempt": attempt + 1,
                "node_id": node_id,
                "checkpoint": ckp_res["hash"],
                "classification": classification
            }

        return {
            "protocol": "RT-80",
            "action": "ESCALATE_TO_DIRECTOR",
            "attempt": attempt,
            "node_id": node_id,
            "checkpoint": ckp_res["hash"],
            "classification": classification,
            "reason": "Max retries exceeded or non-retryable error"
        }


if __name__ == "__main__":
    print("=== TEST NODO T-011: RECOVERY ENGINE ===")
    engine = RecoveryEngine()
    res1 = engine.handle_failure("T-011", "HTTP 429 Too Many Requests", attempt=1, current_state={"step": 1})
    res2 = engine.handle_failure("T-011", "JSONSchema ValidationError", attempt=1, current_state={"step": 1})
    print(json.dumps({"test_retry": res1, "test_escalate": res2}, indent=2))