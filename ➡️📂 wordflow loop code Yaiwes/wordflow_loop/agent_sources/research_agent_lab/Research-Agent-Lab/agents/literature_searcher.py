from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from memory.memory_policy import memory_scope_for_topic
from schemas.paper import Paper
from tools.reference_seed_builder import build_reference_search_seeds


class LiteratureSearchAgent(Agent):
    name = "literature_search"

    def __init__(self, lit_memory_store: object = None):
        super().__init__()
        self.lit_memory_store = lit_memory_store

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        max_papers = int(context.settings.get("max_papers", 8))
        papers: list[Paper] = []
        local_papers = state.values.get("local_papers", [])

        if local_papers:
            local_limit = max_papers
            if context.settings.get("enable_reference_expansion"):
                ref_reserve = int(context.settings.get("max_reference_seeds", 4) or 4)
                local_limit = max(1, max_papers - ref_reserve)
            papers = [Paper(**paper) for paper in local_papers[:local_limit]]

        if not papers and context.tool_registry and context.tool_registry.has("arxiv"):
            for keyword in state.topic.keywords()[:max_papers]:
                output = context.tool_registry.call("arxiv", keyword, max_results=1)
                papers.extend(item for item in output.items if isinstance(item, Paper))
                if len(papers) >= max_papers:
                    break

        reference_seed_papers: list[Paper] = []
        reference_seed_ids: list[str] = []
        if context.settings.get("enable_reference_expansion"):
            reference_seed_papers, reference_seed_ids = self._reference_seed_papers(
                state, context, max_papers
            )

        if reference_seed_papers:
            existing_titles = {p.title.lower() for p in papers}
            for paper in reference_seed_papers:
                if paper.title.lower() in existing_titles:
                    continue
                papers.append(paper)
                existing_titles.add(paper.title.lower())
                if len(papers) >= max_papers:
                    break

        if not papers:
            papers = self._offline_seed_papers(state, max_papers)

        artifact_ids: list[str] = []
        for paper in papers[:max_papers]:
            context.artifact_store.save_json(state.run_id, "papers", paper.paper_id, paper)
            artifact_ids.append(paper.paper_id)

        state.values["papers"] = [asdict(paper) for paper in papers[:max_papers]]
        artifacts = {"papers": artifact_ids}
        if reference_seed_ids:
            artifacts["reference_search_seeds"] = reference_seed_ids
        return AgentResult(
            notes=[f"collected {len(artifact_ids)} paper records"],
            artifacts=artifacts,
            values={
                "paper_count": len(artifact_ids),
                "reference_search_seed_count": len(reference_seed_ids),
            },
        )

    def _offline_seed_papers(self, state: ResearchState, max_papers: int) -> list[Paper]:
        keywords = state.topic.keywords() or [state.topic.topic_name]
        goal = state.topic.research_goal.get("short") or state.topic.research_goal.get("long") or ""
        papers: list[Paper] = []
        for index, keyword in enumerate(keywords[:max_papers], start=1):
            papers.append(
                Paper(
                    title=f"Search seed {index}: {keyword}",
                    abstract=(
                        f"Offline seed generated from topic keyword '{keyword}'. "
                        f"Research goal: {goal}"
                    ),
                    keywords=[keyword],
                    source="offline_seed",
                )
            )
        return papers

    def _reference_seed_papers(
        self, state: ResearchState, context: AgentContext, max_papers: int
    ) -> tuple[list[Paper], list[str]]:
        if self.lit_memory_store is None:
            return [], []
        max_reference_seeds = int(context.settings.get("max_reference_seeds", 4) or 4)
        scope = memory_scope_for_topic(state.topic.topic_name)
        references = self.lit_memory_store.retrieve_references(
            scope, min_score=0.0, limit=max_reference_seeds * 2
        )
        seeds = build_reference_search_seeds(
            references,
            topic_keywords=state.topic.keywords(),
            max_seeds=max_reference_seeds,
        )
        papers: list[Paper] = []
        artifact_ids: list[str] = []
        for index, seed in enumerate(seeds, start=1):
            query = seed["query"]
            if context.tool_registry and context.tool_registry.has("arxiv"):
                output = context.tool_registry.call("arxiv", query, max_results=1)
                for item in output.items:
                    if isinstance(item, Paper):
                        papers.append(item)
                        artifact_ids.append(seed.get("source_ref_id") or f"reference_seed_{index}")
                        break
            else:
                paper = Paper(
                    title=f"Reference seed {index}: {query}",
                    abstract=(
                        "Offline reference-network seed generated from extracted references. "
                        f"source_ref_id={seed.get('source_ref_id', '')}; "
                        f"score={seed.get('relevance_score', 0.0)}"
                    ),
                    keywords=[query],
                    source="reference_seed",
                )
                papers.append(paper)
                artifact_ids.append(seed.get("source_ref_id") or paper.paper_id)
            if len(papers) >= max_papers:
                break
        state.values["reference_search_seeds"] = seeds
        return papers, artifact_ids
