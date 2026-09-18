"""
test_p1_20_21_25_26_29.py - Tests worker_bootstrap, isolation,
recovery_types, llm_output_schema.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from worker_bootstrap import ConfigContract, cargar_y_validar, verificar_nodo_autorizado
from isolation import WorkerIdentity, RegistroDeEscritura
from recovery_types import ClaseDeFallo, clasificar_fallo, politica_para
from llm_output_schema import parsear_respuesta_llm


def test_P1_20_bloquea_si_faltan_secretos(monkeypatch):
    import os
    for k in list(os.environ.keys()):
        if k.startswith("CEREBRAS_API_KEY") or k in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN"):
            monkeypatch.delenv(k, raising=False)
    contract = ConfigContract(worker_id="w1", assigned_node=1, write_scope="/tmp/x")
    resultado = cargar_y_validar(contract)
    assert resultado.ready is False
    assert resultado.estado == "BLOCKED_MISSING_SECRETS"


def test_P1_21_worker_no_ejecuta_nodo_no_autorizado():
    contract = ConfigContract(worker_id="w1", assigned_node=5, write_scope="/x")
    ok, motivo = verificar_nodo_autorizado(contract, 99)
    assert ok is False
    assert "NODO_NO_AUTORIZADO" in motivo


def test_P1_25_dos_workers_no_escriben_mismo_scope():
    registro = RegistroDeEscritura()
    w1 = WorkerIdentity("p", "c1", "n1", "claim1", "/ws1", "sha1", "scope-A", "cmd1")
    w2 = WorkerIdentity("p", "c2", "n1", "claim2", "/ws2", "sha1", "scope-A", "cmd2")
    ok1, _ = registro.reclamar_scope(w1)
    assert ok1 is True
    ok2, motivo = registro.reclamar_scope(w2)
    assert ok2 is False
    assert "OCUPADO" in motivo


def test_P1_26_clasifica_auth_error():
    clase = clasificar_fallo("AUTH_ERROR", "no hay CEREBRAS_API_KEY")
    assert clase == ClaseDeFallo.AUTH
    assert politica_para(clase) == "bloquear_y_avisar_credenciales"


def test_P1_26_clasifica_retryable():
    clase = clasificar_fallo("TIMEOUT", "")
    assert clase == ClaseDeFallo.RETRYABLE


def test_P1_29_rechaza_respuesta_vacia():
    assert parsear_respuesta_llm("") is None
    assert parsear_respuesta_llm("ERROR_CEREBRAS: fallo") is None


def test_P1_29_acepta_respuesta_valida():
    decision = parsear_respuesta_llm("Si encaja con YAIWES")
    assert decision is not None
    assert decision.decision.startswith("Si encaja")
