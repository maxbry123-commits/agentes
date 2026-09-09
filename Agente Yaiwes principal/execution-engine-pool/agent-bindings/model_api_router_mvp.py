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

PREFERENCE = {
    "coding": ("kimi-k3", "deepseek-v4", "minimax-m3", "gpt-oss-120b", "qwen", "gemma-4-31b", "glm", "laguna"),
    "reasoning": ("gpt-oss-120b", "kimi-k3", "deepseek-v4", "minimax-m3", "qwen", "glm"),
    "review": ("gpt-oss-120b", "qwen", "kimi-k3", "minimax-m3"),
    "general": ("gpt-oss-120b", "qwen", "kimi-k3", "minimax-m3", "gpt-oss-20b"),
}


class ModelRouterMVP:
    """Availability-first router. Secrets stay in environment variables only."""

    def __init__(self) -> None:
        self.routes: list[dict[str, Any]] = []

    @staticmethod
    def _keys(provider: Provider) -> list[str]:
        return [value.strip() for value in environ.get(provider.secret_env, "").split(",") if value.strip()]

    def discover(self) -> dict[str, Any]:
        self.routes = []
        report: dict[str, Any] = {}
        for provider in PROVIDERS:
            checks = []
            for slot, key in enumerate(self._keys(provider), 1):
                try:
                    client = OpenAI(api_key=key, base_url=provider.base_url)
                    models = sorted({item.id for item in client.models.list().data})
                    checks.append({"key_slot": slot, "status": "OK", "models": models})
                    for model in models:
                        self.routes.append({"provider": provider.name, "key_slot": slot, "key": key, "model": model})
                except Exception as exc:
                    checks.append({"key_slot": slot, "status": "ERROR", "error": type(exc).__name__})
            report[provider.name] = checks
        return {"status": "OK" if self.routes else "NO_AVAILABLE_MODELS", "providers": report}

    @staticmethod
    def _rank(model: str, capability: str) -> tuple[int, str]:
        prefs = PREFERENCE.get(capability, PREFERENCE["general"])
        low = model.lower()
        for index, token in enumerate(prefs):
            if token in low:
                return index, low
        return len(prefs), low

    def candidates(self, capability: str) -> list[dict[str, Any]]:
        order = {"nvidia": 0, "cerebras": 1, "groq": 2}
        return sorted(self.routes, key=lambda r: (self._rank(r["model"], capability), order[r["provider"]], r["key_slot"]))

    def dispatch(self, task: dict[str, Any], offset: int = 0) -> dict[str, Any]:
        capability = task.get("capability", "general")
        candidates = self.candidates(capability)
        if not candidates:
            return {"status": "NO_ROUTE", "agent_id": task.get("agent_id")}
        for route in candidates[offset:] + candidates[:offset]:
            provider = next(item for item in PROVIDERS if item.name == route["provider"])
            try:
                client = OpenAI(api_key=route["key"], base_url=provider.base_url)
                response = client.chat.completions.create(model=route["model"], messages=task["messages"], max_tokens=task.get("max_tokens", 512))
                return {"status": "OK", "agent_id": task.get("agent_id"), "provider": route["provider"], "model": route["model"], "key_slot": route["key_slot"], "content": response.choices[0].message.content}
            except Exception:
                continue
        return {"status": "ALL_ROUTES_FAILED", "agent_id": task.get("agent_id")}

    def dispatch_parallel(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.routes:
            self.discover()
        with ThreadPoolExecutor(max_workers=max(1, min(len(tasks), 16))) as pool:
            futures = [pool.submit(self.dispatch, task, index % max(1, len(self.routes))) for index, task in enumerate(tasks)]
            return [future.result() for future in futures]
