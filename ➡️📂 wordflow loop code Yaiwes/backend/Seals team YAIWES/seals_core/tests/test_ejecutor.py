"""
test_ejecutor.py - Cumple la regla del proyecto: no PASS sin test.
Cubre: verificar_existencia (0% LLM, sin mocks necesarios) y que
mission_id se genera y se conserva en la evidencia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ejecutor import ejecutar_tarea, registrar_evidencia


def test_verificar_existencia_archivo_real():
    tarea = {"tipo": "verificar_existencia", "nombre": "ejecutor.py"}
    resultado = ejecutar_tarea(tarea)
    assert resultado["status"] == "PASS"
    assert resultado["evidencia"]["existe"] is True


def test_verificar_existencia_archivo_inexistente():
    tarea = {"tipo": "verificar_existencia", "nombre": "esto_no_existe_123.xyz"}
    resultado = ejecutar_tarea(tarea)
    assert resultado["status"] == "PASS"
    assert resultado["evidencia"]["existe"] is False


def test_mission_id_se_genera_si_no_viene():
    tarea = {"tipo": "verificar_existencia", "nombre": "ejecutor.py"}
    resultado = ejecutar_tarea(tarea)
    assert "mission_id" in resultado
    assert len(resultado["mission_id"]) > 0


def test_mission_id_se_conserva_si_ya_viene():
    tarea = {"tipo": "verificar_existencia", "nombre": "ejecutor.py", "mission_id": "fijo-123"}
    resultado = ejecutar_tarea(tarea)
    assert resultado["mission_id"] == "fijo-123"


def test_registrar_evidencia_escribe_jsonl(tmp_path, monkeypatch):
    import ejecutor
    monkeypatch.setattr(ejecutor, "RAIZ", tmp_path)
    tarea = {"tipo": "verificar_existencia", "nombre": "x", "mission_id": "abc"}
    resultado = {"status": "PASS", "mission_id": "abc", "evidencia": {}}
    registrar_evidencia(tarea, resultado)
    log = tmp_path / "evidencia_local.jsonl"
    assert log.exists()
    assert "abc" in log.read_text()
