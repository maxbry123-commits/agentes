from __future__ import annotations

from dataclasses import asdict, dataclass
import os

from schemas.topic_pack import TopicPack


@dataclass(slots=True)
class ModelRoute:
    agent: str
    provider: str
    model: str
    api_key_env: str = ""
    task_difficulty: str = ""
    enabled: bool = False


class ModelRouter:
    def __init__(self, topic: TopicPack):
        self.config = topic.metadata.get("models", {})

    def route_for(self, agent_name: str) -> ModelRoute:
        routes = self.config.get("routes", {})
        default = self.config.get("default", {})
        selected = routes.get(agent_name, default)
        provider = str(selected.get("provider", default.get("provider", "offline")))
        model = str(selected.get("model", default.get("model", "rule_based")))
        api_key_env = str(selected.get("api_key_env", default.get("api_key_env", "")))
        task_difficulty = str(selected.get("task_difficulty", default.get("task_difficulty", "")))
        return ModelRoute(
            agent=agent_name,
            provider=provider,
            model=model,
            api_key_env=api_key_env,
            task_difficulty=task_difficulty,
            enabled=self._is_enabled(provider, api_key_env),
        )

    def summary(self) -> dict[str, object]:
        agents = self.config.get("routes", {}).keys()
        routes = {agent: asdict(self.route_for(agent)) for agent in agents}
        routes["default"] = asdict(self.route_for("default"))
        return {
            "policy": self.config.get("policy", "offline_first"),
            "routes": routes,
        }

    def _is_enabled(self, provider: str, api_key_env: str) -> bool:
        if provider in {"offline", "local", "rule_based"}:
            return True
        return bool(api_key_env and os.environ.get(api_key_env))
