"""
Checkpoint Manager Module - PECP-MAXBRY-100x (Nodo T-011)
Gestión granular de checkpoints con verificación de integridad por SHA-256.
"""

from typing import Dict, Any, Optional
import hashlib
import json


class CheckpointManager:
    """Guarda y restaura estados comprobando integridad mediante hashing."""

    def __init__(self) -> None:
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Genera un hash SHA-256 determinista a partir de los datos."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def create_checkpoint(self, checkpoint_id: str, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea y registra un nuevo punto de restauración."""
        state_hash = self._compute_hash(state_data)
        record = {
            "checkpoint_id": checkpoint_id,
            "state_data": state_data,
            "hash": state_hash,
            "status": "VALID"
        }
        self._checkpoints[checkpoint_id] = record
        return {"checkpoint_id": checkpoint_id, "hash": state_hash, "created": True}

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Recupera el estado verificando la integridad del hash."""
        record = self._checkpoints.get(checkpoint_id)
        if not record:
            return None

        current_hash = self._compute_hash(record["state_data"])
        if current_hash != record["hash"]:
            record["status"] = "CORRUPTED"
            return None

        return record["state_data"]


if __name__ == "__main__":
    print("=== TEST NODO T-011: CHECKPOINT MANAGER ===")
    ckp = CheckpointManager()
    res = ckp.create_checkpoint("chk_001", {"node": "T-011", "step": "EXECUTE"})
    data = ckp.restore_checkpoint("chk_001")
    print(json.dumps({"creation": res, "restored_data": data}, indent=2))