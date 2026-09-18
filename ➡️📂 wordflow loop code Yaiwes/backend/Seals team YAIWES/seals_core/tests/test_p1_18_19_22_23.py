"""
test_p1_18_19_22_23.py - Tests stuck detector, research real, work surface.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stuck_detector import DetectorDeAtasco
from research_real import ResearchResult, construir_desde_respuesta_llm
from work_surface import WorkSurface, FrontendGateResult, determinar_work_surface


def test_P1_19_no_repite_20_veces_sin_evidencia():
    detector = DetectorDeAtasco(umbral=3)
    for _ in range(2):
        atascado, _ = detector.registrar_intento("consultar_cerebras", {"q": "x"}, hubo_evidencia_nueva=False)
        assert atascado is False
    atascado, motivo = detector.registrar_intento("consultar_cerebras", {"q": "x"}, hubo_evidencia_nueva=False)
    assert atascado is True
    assert "BLOCKED_STUCK" in motivo


def test_P1_19_evidencia_nueva_reinicia():
    detector = DetectorDeAtasco(umbral=3)
    detector.registrar_intento("x", {}, False)
    detector.registrar_intento("x", {}, False)
    atascado, motivo = detector.registrar_intento("x", {}, True)
    assert atascado is False
    assert "reinicia" in motivo


def test_P1_18_solo_opinion_llm_no_es_evidencia_real():
    rr = construir_desde_respuesta_llm("como resolver X", "RESUELTO: usa Y")
    ok, motivo = rr.es_evidencia_real()
    assert ok is False
    assert "SOLO_OPINION_LLM" in motivo or "NO_NEW_EVIDENCE" in motivo


def test_P1_18_con_fuentes_y_cross_check_si_es_evidencia():
    rr = ResearchResult(
        query="x", sources=["github.com/x/y"], source_type="github",
        claims=["esto funciona"], cross_check=["confirmado en docs oficiales"],
        new_evidence=True,
    )
    ok, motivo = rr.es_evidencia_real()
    assert ok is True


def test_P1_22_work_surface_falla_cerrado_a_backend_si_no_declarado():
    ws = determinar_work_surface({"tipo": "instalar_paquete"})
    assert ws == WorkSurface.BACKEND


def test_P1_22_work_surface_respeta_declaracion_explicita():
    ws = determinar_work_surface({"work_surface": "FRONTEND"})
    assert ws == WorkSurface.FRONTEND


def test_P1_23_frontend_no_pasa_sin_los_3_gates():
    resultado = FrontendGateResult(code_pass=True, browser_pass=False, visual_pass=False)
    ok, motivo = resultado.pass_completo()
    assert ok is False
    assert "BROWSER_PASS" in motivo


def test_P1_23_frontend_pasa_solo_con_los_3():
    resultado = FrontendGateResult(code_pass=True, browser_pass=True, visual_pass=True)
    ok, motivo = resultado.pass_completo()
    assert ok is True
