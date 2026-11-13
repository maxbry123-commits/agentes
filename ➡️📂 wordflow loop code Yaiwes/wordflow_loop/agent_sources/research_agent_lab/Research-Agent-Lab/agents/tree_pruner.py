from __future__ import annotations

from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState

PRUNEABLE_STATUSES = {"pending", "max_depth_reached", "blocked_max_active"}

PROTECTED_STATUSES = {"active", "smoke_passed", "selected"}


class TreePrunerAgent(Agent):
    """Prunes dead-end nodes from the experiment tree.

    Removes nodes that are at or beyond max_depth with no results and a
    pruneable status.  Recursively removes ancestor nodes whose entire
    subtree has been pruned.
    """

    name = "tree_pruner"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        tree = state.values.get("experiment_tree")

        if not isinstance(tree, dict):
            return AgentResult(notes=["tree_pruner: no tree, skipping"])

        nodes: list[dict[str, Any]] = tree.get("nodes") or []
        if not nodes:
            return AgentResult(notes=["tree_pruner: no tree, skipping"])

        max_depth = tree.get("max_depth", 2)

        # Step 1 - mark direct dead nodes
        to_prune: set[str] = set()
        for node in nodes:
            if self._should_prune(node, max_depth):
                to_prune.add(node["node_id"])

        # Step 2 - recursive propagation up the tree
        changed = True
        while changed:
            changed = False
            for node in nodes:
                nid = node["node_id"]
                if nid in to_prune:
                    continue
                if nid == tree.get("root_id"):
                    continue
                if node.get("result"):
                    continue
                if node.get("status") not in {"branched", "max_depth_reached", "blocked_max_active"}:
                    continue
                children = node.get("children_ids") or []
                if children and all(cid in to_prune for cid in children):
                    to_prune.add(nid)
                    changed = True

        # Step 3 - remove pruned nodes
        surviving: list[dict[str, Any]] = [n for n in nodes if n["node_id"] not in to_prune]

        # Step 4 - update children_ids on surviving nodes
        pruned_set = to_prune
        for node in surviving:
            old_children = node.get("children_ids") or []
            node["children_ids"] = [cid for cid in old_children if cid not in pruned_set]

        tree["nodes"] = surviving
        state.values["experiment_tree"] = tree

        count = len(to_prune)
        return AgentResult(notes=[f"tree_pruner: pruned {count} node(s)"])

    # -- internal -------------------------------------------------------------

    @staticmethod
    def _should_prune(node: dict[str, Any], max_depth: int) -> bool:
        """Return True if *node* should be considered for pruning."""
        status = node.get("status", "")
        if status in PROTECTED_STATUSES:
            return False
        if node.get("result"):
            return False
        if status not in PRUNEABLE_STATUSES:
            return False
        depth = node.get("depth", 0)
        if depth < max_depth:
            return False
        return True
