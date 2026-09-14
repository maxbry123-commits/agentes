from runtime.src.core.code_task_graph import CodeTask, TaskContractError, compile_task_graph
from runtime.src.core.dag_engine import DAGEngine


def test_director_and_generated_tasks_are_separate_and_topological():
    graph = compile_task_graph([
        CodeTask("D-001", "director", "audit_file", "auditor", priority=10),
        CodeTask("G-001", "generated", "extract_architecture", "architect", depends_on=["D-001"], priority=20),
        CodeTask("G-002", "generated", "generate_code", "coder", depends_on=["G-001"], priority=30),
    ])
    assert graph["director_tasks"] == ["D-001"]
    assert graph["generated_tasks"] == ["G-001", "G-002"]
    assert DAGEngine().topological_order(graph) == ["D-001", "G-001", "G-002"]


def test_missing_dependency_fails_closed():
    try:
        compile_task_graph([CodeTask("G-001", "generated", "x", "coder", depends_on=["MISSING"])])
    except TaskContractError:
        return
    raise AssertionError("missing dependency must fail closed")


def test_cycle_is_rejected_by_existing_dag_engine():
    graph = compile_task_graph([
        CodeTask("A", "generated", "a", "coder", depends_on=["B"]),
        CodeTask("B", "generated", "b", "coder", depends_on=["A"]),
    ])
    assert DAGEngine().detect_cycle(graph)
