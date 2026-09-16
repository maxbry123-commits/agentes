from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from os import environ
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    secret_env: str


PROVIDERS = (
    Provider("nvidia", "https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEYS"),
    Provider("cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEYS"),
    Provider("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEYS"),
)

MODEL_PRIORITY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kimi_k", ("kimi-k3", "kimi-k2.6", "kimi-k2", "kimi")),
    ("minimax", ("minimax-m3", "minimax-m2.7", "minimax")),
    ("deepseek_v4_pro", ("deepseek-v4-pro",)),
    ("deepseek_v4_flash", ("deepseek-v4-flash",)),
    ("glm_5", ("glm-5.2", "glm-5", "glm5")),
    ("meta_glimmer", ("muse-glimmer", "meta-glimmer", "glimmer")),
    ("qwen_3_8", ("qwen3.8", "qwen-3.8", "qwen/qwen3.8")),
    ("gpt_oss", ("gpt-oss-120b", "gpt-oss-20b", "gpt-oss")),
)


class ModelRouterMVP:
    """Availability-first model router for Wordflow LOOP YAIWES."""

    def __init__(self) -> None:
        self.routes: list[dict[str, Any]] = []
        self._health: dict[tuple[str, int, str], bool] = {}

    @staticmethod
    def _keys(provider: Provider) -> list[str]:
        return [value.strip() for value in environ.get(provider.secret_env, "").split(",") if value.strip()]

    @staticmethod
    def _family(model: str) -> tuple[int, str]:
        low = model.lower()
        for rank, (family, aliases) in enumerate(MODEL_PRIORITY):
            if any(alias in low for alias in aliases):
                return rank, family
        return len(MODEL_PRIORITY), "other"

    @staticmethod
    def _public_route(route: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in route.items() if key != "key"}

    def discover(self) -> dict[str, Any]:
        self.routes = []
        self._health = {}
        report: dict[str, Any] = {}
        for provider in PROVIDERS:
            checks: list[dict[str, Any]] = []
            for slot, key in enumerate(self._keys(provider), 1):
                try:
                    client = OpenAI(api_key=key, base_url=provider.base_url)
                    models = sorted({item.id for item in client.models.list().data})
                    checks.append({"key_slot": slot, "status": "OK", "models": models})
                    for model in models:
                        rank, family = self._family(model)
                        self.routes.append({"provider": provider.name,"key_slot": slot,"key": key,"model": model,"family": family,"priority": rank + 1})
                except Exception as exc:
                    checks.append({"key_slot": slot, "status": "ERROR", "error": type(exc).__name__})
            report[provider.name] = checks
        return {"status": "OK" if self.routes else "NO_AVAILABLE_MODELS","providers": report,"routes": [self._public_route(route) for route in self.candidates()]}

    def candidates(self) -> list[dict[str, Any]]:
        provider_order = {"nvidia": 0, "cerebras": 1, "groq": 2}
        return sorted(self.routes,key=lambda route: (route["priority"],route["family"],provider_order.get(route["provider"], 99),route["key_slot"],route["model"].lower()))

    @staticmethod
    def _client(route: dict[str, Any]) -> OpenAI:
        provider = next(item for item in PROVIDERS if item.name == route["provider"])
        return OpenAI(api_key=route["key"], base_url=provider.base_url)

    def probe_route(self, route: dict[str, Any]) -> bool:
        cache_key = (route["provider"], int(route["key_slot"]), route["model"])
        if cache_key in self._health:
            return self._health[cache_key]
        try:
            response = self._client(route).chat.completions.create(model=route["model"],messages=[{"role": "user", "content": "Reply only OK"}],max_tokens=8)
            healthy = bool(response.choices)
        except Exception:
            healthy = False
        self._health[cache_key] = healthy
        return healthy

    @staticmethod
    def _rotate_same_family(routes: list[dict[str, Any]], lane: int) -> list[dict[str, Any]]:
        if not routes:
            return routes
        shift = lane % len(routes)
        return routes[shift:] + routes[:shift]

    def ordered_for_lane(self, lane: int = 0) -> list[dict[str, Any]]:
        ordered = self.candidates()
        result: list[dict[str, Any]] = []
        for priority in sorted({route["priority"] for route in ordered}):
            same_priority = [route for route in ordered if route["priority"] == priority]
            result.extend(self._rotate_same_family(same_priority, lane))
        return result

    def dispatch(self, task: dict[str, Any], lane: int = 0) -> dict[str, Any]:
        if not self.routes:
            self.discover()
        attempts: list[dict[str, Any]] = []
        for route in self.ordered_for_lane(lane):
            public = self._public_route(route)
            if not self.probe_route(route):
                attempts.append({**public, "status": "PROBE_FAILED"})
                continue
            try:
                response = self._client(route).chat.completions.create(model=route["model"],messages=task["messages"],max_tokens=task.get("max_tokens", 512))
                return {"status": "OK","agent_id": task.get("agent_id"),"provider": route["provider"],"model": route["model"],"family": route["family"],"priority": route["priority"],"key_slot": route["key_slot"],"content": response.choices[0].message.content,"failed_attempts": attempts}
            except Exception as exc:
                attempts.append({**public, "status": "DISPATCH_FAILED", "error": type(exc).__name__})
                self._health[(route["provider"], int(route["key_slot"]), route["model"])] = False
        return {"status": "ALL_ROUTES_FAILED", "agent_id": task.get("agent_id"), "attempts": attempts}

    def dispatch_parallel(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not tasks:
            return []
        if not self.routes:
            self.discover()
        if not self.routes:
            return [{"status": "NO_ROUTE", "agent_id": task.get("agent_id")} for task in tasks]
        with ThreadPoolExecutor(max_workers=min(len(tasks), 16)) as pool:
            futures = [pool.submit(self.dispatch, task, lane=index) for index, task in enumerate(tasks)]
            return [future.result() for future in futures]
