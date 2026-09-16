from __future__ import annotations

from ..contracts import LayerResult, NodeContract
from ..ledger import verify_ledger


def check(node: NodeContract, result: LayerResult, ledger: list[dict]) -> list[str]:
    errors: list[str] = []
    if not verify_ledger(ledger):
        errors.append("ledger_integrity_failure")
    if result.actions and node.mutation is False:
        mutation_like = {"write", "move", "copy", "delete", "commit", "dispatch_action"}
        if mutation_like & set(result.actions):
            errors.append("mutation_action_on_readonly_node")
    return errors
