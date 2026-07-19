"""
test_dsl.py — Test del DSL Runtime.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.dsl import DSLRuntime, run_dsl, SimpleYAML, LoopStatus


def test_simple_yaml_basic():
    yaml = """
name: test
version: 1
count: 42
flag: true
    """
    d = SimpleYAML.parse(yaml)
    assert d["name"] == "test"
    assert d["version"] == 1
    assert d["count"] == 42
    assert d["flag"] is True
    return "PASS"


def test_simple_yaml_nested():
    yaml = """
orchestrator:
  max_loops: 100
  providers:
    mavis:
      model: mavis/x
    cerebras:
      model: cerebras/y
    """
    d = SimpleYAML.parse(yaml)
    assert d["orchestrator"]["max_loops"] == 100
    assert d["orchestrator"]["providers"]["mavis"]["model"] == "mavis/x"
    return "PASS"


def test_simple_yaml_list():
    yaml = """---
loops:
  - id: L1
    type: execute
  - id: L2
    type: verify
    """
    d = SimpleYAML.parse(yaml)
    assert len(d["loops"]) == 2
    assert d["loops"][0]["id"] == "L1"
    assert d["loops"][1]["type"] == "verify"
    return "PASS"


def test_dsl_load():
    dsl_path = "dsl_ejemplo.yaml"
    rt = DSLRuntime(dsl_path)
    ok = rt.load()
    assert ok is True
    assert len(rt.loops) > 0
    assert "L1_goal_lock" in rt.loops
    return "PASS"


def test_dsl_validate():
    rt = DSLRuntime("dsl_ejemplo.yaml")
    rt.load()
    errs = rt.validate()
    # el DSL completo no debe tener errores
    return "PASS" if len(errs) == 0 else f"FAIL: {errs}"


def test_dsl_topological_order():
    rt = DSLRuntime("dsl_ejemplo.yaml")
    rt.load()
    order = rt.loop_order
    # L1 debe ir antes que L4
    assert order.index("L1_goal_lock") < order.index("L4_execute")
    assert order.index("L4_execute") < order.index("L5_verify")
    return "PASS"


def test_dsl_run():
    messages = []
    def chat(msg):
        messages.append(msg)
    result = run_dsl("dsl_ejemplo.yaml",
                     user_input={"objetivo": "construir API", "metas": ["pytest 100%"]},
                     chat_callback=chat)
    assert result["status"] == "done"
    assert len(result["completed_loops"]) > 0
    return "PASS"


def test_dsl_chat_callback():
    messages = []
    def chat(msg):
        messages.append(msg)
    run_dsl("dsl_ejemplo.yaml", chat_callback=chat)
    # debe haber al menos un mensaje por loop
    assert len(messages) > 0
    return "PASS"


def test_dsl_no_escalate_on_success():
    """El DSL no debe escalar si todos los loops pasan."""
    result = run_dsl("dsl_ejemplo.yaml",
                     user_input={"objetivo": "x", "metas": []})
    assert result["status"] == "done"
    assert result["escalate_count"] == 0
    return "PASS"


def test_dsl_resolve_references():
    rt = DSLRuntime("dsl_ejemplo.yaml")
    rt.load()
    context = {"user": {"objetivo": "test"}, "state": {}, "orchestrator": {}}
    # inputs de L1 tienen ${user.objetivo}
    l1 = rt.loops["L1_goal_lock"]
    resolved = rt._resolve(l1["inputs"], context)
    assert "test" in str(resolved["objetivo"])
    return "PASS"


if __name__ == "__main__":
    tests = [
        test_simple_yaml_basic,
        test_simple_yaml_nested,
        test_simple_yaml_list,
        test_dsl_load,
        test_dsl_validate,
        test_dsl_topological_order,
        test_dsl_run,
        test_dsl_chat_callback,
        test_dsl_no_escalate_on_success,
        test_dsl_resolve_references,
    ]
    passed = 0
    for t in tests:
        try:
            r = t()
            if r == "PASS":
                passed += 1
                print(f"  OK  {t.__name__}")
            else:
                print(f"  FAIL {t.__name__}: {r}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
    print(f"\n  {passed}/{len(tests)} tests pasaron")
