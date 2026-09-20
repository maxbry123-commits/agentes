from typing import Any

from workflow_core.dag import DAGDefinition
from workflow_core.policies import WorkflowPolicy
from workflow_core.sheriff import DeterministicSheriff, SheriffDecision


def run_sheriff_gate(
    dag: DAGDefinition,
    context: dict[str, Any],
    policy: WorkflowPolicy,
) -> SheriffDecision:
    """Valida el DAG contra política antes de cualquier ejecución."""
    sheriff = DeterministicSheriff(policy)
    return sheriff.inspect(dag, context)
