from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState


class SynthesisAgent(Agent):
    name = "synthesis"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        cards = state.values.get("method_cards", [])
        metrics = ", ".join(state.topic.experiment_metrics) or "topic-specific metrics"
        report = [
            f"# Synthesis Report: {state.topic.topic_name}",
            "",
            "## Scope",
            state.topic.research_goal.get("short", state.topic.research_goal.get("long", "")),
            "",
            "## Current Evidence Level",
            "This V1 run used offline seed papers unless online tools were enabled.",
            "Strong conclusions require full-paper parsing and evidence confirmation.",
            "",
            "## Method Themes",
        ]
        for card in cards[:8]:
            report.append(f"- {card['task']}: {', '.join(card.get('input_modalities', []))}")
        report.extend(
            [
                "",
                "## Evaluation Metrics",
                metrics,
            ]
        )
        text = "\n".join(report).strip() + "\n"
        context.artifact_store.save_text(state.run_id, "reports", "synthesis_report", text)
        state.values["synthesis_report"] = text
        return AgentResult(
            notes=["wrote synthesis report"],
            artifacts={"reports": ["synthesis_report"]},
        )
