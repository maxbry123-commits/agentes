from __future__ import annotations

from dataclasses import dataclass, field
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
    usage: dict[str, Any] = field(default_factory=dict)
    attempts: int = 1


class OpenAICompatibleClient:
    def __init__(self, timeout: int = 60, retries: int = 1):
        self.timeout = timeout
        self.retries = retries

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
        last_error = ""
        attempts = max(1, self.retries + 1)
        for attempt in range(1, attempts + 1):
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
                message = data.get("choices", [{}])[0].get("message", {})
                text = message.get("content", "")
                usage = data.get("usage", {})
                return LLMResponse(
                    ok=bool(text),
                    text=text,
                    provider=route.provider,
                    model=route.model,
                    usage=usage if isinstance(usage, dict) else {},
                    attempts=attempt,
                )
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")[:500]
                return LLMResponse(
                    ok=False,
                    error=f"HTTP {exc.code}: {exc.reason}; {detail}",
                    provider=route.provider,
                    model=route.model,
                    attempts=attempt,
                )
            except json.JSONDecodeError as exc:
                return LLMResponse(
                    ok=False,
                    error=str(exc),
                    provider=route.provider,
                    model=route.model,
                    attempts=attempt,
                )
            except (URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
                if attempt == attempts:
                    return LLMResponse(
                        ok=False,
                        error=last_error,
                        provider=route.provider,
                        model=route.model,
                        attempts=attempt,
                    )
        return LLMResponse(
            ok=False,
            error=last_error or "unknown LLM client error",
            provider=route.provider,
            model=route.model,
            attempts=attempts,
        )


def extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None
