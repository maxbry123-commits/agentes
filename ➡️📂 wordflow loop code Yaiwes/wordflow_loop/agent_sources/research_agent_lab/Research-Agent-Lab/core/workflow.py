from __future__ import annotations

from dataclasses import dataclass

from core.agent_base import Agent, AgentContext
from core.artifact_store import ArtifactStore
from core.run_logger import RunLogger
from core.state import ResearchState
from schemas.topic_pack import TopicPack
from tools.tool_registry import ToolRegistry

SENSITIVE_SETTING_NAMES = {
    "api_key",
    "apikey",
    "secret",
    "token",
}


def _is_sensitive_setting_key(key: object) -> bool:
    name = str(key).lower()
    return (
        name in SENSITIVE_SETTING_NAMES
        or name.endswith("_api_key")
        or name.endswith("_secret")
        or name.endswith("_token")
        or name.endswith("_access_token")
        or name.endswith("_refresh_token")
        or name.endswith("_auth_token")
    )


def _public_workflow_settings(settings: dict) -> dict:
    public: dict = {}
    for key, value in settings.items():
        if _is_sensitive_setting_key(key):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            public[str(key)] = value
        elif isinstance(value, (list, tuple)):
            public[str(key)] = list(value)
        elif isinstance(value, dict):
            public[str(key)] = {
                str(k): v for k, v in value.items()
                if not _is_sensitive_setting_key(k)
                and (isinstance(v, (str, int, float, bool)) or v is None)
            }
    return public


@dataclass(slots=True)
class Workflow:
    name: str
    agents: list[Agent]
    artifact_store: ArtifactStore
    memory_store: object
    tool_registry: ToolRegistry
    logger: RunLogger
    settings: dict

    def run(self, topic: TopicPack) -> ResearchState:
        state = ResearchState(topic=topic)
        state.values["workflow_settings"] = _public_workflow_settings(self.settings)
        context = AgentContext(
            artifact_store=self.artifact_store,
            memory_store=self.memory_store,
            tool_registry=self.tool_registry,
            settings=self.settings,
        )
        self.logger.write(self.artifact_store.run_dir(state.run_id), "workflow_started", {"name": self.name})

        for agent in self.agents:
            state.stage = agent.name
            self.logger.write(
                self.artifact_store.run_dir(state.run_id),
                "agent_started",
                {"agent": agent.name},
            )
            result = agent.run(state, context)
            state.notes.extend(result.notes)
            state.values.update(result.values)
            for kind, artifact_ids in result.artifacts.items():
                for artifact_id in artifact_ids:
                    state.add_artifact(kind, artifact_id)
            self.artifact_store.save_state(state.run_id, state.to_dict())
            self.logger.write(
                self.artifact_store.run_dir(state.run_id),
                "agent_finished",
                {"agent": agent.name, "artifacts": result.artifacts},
            )

        state.stage = "completed"
        self.artifact_store.save_state(state.run_id, state.to_dict())
        self.logger.write(self.artifact_store.run_dir(state.run_id), "workflow_finished", {})
        return state
