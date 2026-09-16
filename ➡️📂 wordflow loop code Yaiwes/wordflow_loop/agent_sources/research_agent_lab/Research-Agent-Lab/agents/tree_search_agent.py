from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.base import new_id
from schemas.experiment_plan import ExperimentPlan
from schemas.experiment_tree import ExperimentBranch, ExperimentNode
from schemas.topic_pack import TopicPack


_MAX_DEPTH = 2
_MAX_ACTIVE = 3

_VARIANT_TEMPLATES = [
    {
        "label": "tweak_conditioning",
        "hypothesis": "Using {conditioning_source} conditioning instead of the current approach may improve {metric_target}.",
        "patch_hint": "Replace the conditioning input source with {conditioning_source}.",
    },
    {
        "label": "simplify_modification",
        "hypothesis": "A minimal change to {scope_target} may achieve the same effect with lower risk.",
        "patch_hint": "Limit changes to {scope_target} only; revert all other modifications.",
    },
    {
        "label": "vary_hyperparameter",
        "hypothesis": "Adjusting {param_name} from {param_low} to {param_high} may yield a clearer signal.",
        "patch_hint": "Change {param_name} to {param_high} in the training config.",
    },
]


class TreeSearchAgent(Agent):
    """Generates 2-3 variant experiment plans when current results are unparsed/failed.
    Uses deferred branching: branch plans are persisted as artifacts for the next run."""

    name = "tree_search"

    def __init__(self, lit_memory_store: object = None):
        super().__init__()
        self._store = lit_memory_store

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plans = state.values.get("experiment_plans", []) or []
        results = state.values.get("experiment_results", []) or []
        decision = state.values.get("experiment_decision") or {}

        existing_tree = state.values.get("experiment_tree")
        if existing_tree and isinstance(existing_tree, dict):
            tree = self._tree_from_dict(existing_tree)
        else:
            tree = ExperimentBranch()

        # Ensure root exists (creates it from plans/results if tree is empty)
        root = self._ensure_root(tree, plans, results, decision)

        # Determine the "current" node: the selected branch node if it was
        # executed this run, otherwise the root.
        current = self._find_selected_node(tree, state)

        # If branches were selected but no experiment results were produced
        # (experiments not enabled), revert ALL selected nodes so they can be
        # reselected next run.
        if not results:
            selected_nodes = self._find_all_selected_nodes(tree, state)
            if selected_nodes:
                for sn in selected_nodes:
                    if sn.status == "selected":
                        sn.status = "pending"
                state.values["experiment_tree"] = asdict(tree)
                context.artifact_store.save_json(
                    state.run_id, "experiment_trees", tree.branch_id, tree
                )
                reverted_ids = [sn.node_id for sn in selected_nodes]
                return AgentResult(
                    notes=[f"tree_search: no experiment results, reverted {len(reverted_ids)} selected node(s) to pending: {reverted_ids}"],
                    values={"experiment_tree": asdict(tree)},
                )

        promote_notes: list[str] = []
        all_notes: list[str] = []
        per_node_decisions = state.values.get("experiment_decisions", {}) or {}

        # If branches were executed, write results and per-node decisions back.
        if results:
            selected_nodes = self._find_all_selected_nodes(tree, state)
            if selected_nodes:
                # Build experiment_id → result map
                results_by_exp: dict[str, dict] = {}
                for r in results:
                    eid = r.get("experiment_id", "")
                    if eid:
                        results_by_exp[eid] = r
                # Assign results and per-node decisions to selected nodes
                for i, sn in enumerate(selected_nodes):
                    eid = sn.experiment_id
                    if eid and eid in results_by_exp:
                        sn.result = results_by_exp[eid]
                    elif i < len(results):
                        sn.result = results[i]
                    # Use per-node decision if available, else fall back to global
                    if eid and eid in per_node_decisions:
                        sn.decision = per_node_decisions[eid]
                    else:
                        sn.decision = decision

                # Process each selected node independently.
                # Pre-calculate available branch slots once — do not recompute
                # mid-loop because each generated child would alter the count.
                active_pending = [n for n in tree.nodes if n.status == "pending" and n.depth < tree.max_depth]
                slots_remaining = tree.max_active_nodes - len(active_pending)
                promoted_in_run = False
                for sn in selected_nodes:
                    if not sn.result:
                        continue

                    result_status = (sn.result.get("status") or "").lower()
                    node_decision = sn.decision or {}
                    decision_action = (node_decision.get("action") or "").lower()

                    if result_status == "passed" and decision_action in {"continue", "hold"}:
                        sn.status = "smoke_passed"
                        all_notes.append(f"node {sn.node_id}: passed → smoke_passed")
                        if not promoted_in_run and sn.node_id != tree.root_id:
                            self._maybe_auto_promote(tree, sn, root, promote_notes)
                            if sn.node_id == tree.root_id:
                                promoted_in_run = True
                    elif result_status in {"unparsed", "failed", "error"} or decision_action in {"investigate", "rollback"}:
                        all_notes.append(f"node {sn.node_id}: {result_status}/{decision_action} → checking branch")
                        if sn.depth >= tree.max_depth:
                            sn.status = "max_depth_reached"
                            all_notes.append(f"node {sn.node_id}: at max depth ({tree.max_depth}), cannot branch")
                        elif slots_remaining <= 0:
                            sn.status = "blocked_max_active"
                            all_notes.append(f"node {sn.node_id}: no branch slots remaining")
                        else:
                            branch_plans = self._generate_branches(sn, state, max_count=1)
                            tree.nodes.extend(branch_plans)
                            sn.children_ids = list(dict.fromkeys(
                                sn.children_ids + [n.node_id for n in branch_plans]
                            ))
                            sn.status = "branched"
                            slots_remaining -= 1
                            all_notes.append(f"node {sn.node_id}: generated 1 branch child")
                    else:
                        all_notes.append(f"node {sn.node_id}: status={result_status} decision={decision_action}, unchanged")

                state.values["experiment_tree"] = asdict(tree)
                context.artifact_store.save_json(
                    state.run_id, "experiment_trees", tree.branch_id, tree
                )
                return AgentResult(
                    notes=all_notes + promote_notes,
                    values={"experiment_tree": asdict(tree)},
                )
            # Fall through: results exist but no selected nodes → use legacy global-decision path

        # Legacy path: no selected nodes, use root and global decision
        if not self._should_branch(decision, results):
            state.values["experiment_tree"] = asdict(tree)
            context.artifact_store.save_json(
                state.run_id, "experiment_trees", tree.branch_id, tree
            )
            return AgentResult(
                notes=["tree_search: no branch needed"] + promote_notes,
                values={"experiment_tree": asdict(tree)},
            )

        if root.depth >= tree.max_depth:
            root.status = "max_depth_reached"
            state.values["experiment_tree"] = asdict(tree)
            context.artifact_store.save_json(
                state.run_id, "experiment_trees", tree.branch_id, tree
            )
            return AgentResult(
                notes=[f"tree_search: root at max depth ({tree.max_depth}), cannot branch"] + promote_notes,
                values={"experiment_tree": asdict(tree)},
            )

        active = [n for n in tree.nodes if n.status == "pending" and n.depth < tree.max_depth]
        remaining = tree.max_active_nodes - len(active)
        if remaining <= 0:
            root.status = "blocked_max_active"
            state.values["experiment_tree"] = asdict(tree)
            context.artifact_store.save_json(
                state.run_id, "experiment_trees", tree.branch_id, tree
            )
            return AgentResult(
                notes=[f"tree_search: max active branches reached ({tree.max_active_nodes})"] + promote_notes,
                values={"experiment_tree": asdict(tree)},
            )

        branch_plans = self._generate_branches(root, state, max_count=remaining)
        tree.nodes.extend(branch_plans)
        root.children_ids = list(dict.fromkeys(
            root.children_ids + [n.node_id for n in branch_plans]
        ))
        root.status = "branched"

        state.values["experiment_tree"] = asdict(tree)
        state.values["experiment_tree_branch_plans"] = [asdict(n) for n in branch_plans]

        context.artifact_store.save_json(
            state.run_id, "experiment_trees", tree.branch_id, tree
        )

        return AgentResult(
            notes=[
                f"tree_search: generated {len(branch_plans)} branch plan(s)",
                f"tree has {len(tree.nodes)} node(s)",
            ] + promote_notes,
            values={
                "experiment_tree": asdict(tree),
                "experiment_tree_branch_count": len(branch_plans),
            },
        )

    # -- internal -------------------------------------------------------------

    def _find_selected_node(
        self, tree: ExperimentBranch, state: ResearchState,
    ) -> ExperimentNode | None:
        """Return the tree node matching ``selected_branch_node``, if any."""
        selected = state.values.get("selected_branch_node")
        if not isinstance(selected, dict):
            return None
        node_id = selected.get("node_id", "")
        for node in tree.nodes:
            if node.node_id == node_id:
                return node
        return None

    def _find_all_selected_nodes(
        self, tree: ExperimentBranch, state: ResearchState,
    ) -> list[ExperimentNode]:
        """Return all tree nodes that are currently selected."""
        selected_list = state.values.get("selected_branch_nodes")
        if isinstance(selected_list, list) and selected_list:
            found: list[ExperimentNode] = []
            for sel in selected_list:
                nid = sel.get("node_id", "") if isinstance(sel, dict) else ""
                for node in tree.nodes:
                    if node.node_id == nid:
                        found.append(node)
                        break
            if found:
                return found
        # Fallback to single
        sn = self._find_selected_node(tree, state)
        return [sn] if sn else []

    def _ensure_root(
        self,
        tree: ExperimentBranch,
        plans: list[dict],
        results: list[dict],
        decision: dict,
    ) -> ExperimentNode:
        if tree.root_id:
            for node in tree.nodes:
                if node.node_id == tree.root_id:
                    return node

        plan = plans[0] if plans else {}
        root = ExperimentNode(
            experiment_id=plan.get("experiment_id", ""),
            hypothesis=plan.get("hypothesis", ""),
            patch_scope=plan.get("modification", ""),
            result=results[0] if results else {},
            decision=decision,
            depth=0,
            status="active",
        )
        tree.root_id = root.node_id
        tree.nodes = [root]
        return root

    def _should_branch(self, decision: dict, results: list[dict]) -> bool:
        action = (decision.get("action") or "").lower()
        if action in {"continue", "hold"}:
            return False
        for r in results:
            status = (r.get("status") or "").lower()
            if status in {"unparsed", "failed", "error"}:
                return True
        return False

    def _any_passed(self, results: list[dict]) -> bool:
        return any((r.get("status") or "").lower() == "passed" for r in results)

    def _generate_branches(
        self,
        root: ExperimentNode,
        state: ResearchState,
        max_count: int = _MAX_ACTIVE,
    ) -> list[ExperimentNode]:
        nodes: list[ExperimentNode] = []
        for i, template in enumerate(_VARIANT_TEMPLATES):
            if len(nodes) >= max_count:
                break
            params = self._resolve_template_params(state, i)
            hypothesis = template["hypothesis"].format(**params)
            patch = template["patch_hint"].format(**params)
            node = ExperimentNode(
                experiment_id=new_id("experiment"),
                parent_id=root.node_id,
                hypothesis=hypothesis,
                patch_scope=patch,
                depth=root.depth + 1,
                status="pending",
            )
            nodes.append(node)
        return nodes

    def _resolve_template_params(self, state: ResearchState, variant_index: int) -> dict[str, str]:
        topic = state.topic
        plan = state.values.get("experiment_plans", [{}])[0] if state.values.get("experiment_plans") else {}
        metrics = topic.experiment_metrics or ["ADE"]
        cond_sources = ["intention", "language", "scene", "social"]
        scopes = ["data loader", "fusion layer", "initializer", "config"]
        return {
            "conditioning_source": cond_sources[variant_index % len(cond_sources)],
            "metric_target": metrics[0] if metrics else "ADE",
            "scope_target": scopes[variant_index % len(scopes)],
            "param_name": "learning_rate" if variant_index % 2 == 0 else "batch_size",
            "param_low": "1e-4" if variant_index % 2 == 0 else "16",
            "param_high": "5e-4" if variant_index % 2 == 0 else "32",
        }

    def _tree_from_dict(self, data: dict) -> ExperimentBranch:
        nodes = [
            ExperimentNode(
                node_id=n.get("node_id", ""),
                experiment_id=n.get("experiment_id", ""),
                parent_id=n.get("parent_id", ""),
                hypothesis=n.get("hypothesis", ""),
                patch_scope=n.get("patch_scope", ""),
                result=n.get("result", {}),
                decision=n.get("decision", {}),
                children_ids=n.get("children_ids", []),
                status=n.get("status", "pending"),
                depth=n.get("depth", 0),
                created_at=n.get("created_at", ""),
            )
            for n in (data.get("nodes") or [])
        ]
        return ExperimentBranch(
            branch_id=data.get("branch_id", ""),
            root_id=data.get("root_id", ""),
            nodes=nodes,
            status=data.get("status", "active"),
            max_depth=data.get("max_depth", _MAX_DEPTH),
            max_active_nodes=data.get("max_active_nodes", _MAX_ACTIVE),
        )

    def _maybe_auto_promote(
        self, tree: ExperimentBranch, current: ExperimentNode,
        root: ExperimentNode, notes: list[str],
    ) -> None:
        """Auto-promote branch node to root if both metrics beat root's."""
        if current is None or current is root:
            return
        if current.node_id == tree.root_id:
            return
        if current.status != "smoke_passed":
            return

        current_metrics = (current.result or {}).get("metrics", {})
        root_metrics = (root.result or {}).get("metrics", {})
        if not current_metrics or not root_metrics:
            return

        # Normalize: look for both case variants
        current_ade = current_metrics.get("ade") or current_metrics.get("ADE")
        current_fde = current_metrics.get("fde") or current_metrics.get("FDE")
        root_ade = root_metrics.get("ade") or root_metrics.get("ADE")
        root_fde = root_metrics.get("fde") or root_metrics.get("FDE")

        if current_ade is None or current_fde is None or root_ade is None or root_fde is None:
            return

        both_better = current_ade < root_ade and current_fde < root_fde
        one_better = current_ade < root_ade or current_fde < root_fde

        if both_better:
            # Auto-promote:
            # 1. Archive old root and make it a child of the new root
            # 2. Move old root's other children (siblings) under new root
            # 3. Recalculate depths from new root
            root.status = "archived"
            tree.root_id = current.node_id
            current.status = "active"
            current.parent_id = ""  # promoted node is now root — no parent
            # Move other root children to new root
            for cid in list(root.children_ids):
                if cid != current.node_id:
                    current.children_ids.append(cid)
                    child = next((n for n in tree.nodes if n.node_id == cid), None)
                    if child:
                        child.parent_id = current.node_id
            # Old root becomes a historical child of the new root
            root.parent_id = current.node_id
            root.children_ids = []
            current.children_ids.append(root.node_id)
            # Recalculate depths
            self._recalc_depths(tree.nodes, tree.root_id, 0)
            notes.append(
                f"auto-promoted node {current.node_id} to root: "
                f"ADE {root_ade:.4f}→{current_ade:.4f}, "
                f"FDE {root_fde:.4f}→{current_fde:.4f}"
            )
        elif one_better:
            notes.append(
                f"borderline: node {current.node_id} has mixed metrics vs root "
                f"(ADE: {root_ade:.4f} vs {current_ade:.4f}, "
                f"FDE: {root_fde:.4f} vs {current_fde:.4f})"
            )

    def _recalc_depths(
        self, nodes: list[ExperimentNode], node_id: str, depth: int,
        visited: set[str] | None = None,
    ) -> None:
        """Recursively recalculate depth for a node and all descendants."""
        if visited is None:
            visited = set()
        if node_id in visited:
            return
        visited.add(node_id)
        node = next((n for n in nodes if n.node_id == node_id), None)
        if node is None:
            return
        node.depth = depth
        for cid in node.children_ids:
            self._recalc_depths(nodes, cid, depth + 1, visited)


def _node_to_plan(node: ExperimentNode, topic: TopicPack, branch_id: str = "") -> ExperimentPlan:
    """Convert a branch ExperimentNode into a full ExperimentPlan."""
    return ExperimentPlan(
        name=f"Branch: {node.hypothesis[:60]}",
        hypothesis=node.hypothesis,
        experiment_id=node.experiment_id,
        modification=node.patch_scope,
        files_to_change=_infer_files(node.patch_scope, topic.allowed_auto_edit()),
        dataset=str(topic.current_status.get("dataset", "")),
        training_config={
            "mode": "smoke-only",
            "epochs": 2,
            "batch_size": "to_confirm",
            "branch_id": branch_id,
            "branch_node_id": node.node_id,
            "parent_node_id": node.parent_id,
            "generated_from_tree_search": True,
        },
        metrics=topic.experiment_metrics,
        ablation_studies=[node.hypothesis],
        acceptance_criteria={"smoke_must_pass": True},
        rollback_plan="branch rollback: revert to parent node config",
    )


def _infer_files(patch_scope: str, allowed: list[str]) -> list[str]:
    """Heuristically match patch_scope text to allowed files."""
    if not allowed:
        return []
    scope_lower = patch_scope.lower()
    keyword_to_glob: list[tuple[str, str]] = [
        ("data loader", "data/"),
        ("dataloader", "data/"),
        ("data", "data/"),
        ("fusion", "models/"),
        ("model", "models/"),
        ("trainer", "trainer/"),
        ("train", "trainer/"),
        ("config", "cfg/"),
        ("cfg", "cfg/"),
        ("visualize", "visualize"),
        ("main", "main_"),
        ("utils", "utils/"),
    ]
    matched: list[str] = []
    for keyword, glob_hint in keyword_to_glob:
        if keyword in scope_lower:
            for pattern in allowed:
                pattern_lower = pattern.lower()
                if glob_hint.lower() in pattern_lower or keyword in pattern_lower:
                    if pattern not in matched:
                        matched.append(pattern)
    if not matched:
        # Conservative fallback: first 2 allowed files
        matched = allowed[:2]
    return matched


class BranchToPlanAgent(Agent):
    """Converts a selected branch node into an ExperimentPlan for execution.

    Reads ``state.values["selected_branch_node"]`` and writes
    ``state.values["experiment_plans"]``. No-op when no node is selected.
    """

    name = "branch_to_plan"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        selected_nodes = state.values.get("selected_branch_nodes")
        if not isinstance(selected_nodes, list) or not selected_nodes:
            # Fallback to legacy single
            selected = state.values.get("selected_branch_node")
            if not isinstance(selected, dict) or not selected.get("node_id"):
                return AgentResult(notes=["branch_to_plan: no selected branch node, skipping"])
            selected_nodes = [selected]

        tree = state.values.get("experiment_tree", {}) or {}
        branch_id = tree.get("branch_id", "") if isinstance(tree, dict) else ""

        all_plans: list[dict] = []
        all_node_ids: list[str] = []
        notes: list[str] = []
        for sel in selected_nodes:
            if not isinstance(sel, dict) or not sel.get("node_id"):
                continue
            node = ExperimentNode(
                node_id=sel.get("node_id", ""),
                experiment_id=sel.get("experiment_id", ""),
                parent_id=sel.get("parent_id", ""),
                hypothesis=sel.get("hypothesis", ""),
                patch_scope=sel.get("patch_scope", ""),
                result=sel.get("result", {}),
                decision=sel.get("decision", {}),
                children_ids=sel.get("children_ids", []),
                status=sel.get("status", "selected"),
                depth=sel.get("depth", 0),
            )
            plan = _node_to_plan(node, state.topic, branch_id=branch_id)
            plan_dict = asdict(plan)
            all_plans.append(plan_dict)
            all_node_ids.append(node.node_id)
            context.artifact_store.save_json(
                state.run_id, "branch_experiment_plans", node.node_id, plan_dict,
            )
            notes.append(f"branch_to_plan: converted node {node.node_id} to experiment plan")
            notes.append(f"hypothesis: {plan.hypothesis[:80]}")

        state.values["experiment_plans"] = all_plans

        return AgentResult(
            notes=notes,
            values={
                "experiment_plans": all_plans,
                "selected_branch_node": selected_nodes[0],
            },
            artifacts={"branch_experiment_plans": all_node_ids},
        )
