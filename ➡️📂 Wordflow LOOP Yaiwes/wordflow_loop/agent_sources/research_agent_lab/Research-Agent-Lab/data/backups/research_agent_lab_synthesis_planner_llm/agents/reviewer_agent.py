from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.review_result import ReviewResult


class ReviewerAgent(Agent):
    name = "reviewer_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        findings: list[str] = []
        required_actions: list[str] = []
        residual_risk: list[str] = []

        if state.values.get("unsupported_evidence_count", 0):
            findings.append("Some evidence records were unsupported.")
            required_actions.append("Re-run with full text parsing or remove unsupported claims.")

        if state.values.get("developer_mode") == "plan_only":
            findings.append("Developer agent produced a scoped plan only; no external code was edited.")
            required_actions.append("Confirm target repository and allowed paths before implementation.")
        elif state.values.get("developer_mode") == "explore_enabled":
            findings.append("Developer agent is allowed to explore the copied project, but this workflow run only created a task.")

        if state.values.get("paper_count", 0) and all(
            paper.get("source") == "offline_seed" for paper in state.values.get("papers", [])
        ):
            residual_risk.append("Literature results are offline seeds, not real paper retrieval.")
            required_actions.append("Enable online arXiv or Semantic Scholar retrieval for real evidence.")

        status = "needs_human_review" if required_actions else "pass"
        review = ReviewResult(
            status=status,
            findings=findings,
            required_actions=required_actions,
            residual_risk=residual_risk,
        )
        context.artifact_store.save_json(state.run_id, "reviews", review.review_id, review)
        state.values["review_status"] = status
        state.values["review"] = asdict(review)
        return AgentResult(
            notes=[f"review completed with status={status}"],
            artifacts={"reviews": [review.review_id]},
            values={"review_status": status},
        )
