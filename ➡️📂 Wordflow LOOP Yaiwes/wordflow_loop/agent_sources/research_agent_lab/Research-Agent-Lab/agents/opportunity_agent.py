from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.opportunity import ResearchOpportunity


class OpportunityAgent(Agent):
    name = "opportunity_agent"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        priorities = state.topic.current_status.get("priority", [])
        priority_text = "; ".join(str(item) for item in priorities) or "improve the target task"
        primary_area = state.topic.domain.get("primary_area", state.topic.topic_name)
        codebase_report = state.values.get("codebase_report", {})
        integration_points = codebase_report.get("integration_points", [])
        strategy = state.topic.current_status.get(
            "first_strategy",
            "Start with the smallest baseline-compatible feature or conditioning pathway.",
        )
        if integration_points:
            strategy = strategy + " Integration points: " + " ".join(integration_points[:3])

        data_req = str(state.topic.current_status.get("data_requirement", "existing data"))
        historical = state.values.get("historical_method_cards", []) or []
        if historical:
            ideas: list[str] = []
            for card in historical[:5]:
                for idea in card.get("reusable_ideas_for_current_topic", []) or []:
                    if idea not in ideas:
                        ideas.append(idea)
            if ideas:
                strategy = strategy + " Historical insights: " + "; ".join(ideas[:3])
            hist_datasets: list[str] = []
            for card in historical[:5]:
                for ds in card.get("datasets", []) or []:
                    if ds not in hist_datasets:
                        hist_datasets.append(ds)
            if hist_datasets:
                data_req = data_req + " (historical: " + ", ".join(hist_datasets[:3]) + ")"

        opportunity = ResearchOpportunity(
            title=f"Evidence-guided first experiment for {primary_area}",
            hypothesis=(
                f"A small, controlled modification aligned with topic priorities can test whether "
                f"the research direction is feasible: {priority_text}."
            ),
            based_on_papers=[
                paper["paper_id"] for paper in state.values.get("selected_papers", [])[:5]
            ],
            technical_strategy=strategy,
            expected_benefit="Produce a measurable baseline delta before larger architecture changes.",
            novelty_level="low",
            implementation_difficulty="medium",
            data_requirement=data_req,
            risk=[
                "offline literature pass may miss stronger related work",
                "experiment should be reviewed before code changes",
            ],
            recommended_priority=1,
        )
        context.artifact_store.save_json(
            state.run_id, "opportunities", opportunity.opportunity_id, opportunity
        )
        state.values["opportunities"] = [asdict(opportunity)]
        return AgentResult(
            notes=["generated first research opportunity"],
            artifacts={"opportunities": [opportunity.opportunity_id]},
            values={"opportunity_count": 1},
        )
