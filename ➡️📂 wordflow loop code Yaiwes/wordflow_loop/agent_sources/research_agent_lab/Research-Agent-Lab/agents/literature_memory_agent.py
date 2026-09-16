from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from memory.memory_policy import memory_scope_for_topic


class LiteratureMemoryPersistenceAgent(Agent):
    """Persists current-run papers, evidence, and method cards to cross-run memory."""

    name = "literature_memory_persistence"

    def __init__(self, lit_memory_store: LiteratureMemoryStore | None = None):
        super().__init__()
        self._store = lit_memory_store

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        store = self._store or getattr(context, "lit_memory_store", None)
        if store is None:
            return AgentResult(notes=["skipped: no LiteratureMemoryStore available"])

        scope = memory_scope_for_topic(state.topic.topic_name)
        state_values = _to_state_values(state)
        state_values = _filter_by_selected(state_values)
        count = store.write_run_artifacts(state_values, scope)

        # Export Mermaid tree visualization
        tree = state.values.get("experiment_tree")
        if isinstance(tree, dict) and tree.get("nodes"):
            from tools.tree_visualizer import export_mermaid
            mermaid = export_mermaid(tree)
            context.artifact_store.save_text(
                state.run_id,
                "experiment_trees",
                tree.get("branch_id", "unknown"),
                mermaid,
                suffix=".mmd",
            )

        return AgentResult(
            notes=[f"persisted {count} artifacts to cross-run literature memory (scope={scope})"],
        )


def _filter_by_selected(state_values: dict) -> dict:
    selected = state_values.get("selected_papers", [])
    selected_ids = {p.get("paper_id", "") for p in selected if p.get("paper_id")}
    if not selected_ids:
        return state_values

    filtered = dict(state_values)
    filtered["selected_papers"] = selected

    filtered["parsed_papers"] = {
        pid: v for pid, v in state_values.get("parsed_papers", {}).items()
        if pid in selected_ids
    }

    filtered["checked_evidence"] = [
        e for e in state_values.get("checked_evidence", [])
        if e.get("paper_id", "") in selected_ids
    ]

    filtered["method_cards"] = [
        m for m in state_values.get("method_cards", [])
        if m.get("paper_id", "") in selected_ids
    ]

    filtered["extracted_references"] = [
        r for r in state_values.get("extracted_references", [])
        if r.get("source_paper_id", "") in selected_ids
    ]

    return filtered


def _to_state_values(state: ResearchState) -> dict:
    """Build a flat dict from state for write_run_artifacts, merging key sources."""
    values: dict = dict(state.values)

    if "selected_papers" not in values:
        values["selected_papers"] = state.artifacts.get("selected_papers", []) or []

    # parsed_papers in state.values is often a dict keyed by paper_id
    if "parsed_papers" not in values:
        values["parsed_papers"] = {}

    if "checked_evidence" not in values:
        values["checked_evidence"] = []

    if "method_cards" not in values:
        values["method_cards"] = []

    if "experiment_tree" not in values:
        values["experiment_tree"] = None

    return values
