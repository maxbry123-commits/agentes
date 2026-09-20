"""
Checkpoint Manager Module - PECP-MAXBRY-100x (Nodo T-011)
Gestion granular de checkpoints con verificacion de integridad por SHA-256.

PATCH 2026-09-20 (Salida 5 / G06 del contrato DSL DAG): persistencia
durable en SQLite en vez de dict en memoria. Antes: self._checkpoints =
{} se perdia en cada crash/restart del proceso -- G06 del contrato exige
"checkpoint durable que sobrevive crash". Mismo API publico
(create_checkpoint/restore_checkpoint), mismo formato de retorno: nadie
que ya importe CheckpointManager tiene que cambiar una linea.
"""

from typing import Dict, Any, Optional
import hashlib
import json
import os
import sqlite3


DEFAULT_DB_PATH = os.environ.get(
    "YAIWES_CHECKPOINT_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints.sqlite3"),
)


class CheckpointManager:
    """Guarda y restaura estados comprobando integridad mediante hashing.

    Persistencia: SQLite en disco (no dict en memoria). Sobrevive crash
    y restart del proceso -- una nueva instancia apuntando al mismo
    db_path ve los checkpoints creados por una instancia anterior.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    state_data TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Genera un hash SHA-256 determinista a partir de los datos."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def create_checkpoint(self, checkpoint_id: str, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea y registra un nuevo punto de restauracion (persistido en disco)."""
        state_hash = self._compute_hash(state_data)
        serialized = json.dumps(state_data, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints (checkpoint_id, state_data, hash, status) "
                "VALUES (?, ?, ?, ?)",
                (checkpoint_id, serialized, state_hash, "VALID"),
            )
        return {"checkpoint_id": checkpoint_id, "hash": state_hash, "created": True}

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Recupera el estado (desde disco) verificando la integridad del hash."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state_data, hash, status FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()
        if not row:
            return None
        serialized, stored_hash, _status = row
        state_data = json.loads(serialized)
        current_hash = self._compute_hash(state_data)
        if current_hash != stored_hash:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE checkpoints SET status = 'CORRUPTED' WHERE checkpoint_id = ?",
                    (checkpoint_id,),
                )
            return None
        return state_data


if __name__ == "__main__":
    print("=== TEST NODO T-011: CHECKPOINT MANAGER (durable) ===")
    ckp = CheckpointManager()
    res = ckp.create_checkpoint("chk_001", {"node": "T-011", "step": "EXECUTE"})
    data = ckp.restore_checkpoint("chk_001")
    print(json.dumps({"creation": res, "restored_data": data}, indent=2))
