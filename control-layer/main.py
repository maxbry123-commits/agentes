"""Entry point mínimo de la Capa de Control.

Flujo: load rules + registry + task → construir DAG → Sheriff gate → report.
No ejecuta agentes ni Temporal. Solo valida y decide.
"""
from pathlib import Path
from typing import Any

from dsl.loader import load_rules, load_registry, load_task
from sheriff.gate import run_sheriff_gate
from workflow_core.contracts import NodeDefinition
from workflow_core.dag import DAGDefinition
from workflow_core.policies import WorkflowPolicy


def build_dag_from_task(task: dict[str, Any]) -> DAGDefinition:
    nodes = []
    for n in task.get("nodes", []):
        nodes.append(
            NodeDefinition(
                node_id=n["id"],
                name=n.get("action", n["id"]),
                role=n.get("role", "architecture"),
                dependencies=tuple(n.get("dependencies", [])),
            )
        )
    return DAGDefinition(
        dag_id=f"dag-{task['task_id']}",
        workflow_id=task["task_id"],
        version=1,
        nodes=tuple(nodes),
    )


def main(config_dir: str | Path = "config") -> dict[str, Any]:
    base = Path(config_dir)
    rules = load_rules(base / "rules.yaml")
    registry = load_registry(base / "registry.json")
    task = load_task(base / "task.example.json")

    policy = WorkflowPolicy(
        allowed_groups=frozenset(registry.get("groups", [])),
        allowed_roles=frozenset(registry.get("roles", [])),
    )

    dag = build_dag_from_task(task)
    decision = run_sheriff_gate(dag, {"group": task.get("group", "backend")}, policy)

    return {
        "task_id": task["task_id"],
        "dsl_version": rules.get("dsl_version"),
        "sheriff_allowed": decision.allowed,
        "reason": decision.reason,
        "violations": list(decision.violations),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(main(), indent=2))
