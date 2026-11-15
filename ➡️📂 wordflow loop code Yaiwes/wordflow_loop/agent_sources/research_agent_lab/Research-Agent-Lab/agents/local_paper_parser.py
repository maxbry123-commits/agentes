from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from tools.local_pdf_parser import LocalPdfParser


class LocalPaperParserAgent(Agent):
    name = "local_paper_parser"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        literature = state.topic.metadata.get("literature", {})
        parser = LocalPdfParser(
            max_pages=int(literature.get("max_parse_pages", 8)),
            max_chars=int(literature.get("max_parse_chars", 12000)),
            chunk_chars=int(literature.get("chunk_chars", 1800)),
        )
        selected = [
            paper
            for paper in state.values.get("selected_papers", [])
            if paper.get("source") == "local_paper"
        ]
        parsed_items = [parser.parse(paper) for paper in selected]

        parsed_ids: list[str] = []
        chunk_ids: list[str] = []
        for parsed in parsed_items:
            context.artifact_store.save_json(
                state.run_id, "parsed_papers", parsed.parsed_paper_id, parsed
            )
            parsed_ids.append(parsed.parsed_paper_id)
            for chunk in parsed.chunks:
                context.artifact_store.save_json(state.run_id, "paper_chunks", chunk.chunk_id, chunk)
                chunk_ids.append(chunk.chunk_id)

        state.values["parsed_papers"] = [asdict(item) for item in parsed_items]
        parsed_count = sum(1 for item in parsed_items if item.status == "parsed")
        return AgentResult(
            notes=[f"parsed {parsed_count}/{len(parsed_items)} selected local papers"],
            artifacts={"parsed_papers": parsed_ids, "paper_chunks": chunk_ids},
            values={
                "parsed_paper_count": parsed_count,
                "paper_chunk_count": len(chunk_ids),
            },
        )
