import json
from pathlib import Path

from runtime.src.core.dag_engine import DAGEngine
from runtime.src.core.parallel_scheduler import TaskEnvelope, plan_tasks


ROOT = Path(__file__).parents[2]
MATRIX_PATH = ROOT / "wordflow_loop" / "contracts" / "planning-stack-g029-matrix.json"
EXPECTED_EXTERNAL = {
    "dagster", "prefect", "argo_workflows", "inngest", "trigger_dev", "restate", "apache_airflow"
}


def load_matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_matrix_has_one_decision_per_required_candidate():
    matrix = load_matrix()
    assert matrix["schema"] == "yaiwes.planning-stack-matrix/v1"
    rows = matrix["candidates"]
    by_id = {row["id"]: row for row in rows}
    assert len(by_id) == len(rows) == 9
    assert set(by_id) == EXPECTED_EXTERNAL | {"dag_engine", "mavis_parallel_scheduler"}
    assert all(row["decision"] in {"ADOPT", "ADAPT", "REJECT"} for row in rows)


def test_local_stack_is_selected_and_no_component_is_invented():
    matrix = load_matrix()
    assert matrix["decision"] == "REUSE_LOCAL_STACK"
    assert matrix["selected_stack"] == ["dag_engine", "mavis_parallel_scheduler"]
    assert matrix["uncovered_planning_capabilities"] == []
    assert matrix["new_component_required"] is False


def test_external_orchestrators_are_rejected_without_concrete_gap():
    rows = {row["id"]: row for row in load_matrix()["candidates"]}
    for candidate_id in EXPECTED_EXTERNAL:
        row = rows[candidate_id]
        assert row["decision"] == "REJECT"
        assert row["concrete_gap"] is None
        assert row["source"].startswith("https://")
        assert row["reason"]
        assert row["reconsider_if"]


def test_selected_stack_executes_dependency_and_priority_plan():
    manifest = {
        "nodes": {
            "start": {"depends_on": []},
            "slow": {"depends_on": ["start"]},
            "urgent": {"depends_on": ["start"]},
            "finish": {"depends_on": ["slow", "urgent"]},
        }
    }
    assert DAGEngine().topological_order(manifest) == ["start", "slow", "urgent", "finish"]
    plan = plan_tasks(
        [
            TaskEnvelope("start", 1, "k-start"),
            TaskEnvelope("slow", 9, "k-slow", ("start",)),
            TaskEnvelope("urgent", 1, "k-urgent", ("start",)),
            TaskEnvelope("finish", 1, "k-finish", ("slow", "urgent")),
        ],
        max_concurrency=2,
    )
    assert plan.batches == (("start",), ("urgent", "slow"), ("finish",))


def test_matrix_sources_are_readable_local_or_official_https():
    for row in load_matrix()["candidates"]:
        source = row["source"]
        if source.startswith("https://"):
            assert source.split("/", 3)[2]
        else:
            assert (ROOT / source).is_file(), source
