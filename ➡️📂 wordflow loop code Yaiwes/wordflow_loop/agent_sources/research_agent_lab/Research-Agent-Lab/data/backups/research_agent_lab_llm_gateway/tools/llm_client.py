from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tools.model_router import ModelRoute


@dataclass(slots=True)
class LLMResponse:
    ok: bool
    text: str = ""
    error: str = ""
    provider: str = ""
    model: str = ""


class OpenAICompatibleClient:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    def chat(
        self,
        route: ModelRoute,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1200,
        base_url: str | None = None,
    ) -> LLMResponse:
        if not route.enabled:
            return LLMResponse(
                ok=False,
                error=f"route is disabled; missing env var {route.api_key_env}",
                provider=route.provider,
                model=route.model,
            )

        api_key = os.environ.get(route.api_key_env, "")
        if not api_key:
            return LLMResponse(
                ok=False,
                error=f"missing env var {route.api_key_env}",
                provider=route.provider,
                model=route.model,
            )

        endpoint = base_url or os.environ.get("DEEPSEEK_BASE_URL", "")
        if not endpoint:
            endpoint = "https://api.deepseek.com/chat/completions"

        payload: dict[str, Any] = {
            "model": route.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResponse(
                ok=bool(text),
                text=text,
                provider=route.provider,
                model=route.model,
            )
        except HTTPError as exc:
            return LLMResponse(
                ok=False,
                error=f"HTTP {exc.code}: {exc.reason}",
                provider=route.provider,
                model=route.model,
            )
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return LLMResponse(
                ok=False,
                error=str(exc),
                provider=route.provider,
                model=route.model,
            )
