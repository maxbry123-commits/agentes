from __future__ import annotations

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from memory.memory_policy import memory_scope_for_topic
from tools.model_router import ModelRouter


class ResearchManagerAgent(Agent):
    name = "research_manager"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        scope = memory_scope_for_topic(state.topic.topic_name)
        brief_id = "research_brief"
        brief = {
            "topic_name": state.topic.topic_name,
            "goal": state.topic.research_goal,
            "domain": state.topic.domain,
            "metrics": state.topic.experiment_metrics,
            "keywords": state.topic.keywords(),
            "model_routing": ModelRouter(state.topic).summary(),
            "literature": state.topic.metadata.get("literature", {}),
            "human_review_policy": "human approval required before external repo edits",
        }
        context.artifact_store.save_json(state.run_id, "briefs", brief_id, brief)
        context.memory_store.write(scope, "project_memory", brief)
        return AgentResult(
            notes=[f"prepared research brief for {state.topic.topic_name}"],
            artifacts={"briefs": [brief_id]},
            values={"memory_scope": scope},
        )
