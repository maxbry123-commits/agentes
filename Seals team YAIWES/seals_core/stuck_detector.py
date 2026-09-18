"""
stuck_detector.py - P1-19 FIX. Antes: podia repetir la misma consulta
hasta 20 veces sin ninguna senal de que estaba atascado. Ahora: si la
misma accion + mismos argumentos + cero evidencia nueva se repite,
se declara STUCK y se cambia de estrategia o se bloquea con traza.
"""
import hashlib
import json


class DetectorDeAtasco:
    def __init__(self, umbral: int = 3):
        self.umbral = umbral
        self._historial: dict[str, int] = {}

    def _fingerprint(self, accion: str, args: dict, evidencia_nueva: bool) -> str:
        payload = json.dumps({"accion": accion, "args": args, "evidencia_nueva": evidencia_nueva}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def registrar_intento(self, accion: str, args: dict, hubo_evidencia_nueva: bool) -> tuple[bool, str]:
        """P1-19 aceptacion: no repetir 20 veces una operacion identica sin
        informacion nueva. Devuelve (esta_atascado, motivo)."""
        if hubo_evidencia_nueva:
            return False, "evidencia_nueva_reinicia_contador"
        fp = self._fingerprint(accion, args, hubo_evidencia_nueva)
        self._historial[fp] = self._historial.get(fp, 0) + 1
        if self._historial[fp] >= self.umbral:
            return True, f"BLOCKED_STUCK:misma_accion_x{self._historial[fp]}_sin_evidencia_nueva"
        return False, f"intento_{self._historial[fp]}_de_{self.umbral}"
