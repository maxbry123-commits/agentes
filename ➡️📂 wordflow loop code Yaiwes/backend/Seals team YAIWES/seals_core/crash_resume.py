"""
crash_resume.py - FIX P1-27. Consume la persistencia del control plane
(CrazyWallAdapter, P0-07) - NO crea un segundo sistema de checkpoint
paralelo. CRASH -> NEW PROCESS -> LOAD STATE -> VERIFY HASH -> RESUME.
"""
import hashlib
import json


def resumir_desde_checkpoint(crazy_wall_adapter, node_id: int) -> tuple[bool, str, dict | None]:
    """P1-27 aceptacion: crash test reproducible. Lee el checkpoint que
    ya vive en Crazy Wall (CrazyWallAdapter, no un archivo local nuevo),
    verifica su integridad, y decide si es seguro resumir."""
    try:
        crazy_wall, _sha = crazy_wall_adapter._leer_fresco()
    except Exception as e:
        return False, f"NO_SE_PUDO_LEER_CRAZY_WALL:{e}", None

    for nodo in crazy_wall.get("nodes", []):
        if nodo.get("id") == node_id:
            checkpoint = nodo.get("checkpoint", {}).get("after")
            if checkpoint is None:
                return False, "SIN_CHECKPOINT_PREVIO_NO_HAY_QUE_RESUMIR", None
            hash_esperado = checkpoint.get("_integrity_hash")
            checkpoint_sin_hash = {k: v for k, v in checkpoint.items() if k != "_integrity_hash"}
            hash_real = _hash_checkpoint(checkpoint_sin_hash)
            if hash_esperado and hash_esperado != hash_real:
                return False, "CHECKPOINT_CORRUPTO_HASH_NO_COINCIDE", None
            return True, "RESUME_SEGURO", checkpoint_sin_hash

    return False, "NODO_NO_ENCONTRADO", None


def guardar_checkpoint_con_hash(crazy_wall_adapter, node_id: int, dato: dict) -> tuple[bool, str]:
    """Envuelve CrazyWallAdapter.checkpoint() anadiendo el hash de
    integridad, para que resumir_desde_checkpoint pueda verificarlo."""
    dato_con_hash = {**dato, "_integrity_hash": _hash_checkpoint(dato)}
    return crazy_wall_adapter.checkpoint(node_id, dato_con_hash)


def _hash_checkpoint(dato: dict) -> str:
    payload = json.dumps(dato, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
