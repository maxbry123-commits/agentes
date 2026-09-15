from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from memory.memory_policy import memory_scope_for_topic


class MethodCardRetrieverAgent(Agent):
    """Retrieves historical method cards from cross-run memory, deduplicates against
    current-run papers, and writes them to state for downstream agents."""

    name = "method_card_retriever"

    def __init__(self, lit_memory_store: LiteratureMemoryStore | None = None):
        super().__init__()
        self._store = lit_memory_store

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        store = self._store or getattr(context, "lit_memory_store", None)
        if store is None:
            state.values["historical_method_cards"] = []
            return AgentResult(notes=["skipped: no LiteratureMemoryStore available"])

        scope = memory_scope_for_topic(state.topic.topic_name)
        current_paper_ids = self._current_paper_ids(state)

        search_params = self._build_search(state)
        cards = store.retrieve_method_cards(scope, **search_params)

        historical = [
            c for c in cards
            if c.get("paper_id") not in current_paper_ids
        ]

        state.values["historical_method_cards"] = historical
        state.values["historical_method_card_count"] = len(historical)

        notes = [f"retrieved {len(historical)} historical method cards (scope={scope})"]
        return AgentResult(
            notes=notes,
            values={
                "historical_method_cards": historical,
                "historical_method_card_count": len(historical),
            },
        )

    def _build_search(self, state: ResearchState) -> dict:
        topic = state.topic
        return {
            "task": topic.domain.get("primary_area", ""),
            "dataset": self._first(topic.current_status.get("datasets", [])),
            "metric": self._first(topic.experiment_metrics),
            "topic_keywords": topic.keywords(),
            "limit": 10,
        }

    def _current_paper_ids(self, state: ResearchState) -> set[str]:
        ids: set[str] = set()
        for paper in (state.values.get("selected_papers") or []):
            if isinstance(paper, dict) and paper.get("paper_id"):
                ids.add(paper["paper_id"])
        for paper in (state.values.get("papers") or []):
            if isinstance(paper, dict) and paper.get("paper_id"):
                ids.add(paper["paper_id"])
        return ids

    @staticmethod
    def _first(items: list[str]) -> str | None:
        return items[0] if items else None
