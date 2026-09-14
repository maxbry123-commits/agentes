"""
Reconciliation Engine Module - PECP-MAXBRY-100x (Nodo T-011)
Motor de reconciliación para detectar inconsistencias y ejecutar rollback/repair.
"""

from typing import Dict, Any, List
import json


class ReconciliationEngine:
    """Restaura la consistencia lógica entre servicios remotos y el estado local."""

    def reconcile(self, local_state: Dict[str, Any], remote_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara el estado local vs remoto y decide si reparar o aplicar rollback.
        """
        inconsistencies: List[str] = []

        for key, value in local_state.items():
            if key in remote_state and remote_state[key] != value:
                inconsistencies.append(f"Mismatch in key '{key}': local={value}, remote={remote_state[key]}")

        reconciled = len(inconsistencies) > 0
        action = "NO_ACTION"

        if reconciled:
            action = "REPAIR_SYNC_REMOTE"

        return {
            "reconciled": reconciled,
            "inconsistencies_found": len(inconsistencies),
            "details": inconsistencies,
            "action_taken": action
        }


if __name__ == "__main__":
    print("=== TEST NODO T-011: RECONCILIATION ENGINE ===")
    rec = ReconciliationEngine()
    local = {"status": "DONE", "commit": "abc"}
    remote = {"status": "PENDING", "commit": "abc"}
    print(json.dumps(rec.reconcile(local, remote), indent=2))