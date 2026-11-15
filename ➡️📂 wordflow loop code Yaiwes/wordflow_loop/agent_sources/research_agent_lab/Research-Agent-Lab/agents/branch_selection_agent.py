from __future__ import annotations

from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from memory.memory_policy import memory_scope_for_topic


class BranchSelectionAgent(Agent):
    """Selects the highest-scoring pending experiment tree node for the next run.

    Scoring is rule-based (no LLM): -depth * 0.3 + risk_bonus + scope_match_bonus.
    Lower depth and lower-risk scopes are preferred.
    """

    name = "branch_selection"

    def __init__(self, lit_memory_store: object = None):
        super().__init__()
        self._store = lit_memory_store

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        tree = state.values.get("experiment_tree")

        # If no tree in state, try loading persisted tree from cross-run memory
        if not isinstance(tree, dict):
            store = self._store or getattr(context, "lit_memory_store", None)
            if store is not None:
                scope = memory_scope_for_topic(state.topic.topic_name)
                loaded = store.load_branch(scope)
                if isinstance(loaded, dict):
                    tree = loaded
                    state.values["experiment_tree"] = tree

        if not isinstance(tree, dict):
            return AgentResult(notes=["no experiment_tree in state, nothing to select"])

        max_depth = tree.get("max_depth", 2)
        nodes: list[dict[str, Any]] = tree.get("nodes", []) or []
        pending = [
            n for n in nodes
            if n.get("status") == "pending" and n.get("depth", 0) < max_depth
        ]

        if not pending:
            return AgentResult(notes=["no pending branches to select"])

        allowed = state.topic.allowed_auto_edit()
        scored = [(_score_node(n, allowed), n) for n in pending]
        scored.sort(key=lambda pair: (-pair[0], pair[1].get("depth", 0)))

        max_parallel = int(context.settings.get("max_parallel_branches", 1))
        max_parallel = max(1, max_parallel)

        selected_nodes: list[tuple[float, dict[str, Any]]] = []
        for i, (score, node) in enumerate(scored):
            if i >= max_parallel:
                break
            node["status"] = "selected"
            selected_nodes.append((score, node))

        state.values["experiment_tree"] = tree
        state.values["selected_branch_nodes"] = [dict(n) for _, n in selected_nodes]
        state.values["selected_branch_node"] = dict(selected_nodes[0][1])

        notes = []
        for score, n in selected_nodes:
            notes.append(f"selected branch node {n['node_id']} (score={score:.2f})")
            notes.append(f"hypothesis: {n.get('hypothesis', '')[:80]}")

        return AgentResult(
            notes=notes,
            values={
                "experiment_tree": tree,
                "selected_branch_nodes": [dict(n) for _, n in selected_nodes],
                "selected_branch_node": dict(selected_nodes[0][1]),
                "selected_branch_score": selected_nodes[0][0],
            },
        )


def _score_node(node: dict[str, Any], allowed: list[str]) -> float:
    depth = node.get("depth", 0)
    patch_scope = (node.get("patch_scope") or "").lower()

    # Lower depth is preferred (shallower = less risk)
    score = -depth * 0.3

    # Risk bonus: lower-risk scopes get higher scores
    if "data loader" in patch_scope or "dataloader" in patch_scope:
        score += 0.3
    elif "fusion" in patch_scope or "model" in patch_scope:
        score += 0.1
    elif "config" in patch_scope or "cfg" in patch_scope:
        score += 0.2

    # Scope match bonus: patch_scope keywords match allowed files
    for pattern in allowed:
        pattern_lower = pattern.lower()
        for token in patch_scope.replace("/", " ").replace("*", "").split():
            if len(token) >= 3 and token in pattern_lower:
                score += 0.5
                break

    return score
