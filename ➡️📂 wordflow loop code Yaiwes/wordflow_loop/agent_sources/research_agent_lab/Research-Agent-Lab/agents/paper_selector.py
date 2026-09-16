from __future__ import annotations

import sys

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState


class PaperSelectionAgent(Agent):
    """Interactive terminal prompt for selecting papers after triage, before parsing."""

    name = "paper_selection"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        papers = state.values.get("selected_papers", [])
        if not papers:
            return AgentResult(notes=["no papers to select"])

        if not sys.stdin.isatty():
            state.values["selected_paper_count"] = len(papers)
            return AgentResult(
                notes=[f"non-interactive: keeping all {len(papers)} papers"],
                values={"selected_paper_count": len(papers)},
            )

        print(f"\n=== 候选论文 ({len(papers)} 篇) ===")
        for i, p in enumerate(papers, 1):
            score = p.get("relevance_score", 0)
            decision = p.get("triage_decision", "read")
            title = (p.get("title") or "")[:100]
            authors = p.get("authors", "")
            if isinstance(authors, list):
                authors = ", ".join(str(a) for a in authors[:3])
            year = p.get("year", "")
            url = p.get("url", "")
            local = p.get("local_path") or p.get("pdf_path", "")
            abstract = (p.get("abstract") or "")[:200]

            print(f"[{i}] ★{score:.2f} {decision} | {title}")
            print(f"    {authors}, {year}")
            if url:
                print(f"    \U0001f517 {url}")
            elif local:
                print(f"    \U0001f4c1 {local}")
            print(f"    {abstract}")
            print()

        choice = input("输入要保留的论文编号（逗号分隔），回车全选，输入 none 跳过全部：").strip()
        if choice.lower() == "none":
            state.values["selected_papers"] = []
        elif choice:
            indices = {int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()}
            state.values["selected_papers"] = [p for i, p in enumerate(papers) if i in indices]

        state.values["selected_paper_count"] = len(state.values["selected_papers"])
        return AgentResult(
            notes=[f"user selected {len(state.values['selected_papers'])}/{len(papers)} papers"],
            values={"selected_paper_count": len(state.values["selected_papers"])},
        )
