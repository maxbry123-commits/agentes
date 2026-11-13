"""Shared transport and parsing primitives for failure-mode judge CLIs."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar


T = TypeVar("T")


def batched(items: Sequence[T], batch_size: int) -> Iterable[Sequence[T]]:
    """Yield contiguous batches while preserving input order."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def strip_json_code_fence(payload: str) -> str:
    """Remove one optional Markdown code fence from a JSON model response."""
    text = payload.strip()
    if not text.startswith("```"):
        return text
    parts = text.split("```", 2)
    if len(parts) < 2:
        return text
    content = parts[1]
    if "\n" in content:
        content = content.split("\n", 1)[1]
    return content.strip()


def request_json_array(
    client: Any,
    *,
    model: str,
    temperature: float,
    system_prompt: str,
    user_prompt: str,
    max_output_tokens: int | None = None,
    max_attempts: int = 1,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> list[dict[str, Any]]:
    """Request and validate a JSON-array response from an OpenAI-compatible client."""
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")

    completion_kwargs: dict[str, Any] = {}
    if max_output_tokens:
        completion_kwargs["max_completion_tokens"] = max_output_tokens

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **completion_kwargs,
            )
            content = strip_json_code_fence(response.choices[0].message.content or "[]")
            parsed = json.loads(content)
            if not isinstance(parsed, list):
                raise ValueError("Judge response must be a JSON array")
            return [entry for entry in parsed if isinstance(entry, dict)]
        except Exception as exc:
            if attempt >= max_attempts:
                raise
            if on_retry:
                on_retry(attempt, exc)

    raise AssertionError("unreachable")
