"""
tests/test_mvp.py — Smoke test del Orquestador Universal v1.0.

Testea:
- L1 Goal Lock: hash creado, dag validado
- L2 Consensus: con consensus_mode="single" no falla
- 10 loops en topological_order
- Sheriff: 6 gates definidos
- Juez: 3 simulaciones
- Sentinel: eventos, métricas
- State: persist atómico + load
"""
import os
import sys
import json
import tempfile
import pytest

# Path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import WorkflowState, atomic_write_json, hash_goal
from orchestrator.sentinel import Sentinel
from orchestrator.sheriff import Sheriff, Verdict, Validador, Verificador
from orchestrator.juez import Judge
from orchestrator.repair import RepairEngine
from orchestrator.orchestrator import Orchestrator, run_orchestrator, DAGEngine, node


TEMPLATE_BASIC = {
    "objetivo": "test objetivo",
    "planificar": ["a", "b"],
    "tareas": ["t1"],
    "metas": ["m1"],
    "proposito": "p",
    "refutaciones": ["r1"],
}


# ============================================================================
# Test state.py
# ============================================================================

def test_hash_goal_is_deterministic():
    h1 = hash_goal("objetivo X")
    h2 = hash_goal("objetivo X")
    assert h1 == h2
    assert len(h1) == 16


def test_hash_goal_differs():
    assert hash_goal("a") != hash_goal("b")


def test_workflow_state_goal_lock():
    state = WorkflowState(input_data={"objetivo": "build API"})
    assert state.goal_hash != ""
    assert len(state.goal_hash) == 16


def test_atomic_write_json_creates_file(tmp_path):
    p = tmp_path / "test.json"
    atomic_write_json(str(p), {"a": 1, "b": [1, 2, 3]})
    assert p.exists()
    with open(p) as f:
        data = json.load(f)
    assert data == {"a": 1, "b": [1, 2, 3]}


def test_workflow_state_persist_and_load(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = WorkflowState(input_data={"objetivo": "x"})
    state.completed_nodes.append("L1_goal_lock")
    state.persist()
    loaded = WorkflowState.load()
    assert "L1_goal_lock" in loaded.completed_nodes


# ============================================================================
# Test sentinel.py
# ============================================================================

def test_sentinel_log_and_metrics():
    s = Sentinel()
    s.log({"event": "test", "node_id": "N1"})
    s.log({"event": "test", "node_id": "N1"})
    s.log({"event": "test", "node_id": "N2"})
    m = s.get_metrics()
    assert m["total_events"] == 3
    assert m["node_executions"]["N1"] == 2
    assert m["node_executions"]["N2"] == 1


def test_sentinel_detect_loops():
    s = Sentinel()
    for _ in range(5):
        s.log({"event": "x", "node_id": "loop_node"})
    loops = s.detect_loops()
    assert "loop_node" in loops


def test_sentinel_openmanus_watch():
    s = Sentinel()
    s.log({"event": "x"})
    r = s.watch_openmanus(None)  # state=None es válido aquí
    assert "rate_per_s" in r
    assert "alerts" in r
    assert "healthy" in r


# ============================================================================
# Test sheriff.py
# ============================================================================

def test_sheriff_has_6_gates():
    sh = Sheriff()
    assert len(sh.gates) == 6
    expected = {"completitud", "coherencia", "formato",
                "sandbox_isolation", "repairs_ok", "approval"}
    assert set(sh.gates.keys()) == expected


def test_sheriff_validate_completitud_ok():
    sh = Sheriff()
    v = sh.validate({"status": "ok"}, "completitud", state=None)
    assert v.verdict == Verdict.GO


def test_sheriff_validate_completitud_fail():
    sh = Sheriff()
    v = sh.validate({"status": "weird"}, "completitud", state=None)
    assert v.verdict == Verdict.NO_GO


def test_sheriff_validate_unknown_gate():
    sh = Sheriff()
    v = sh.validate({}, "nonexistent", state=None)
    assert v.verdict == Verdict.NO_GO


def test_validador_required_fields():
    val = Validador()
    r = val.validate({"a": 1, "b": 2}, ["a", "b", "c"])
    assert not r["valid"]
    assert "c" in r["missing"]


def test_validador_type_errors():
    val = Validador()
    r = val.validate({"a": "string"}, [], {"a": int})
    assert not r["valid"]
    assert len(r["type_errors"]) == 1


# ============================================================================
# Test juez.py
# ============================================================================

def test_juez_real_pasa():
    j = Judge()
    r = j.run_simulations({"status": "ok"})
    assert r["all_passed"] is True
    assert r["simulations"]["real"]["verdict"] == "GO"


def test_juez_real_falla_status_invalido():
    j = Judge()
    r = j.run_simulations({"status": "weird"})
    assert r["all_passed"] is False


def test_juez_adversarial_detecta_todo():
    j = Judge()
    r = j.run_simulations({"status": "ok", "code": "TODO: fix"})
    assert r["simulations"]["adversarial"]["verdict"] == "NO_GO"


def test_juez_adversarial_pasa():
    j = Judge()
    r = j.run_simulations({"status": "ok", "code": "def f(): return 1"})
    assert r["simulations"]["adversarial"]["verdict"] == "GO"


def test_juez_escribe_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    j = Judge()
    r = j.run_simulations({"status": "ok", "value": 42})
    assert r["all_passed"] is True
    assert r["baseline_written"] is True
    assert os.path.exists("baseline_output.json")
    with open("baseline_output.json") as f:
        baseline = json.load(f)
    assert baseline["source_output"]["value"] == 42


def test_juez_regression_sin_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    j = Judge()
    r = j.run_simulations({"status": "ok"})
    assert r["simulations"]["regression"]["verdict"] == "GO"
    assert r["simulations"]["regression"]["reason"] == "sin_baseline"


# ============================================================================
# Test repair.py
# ============================================================================

class FakeAgent:
    def __init__(self, success=True, diff="--- a/x\n+++ b/x\n"):
        self.success = success
        self.diff = diff
        self.agent_type = "fake"
        self.sandbox = None

    def repair(self, original_diff, error, context):
        from orchestrator.agents import AgentResult
        return AgentResult(self.success, {"diff": self.diff}, "", 0.0, 0, self.diff)

    def verify(self, diff, context):
        from orchestrator.agents import AgentResult
        return AgentResult(self.success, {}, "", 0.0, 0, "")


def test_repair_recovered():
    s = Sentinel()
    state = WorkflowState(input_data={"objetivo": "x"})
    engine = RepairEngine(mimo_agent=FakeAgent(success=True), sentinel=s, max_repairs=2)
    r = engine.run("N1", "old diff", "some error", state, {})
    assert r.get("recovered") is True


def test_repair_escalate_after_max():
    s = Sentinel()
    state = WorkflowState(input_data={"objetivo": "x"})
    state.repair_counts["N1"] = 2  # ya gastó sus 2 intentos
    engine = RepairEngine(mimo_agent=FakeAgent(success=False), sentinel=s, max_repairs=2)
    r = engine.run("N1", "old diff", "error", state, {})
    assert r.get("escalated") is True


# ============================================================================
# Test orchestrator.py: 10 loops
# ============================================================================

def test_orchestrator_has_10_nodes():
    orch = Orchestrator(TEMPLATE_BASIC, consensus_mode="single")
    order = orch.dag.topological_order()
    assert len(order) == 10
    expected_prefixes = ["L1_", "L2_", "L3_", "L4_", "L5_",
                         "L6_", "L7_", "L8_", "L9_", "L10_"]
    actual_prefixes = [n.split("_")[0] + "_" for n in order]
    assert actual_prefixes == expected_prefixes


def test_orchestrator_dag_no_cycles():
    orch = Orchestrator(TEMPLATE_BASIC, consensus_mode="single")
    assert not orch.dag.has_cycles()


def test_orchestrator_l1_goal_lock():
    orch = Orchestrator(TEMPLATE_BASIC, consensus_mode="single")
    r = orch.L1_goal_lock()
    assert r["status"] == "ok"
    assert r["goal_hash"] != ""
    assert "dag_order" in r


def test_orchestrator_l2_consensus_single_mode():
    orch = Orchestrator(TEMPLATE_BASIC, consensus_mode="single")
    # L1 primero
    orch.L1_goal_lock()
    r = orch.L2_consensus_plan()
    assert r["status"] == "ok"
    assert r["consensus_mode"] == "single"


def test_orchestrator_run_smoke(tmp_path, monkeypatch):
    """Smoke test del run completo (sin docker real, con agentes que no se pueden inicializar)."""
    monkeypatch.chdir(tmp_path)
    template = {**TEMPLATE_BASIC, "consensus": "single"}
    # El run va a fallar en L3 (no hay docker) pero L1 y L2 deben completar
    # En este test solo verificamos que el orquestador arranca
    orch = Orchestrator(template, work_dir=str(tmp_path), consensus_mode="single")
    order = orch.dag.topological_order()
    assert len(order) == 10


@pytest.mark.skipif(os.environ.get("SKIP_DOCKER_TESTS") is not None,
                    reason="requires docker (skipped in sandbox)")
def test_run_orchestrator_api():
    """Test de la API pública run_orchestrator. Requiere docker (skipped en sandbox)."""
    template = {**TEMPLATE_BASIC, "consensus": "single"}
    result = run_orchestrator(template, work_dir="/tmp/test_orch",
                              consensus_mode="single")
    assert "status" in result
    assert "completed_nodes" in result
    assert "goal_hash" in result
    assert "metrics" in result


# ============================================================================
# Test DAG engine
# ============================================================================

def test_dag_topological_order():
    dag = DAGEngine()

    @node("A")
    def a(): pass

    @node("B", depends_on=["A"])
    def b(): pass

    @node("C", depends_on=["A", "B"])
    def c(): pass

    for f in [a, b, c]:
        dag.add_node(f)

    order = dag.topological_order()
    assert order.index("A") < order.index("B") < order.index("C")


def test_dag_has_cycles_false():
    dag = DAGEngine()

    @node("X")
    def x(): pass

    @node("Y", depends_on=["X"])
    def y(): pass

    for f in [x, y]:
        dag.add_node(f)
    assert not dag.has_cycles()


# ============================================================================
# Test integración: Sheriff + State
# ============================================================================

def test_sheriff_validates_state_completitud():
    sh = Sheriff()
    state = WorkflowState(input_data={"objetivo": "x"})
    state.current_node = "L1"
    v = sh.validate({"status": "ok", "required_fields": ["status"]},
                    "completitud", state)
    assert v.verdict == Verdict.GO


def test_sheriff_repairs_ok_fail():
    sh = Sheriff()
    state = WorkflowState(input_data={"objetivo": "x"})
    state.current_node = "L6"
    state.repair_counts["L6"] = 3
    v = sh.validate({"status": "ok"}, "repairs_ok", state, node_repair_max=2)
    assert v.verdict == Verdict.NO_GO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
