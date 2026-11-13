"""
LLM utility — wraps OpenAI-compatible API for structured extraction and QA.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Any, Optional

from openai import APITimeoutError, OpenAI, RateLimitError

from mmem.config import LLMConfig, get_config

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around OpenAI chat completions with exponential backoff."""

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self._config = config or get_config().llm
        self._client = OpenAI(
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            timeout=self._config.timeout,
        )

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        delay = min(
            self._config.backoff_base ** attempt,
            self._config.backoff_max,
        )
        return delay * (0.5 + random.random() * 0.5)

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Send a single chat completion request, return the assistant text."""
        model = model or self._config.extraction_model
        temperature = temperature if temperature is not None else self._config.temperature

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                }
                if not _uses_default_temperature_only(model):
                    kwargs["temperature"] = temperature
                resp = self._client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except (RateLimitError, APITimeoutError) as e:
                last_exc = e
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "LLM call attempt %d/%d hit %s, retrying in %.1fs",
                    attempt + 1,
                    self._config.max_retries,
                    type(e).__name__,
                    delay,
                )
                time.sleep(delay)
            except Exception as e:
                last_exc = e
                logger.warning(
                    "LLM call attempt %d/%d failed: %s",
                    attempt + 1,
                    self._config.max_retries,
                    e,
                )
                if attempt == self._config.max_retries - 1:
                    raise
                time.sleep(self._backoff_delay(attempt))

        raise last_exc  # type: ignore[misc]

    _FENCE_RE = re.compile(r"```(?:\w*)\s*\n(.*?)```", re.DOTALL)

    def chat_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: str = "",
        temperature: Optional[float] = None,
    ) -> dict[str, Any] | list[Any]:
        """Chat and parse the response as JSON.

        Returns the parsed JSON value (dict or list).
        Falls back to ``{}`` on parse error.
        """
        raw = self.chat(prompt, model=model, system=system, temperature=temperature)
        raw = raw.strip()
        fence_match = self._FENCE_RE.search(raw)
        if fence_match:
            raw = fence_match.group(1).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(
                "Failed to parse LLM JSON output (first 300 chars): %s",
                raw[:300],
            )
            return {}
        if isinstance(parsed, (dict, list)):
            return parsed
        logger.warning("LLM returned non-dict/list JSON: %s", type(parsed).__name__)
        return {}


_default_client: LLMClient | None = None


def _uses_default_temperature_only(model: str) -> bool:
    return model.startswith("gpt-5")


def get_llm_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
