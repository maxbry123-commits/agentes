"""
idempotencia.py - P0-11 FIX (integracion Meta Muse Code). mission_id UUID
solo identificaba, no impedia repetir side effects. Ahora:
SAME command_id + SAME payload -> JOIN/REPLAY (se devuelve el resultado ya obtenido)
SAME command_id + DIFFERENT payload -> IDEMPOTENCY_CONFLICT (rechazo)
"""
import hashlib
import json


class RegistroIdempotencia:
    """En memoria del proceso worker. El registro DURABLE (para sobrevivir
    un crash) vive en el CrazyWallAdapter/evidencia - esto es la capa
    rapida de deteccion antes de tocar el side effect."""

    def __init__(self):
        self._registro: dict[str, dict] = {}

    def fingerprint(self, tarea: dict) -> str:
        payload_canonico = json.dumps(
            {k: v for k, v in tarea.items() if k != "mission_id"},
            sort_keys=True,
        )
        return hashlib.sha256(payload_canonico.encode("utf-8")).hexdigest()

    def verificar(self, command_id: str, tarea: dict) -> tuple[str, dict | None]:
        """Devuelve (accion, resultado_previo_o_None).
        accion es una de: EJECUTAR, REPLAY, IDEMPOTENCY_CONFLICT."""
        fp_actual = self.fingerprint(tarea)
        previo = self._registro.get(command_id)
        if previo is None:
            return "EJECUTAR", None
        if previo["fingerprint"] == fp_actual:
            return "REPLAY", previo["resultado"]
        return "IDEMPOTENCY_CONFLICT", None

    def registrar_resultado(self, command_id: str, tarea: dict, resultado: dict) -> None:
        self._registro[command_id] = {
            "fingerprint": self.fingerprint(tarea),
            "resultado": resultado,
        }


# Instancia compartida del proceso worker actual (no durable entre
# crashes - la durabilidad real vive en Crazy Wall via CrazyWallAdapter).
REGISTRO_GLOBAL = RegistroIdempotencia()
