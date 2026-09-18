"""
test_p0_05_06_07.py - Tests de goal_tracking, evidence, y CrazyWallAdapter.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evidence import EvidenceRecord, exigir_evidencia_para_pass
from goal_tracking import GoalContract


def test_P0_06_pass_sin_evidence_record_es_rechazado():
    status, motivo = exigir_evidencia_para_pass("PASS", None)
    assert status == "GAP"
    assert "SIN_EVIDENCE_RECORD" in motivo


def test_P0_06_evidence_record_incompleto_es_rechazado():
    ev = EvidenceRecord(path="", mission_id="m1", node_id="n1", operation="test")
    status, motivo = exigir_evidencia_para_pass("PASS", ev)
    assert status == "GAP"


def test_P0_06_evidence_record_completo_pasa():
    ev = EvidenceRecord(path="x.py", mission_id="m1", node_id="n1", operation="install", sha256="abc123")
    status, motivo = exigir_evidencia_para_pass("PASS", ev)
    assert status == "PASS"


def test_P0_05_no_cierra_sin_acceptance_declarado():
    goal = GoalContract(goal_id="g1", objective="instalar componente X")
    ok, motivo = goal.completion_audit()
    assert ok is False
    assert "SIN_ACCEPTANCE" in motivo


def test_P0_05_no_cierra_con_acceptance_sin_demostrar():
    goal = GoalContract(goal_id="g1", objective="x", acceptance=["a1", "a2"])
    ev = EvidenceRecord(path="x", mission_id="m", node_id="n", operation="op", sha256="s")
    goal.registrar_evidencia_de_acceptance("a1", ev)
    ok, motivo = goal.completion_audit()
    assert ok is False
    assert "a2" in motivo


def test_P0_05_cierra_solo_cuando_todo_demostrado():
    goal = GoalContract(goal_id="g1", objective="x", acceptance=["a1"])
    ev = EvidenceRecord(path="x", mission_id="m", node_id="n", operation="op", sha256="s")
    goal.registrar_evidencia_de_acceptance("a1", ev)
    ok, motivo = goal.completion_audit()
    assert ok is True
    assert goal.completion_status == "VERIFIED_CLOSED"


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


class _FakeHTTP:
    """Simula GitHub: cada PUT cambia el sha, cada GET devuelve el sha actual."""

    def __init__(self):
        import base64
        import json as _json
        self.sha = "sha_inicial"
        self.contenido = {"nodes": [{"id": 1, "lock": "FREE", "owner": None}]}
        self._b64 = base64
        self._json = _json

    def get(self, url, headers=None, timeout=None):
        contenido_b64 = self._b64.b64encode(self._json.dumps(self.contenido).encode()).decode()
        return _FakeResponse(200, {"content": contenido_b64, "sha": self.sha})

    def put(self, url, headers=None, json=None, timeout=None):
        self.contenido = self._json.loads(self._b64.b64decode(json["content"]).decode())
        self.sha = "sha_" + str(len(self.sha))  # cambia en cada escritura
        return _FakeResponse(200)


def test_P0_07_claim_con_readback():
    from crazy_wall_adapter import CrazyWallAdapter

    fake_http = _FakeHTTP()
    adapter = CrazyWallAdapter(token="fake", sesion_http=fake_http)
    ok, motivo = adapter.claim(1, "worker-001")
    assert ok is True
    assert fake_http.contenido["nodes"][0]["lock"] == "CLAIMED"
    assert fake_http.contenido["nodes"][0]["owner"] == "worker-001"


def test_P0_07_no_permite_doble_claim():
    from crazy_wall_adapter import CrazyWallAdapter

    fake_http = _FakeHTTP()
    adapter = CrazyWallAdapter(token="fake", sesion_http=fake_http)
    adapter.claim(1, "worker-001")
    ok, motivo = adapter.claim(1, "worker-002")
    assert ok is False
    assert "ya_reclamado" in motivo
