from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from tools.local_paper_library import LocalPaperLibrary


class LocalPaperLibraryAgent(Agent):
    name = "local_paper_library"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        papers = LocalPaperLibrary().scan(state.topic)
        artifact_ids: list[str] = []
        for paper in papers:
            context.artifact_store.save_json(state.run_id, "local_papers", paper.paper_id, paper)
            artifact_ids.append(paper.paper_id)

        state.values["local_papers"] = [asdict(paper) for paper in papers]
        return AgentResult(
            notes=[f"indexed {len(papers)} local papers"],
            artifacts={"local_papers": artifact_ids[:50]},
            values={"local_paper_count": len(papers)},
        )
