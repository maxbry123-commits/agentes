"""
test_p0_fixes.py - Regression tests de las 4 simulaciones de la auditoria 5x.
SIM-01, SIM-02 quedan como test automatico permanente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ejecutor import ejecutar_tarea


def test_SIM01_existencia_falsa_ya_no_es_pass():
    """ANTES: PASS + existe:false. AHORA: GAP."""
    tarea = {"tipo": "verificar_existencia", "nombre": "archivo_que_no_existe_123.xyz"}
    resultado = ejecutar_tarea(tarea)
    assert resultado["status"] == "GAP", "SIM-01 sigue rota: existencia falsa dio PASS"
    assert resultado["evidencia"]["existe"] is False


def test_SIM01b_existencia_real_si_es_pass():
    tarea = {"tipo": "verificar_existencia", "nombre": "ejecutor.py"}
    resultado = ejecutar_tarea(tarea)
    assert resultado["status"] == "PASS"
    assert resultado["evidencia"]["existe"] is True


def test_SIM02_error_cerebras_ya_no_es_pass(monkeypatch):
    """ANTES: PASS + ERROR en evidencia. AHORA: GAP tipado."""
    import ejecutor as ejecutor_mod

    def fake_error(contexto, pregunta):
        return "ERROR: no hay CEREBRAS_API_KEY_1..6 configuradas"

    monkeypatch.setattr(ejecutor_mod, "consultar_experto_cerebras", fake_error)
    tarea = {"tipo": "evaluar_componente", "nombre": "algo"}
    resultado = ejecutor_mod.ejecutar_tarea(tarea)
    assert resultado["status"] == "GAP", "SIM-02 sigue rota: error de provider dio PASS"
    assert resultado["evidencia"]["tipo_error"] == "PROVIDER_ERROR_OR_AUTH_ERROR"


def test_SIM02b_respuesta_valida_si_es_pass(monkeypatch):
    import ejecutor as ejecutor_mod

    def fake_ok(contexto, pregunta):
        return "Si encaja, usa el patron REUSE_EXISTING"

    monkeypatch.setattr(ejecutor_mod, "consultar_experto_cerebras", fake_ok)
    tarea = {"tipo": "evaluar_componente", "nombre": "algo"}
    resultado = ejecutor_mod.ejecutar_tarea(tarea)
    assert resultado["status"] == "PASS"


def test_P0_04_veredicto_claude_marcado_como_opinion(monkeypatch):
    """El veredicto de diseno_arquitectura debe quedar marcado como opinion
    advisory, nunca como oraculo objetivo (P0-04)."""
    import ejecutor as ejecutor_mod

    def fake_veredicto(tarea):
        return {"status": "PASS", "detalle": "CORRECTO segun analisis"}

    monkeypatch.setattr(ejecutor_mod, "verificar_con_claude", fake_veredicto)
    tarea = {"tipo": "diseno_arquitectura", "nombre": "algo"}
    resultado = ejecutor_mod.ejecutar_tarea(tarea)
    assert resultado["evidencia"]["tipo_veredicto"] == "LLM_ADVISORY_OPINION_NO_ES_ORACLE_OBJETIVO"
