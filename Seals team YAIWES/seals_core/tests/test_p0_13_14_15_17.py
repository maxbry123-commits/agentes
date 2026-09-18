"""
test_p0_13_14_15_17.py - Tests de commit reproducible, verificacion real,
sheriff/policy, y ToolResult tipado.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sheriff_policy import StructuredAction, aprobar
from tool_result import ToolResult


def test_P0_15_accion_no_permitida_se_deniega():
    accion = StructuredAction(action="rm_recursivo_peligroso", target_path="x", params={})
    ok, motivo = aprobar(accion, Path("/tmp/workspace"))
    assert ok is False
    assert "ACCION_NO_PERMITIDA" in motivo


def test_P0_15_path_traversal_se_deniega(tmp_path):
    accion = StructuredAction(action="git_clone", target_path="../../etc/passwd", params={})
    ok, motivo = aprobar(accion, tmp_path)
    assert ok is False
    assert "PATH_TRAVERSAL" in motivo or "PATH_INVALIDO" in motivo


def test_P0_15_accion_valida_se_aprueba(tmp_path):
    accion = StructuredAction(action="git_clone", target_path="mi_componente", params={"repo_url": "https://x"})
    ok, motivo = aprobar(accion, tmp_path)
    assert ok is True


def test_P0_17_tool_result_error_se_convierte_en_observation():
    tr = ToolResult(ok=False, error_type="GIT_CLONE_FAILED", stderr="fatal: repository not found")
    obs = tr.como_observacion()
    assert obs["tipo"] == "OBSERVATION"
    assert obs["ok"] is False
    assert obs["error_type"] == "GIT_CLONE_FAILED"


def test_P0_14_directorio_sin_manifest_no_es_instalado(tmp_path):
    from instalador_deterministico import _verificar_instalacion_previa

    destino = tmp_path / "componente_sospechoso"
    destino.mkdir()
    ok, motivo = _verificar_instalacion_previa(destino, "https://github.com/x/y.git", destino / ".instalacion_manifest.json")
    assert ok is False
    assert "SIN_MANIFEST" in motivo
