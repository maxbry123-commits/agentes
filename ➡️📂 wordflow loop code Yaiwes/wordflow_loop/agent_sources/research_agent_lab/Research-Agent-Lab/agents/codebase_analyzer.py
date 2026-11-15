from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from tools.codebase_analyzer import CodebaseAnalyzer


class CodebaseAnalyzerAgent(Agent):
    name = "codebase_analyzer"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        repo_path = state.topic.codebase.get("repo_path")
        if not repo_path:
            return AgentResult(notes=["skipped codebase analysis; repo_path is not configured"])

        analyzer = CodebaseAnalyzer()
        report = analyzer.analyze(state.topic)
        context.artifact_store.save_json(state.run_id, "codebase_reports", report.report_id, report)
        context.artifact_store.save_text(
            state.run_id,
            "reports",
            "codebase_report",
            analyzer.to_markdown(report),
        )
        state.values["codebase_report"] = asdict(report)
        return AgentResult(
            notes=[f"analyzed codebase at {report.repository_path}"],
            artifacts={"codebase_reports": [report.report_id], "reports": ["codebase_report"]},
            values={"codebase_report_id": report.report_id},
        )
