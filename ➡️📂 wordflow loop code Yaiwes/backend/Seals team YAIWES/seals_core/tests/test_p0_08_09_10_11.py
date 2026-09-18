"""
test_p0_08_09_10_11.py - Tests watchdog (campo real + reencolado) e idempotencia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from idempotencia import RegistroIdempotencia


def test_P0_08_campo_real_es_wall_status():
    import watchdog
    assert watchdog.CAMPO_STATUS_REAL == "wall_status", "P0-08 sigue roto: campo incorrecto"


def test_P0_09_reencolar_en_inserta_tareas_reales():
    import watchdog

    cola = []
    pendientes = [{"name": "AgentGuard"}, {"name": "AgentScope"}]
    n = watchdog.reencolar_en(cola, pendientes)
    assert n == 2
    assert len(cola) == 2
    assert cola[0]["tipo"] == "verificar_existencia"
    assert cola[0]["nombre"] == "AgentGuard"


def test_P0_11_mismo_id_mismo_payload_es_replay():
    registro = RegistroIdempotencia()
    tarea = {"tipo": "verificar_existencia", "nombre": "x.py"}
    accion1, _ = registro.verificar("cmd-1", tarea)
    assert accion1 == "EJECUTAR"
    registro.registrar_resultado("cmd-1", tarea, {"status": "PASS"})

    accion2, resultado = registro.verificar("cmd-1", tarea)
    assert accion2 == "REPLAY"
    assert resultado == {"status": "PASS"}


def test_P0_11_mismo_id_payload_distinto_es_conflict():
    registro = RegistroIdempotencia()
    tarea1 = {"tipo": "verificar_existencia", "nombre": "x.py"}
    tarea2 = {"tipo": "verificar_existencia", "nombre": "y.py"}
    registro.verificar("cmd-1", tarea1)
    registro.registrar_resultado("cmd-1", tarea1, {"status": "PASS"})

    accion, _ = registro.verificar("cmd-1", tarea2)
    assert accion == "IDEMPOTENCY_CONFLICT"
