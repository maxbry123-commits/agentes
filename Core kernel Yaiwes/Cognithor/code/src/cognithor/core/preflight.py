"""Context-Window Preflight Check.

Estimates token count before LLM API calls and prevents oversized requests.
If a request exceeds the model's context window, auto-compacts by dropping
oldest messages. If still too large, raises ContextWindowExceeded.

Inspired by Claw Code's prompt cache / preflight pattern.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Conservative bytes-per-token ratio.
# English ~3.5, German ~3.2, CJK ~2.5. We use 4 to avoid under-estimation.
_BYTES_PER_TOKEN = 4

# Warn when context usage exceeds this fraction (but don't block).
_WARNING_THRESHOLD = 0.80

# Safety margin: after compaction, target this fraction of context window.
_COMPACTION_TARGET = 0.90

# Minimum messages to preserve during compaction (system + last N pairs).
_MIN_PRESERVE_MESSAGES = 8  # ~4 user+assistant pairs


@dataclass
class PreflightResult:
    """Result of a context-window preflight check."""

    ok: bool
    estimated_tokens: int
    context_window: int
    usage_pct: float  # 0.0 - 1.0
    compacted: bool = False
    dropped_count: int = 0


class ContextWindowExceeded(Exception):
    """Raised when context window cannot be satisfied even after compaction."""

    def __init__(self, model: str, estimated: int, limit: int) -> None:
        self.model = model
        self.estimated = estimated
        self.limit = limit
        super().__init__(
            f"Context window exceeded for {model}: {estimated} estimated tokens > {limit} limit"
        )


def estimate_tokens(
    messages: list[dict[str, Any]] | None = None,
    system: str = "",
    tools: list[dict[str, Any]] | None = None,
) -> int:
    """Estimate token count from message content using byte-length heuristic.

    This is intentionally conservative (over-estimates slightly) to avoid
    sending requests that will be rejected by the provider.
    """
    total_bytes = 0
    if system:
        total_bytes += len(system.encode("utf-8"))
    if messages:
        total_bytes += len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))
    if tools:
        total_bytes += len(json.dumps(tools, ensure_ascii=False).encode("utf-8"))
    return max(1, total_bytes // _BYTES_PER_TOKEN)


def preflight_check(
    model: str,
    messages: list[dict[str, Any]],
    context_window: int,
    *,
    system: str = "",
    tools: list[dict[str, Any]] | None = None,
    max_output_tokens: int = 4096,
    auto_compact: bool = True,
) -> PreflightResult:
    """Check whether a request fits within the model's context window.

    Args:
        model: Model name (for logging/errors).
        messages: Chat messages (mutable list, may be modified by compaction).
        context_window: Maximum tokens for the target model.
        system: System prompt text.
        tools: Tool schemas.
        max_output_tokens: Reserved tokens for the response.
        auto_compact: If True, attempt to drop old messages when exceeded.

    Returns:
        PreflightResult with check outcome.

    Raises:
        ContextWindowExceeded: If request is too large even after compaction.
    """
    if context_window <= 0:
        # Unknown or unconfigured model — skip check
        return PreflightResult(ok=True, estimated_tokens=0, context_window=0, usage_pct=0.0)

    estimated_input = estimate_tokens(messages, system, tools)
    estimated_total = estimated_input + max_output_tokens
    usage_pct = estimated_total / context_window

    # Under threshold — all good
    if usage_pct <= _WARNING_THRESHOLD:
        return PreflightResult(
            ok=True,
            estimated_tokens=estimated_input,
            context_window=context_window,
            usage_pct=usage_pct,
        )

    # Warning zone (80-100%) — log but allow
    if usage_pct <= 1.0:
        log.warning(
            "context_window_near_limit",
            model=model,
            estimated_tokens=estimated_input,
            context_window=context_window,
            usage_pct=round(usage_pct * 100, 1),
        )
        return PreflightResult(
            ok=True,
            estimated_tokens=estimated_input,
            context_window=context_window,
            usage_pct=usage_pct,
        )

    # Exceeded — attempt auto-compaction
    if not auto_compact:
        raise ContextWindowExceeded(model, estimated_total, context_window)

    dropped = _compact_messages(messages, context_window, max_output_tokens, system, tools)

    if dropped > 0:
        new_estimated = estimate_tokens(messages, system, tools)
        new_total = new_estimated + max_output_tokens
        new_usage = new_total / context_window

        if new_usage <= 1.0:
            log.info(
                "preflight_auto_compacted",
                model=model,
                dropped_messages=dropped,
                new_usage_pct=round(new_usage * 100, 1),
            )
            return PreflightResult(
                ok=True,
                estimated_tokens=new_estimated,
                context_window=context_window,
                usage_pct=new_usage,
                compacted=True,
                dropped_count=dropped,
            )

    # Still too large after compaction
    final_estimated = estimate_tokens(messages, system, tools) + max_output_tokens
    raise ContextWindowExceeded(model, final_estimated, context_window)


def _compact_messages(
    messages: list[dict[str, Any]],
    context_window: int,
    max_output_tokens: int,
    system: str,
    tools: list[dict[str, Any]] | None,
) -> int:
    """Drop oldest non-system messages until the request fits.

    Preserves system messages and the last _MIN_PRESERVE_MESSAGES messages.
    Modifies the messages list in-place.

    Returns:
        Number of messages dropped.
    """
    target_tokens = int(context_window * _COMPACTION_TARGET) - max_output_tokens
    dropped = 0

    while len(messages) > _MIN_PRESERVE_MESSAGES:
        current = estimate_tokens(messages, system, tools)
        if current <= target_tokens:
            break

        # Find the first non-system message to drop
        drop_idx = _find_droppable_index(messages)
        if drop_idx < 0:
            break

        messages.pop(drop_idx)
        dropped += 1

    return dropped


def _find_droppable_index(messages: list[dict[str, Any]]) -> int:
    """Find the index of the oldest non-system message that can be dropped.

    Skips system messages (they are never dropped).
    Returns -1 if no droppable message is found.
    """
    for i, msg in enumerate(messages):
        if msg.get("role") != "system":
            return i
    return -1
