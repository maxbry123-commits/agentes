from __future__ import annotations

from typing import Any

from core.state import ResearchState


def llm_budget_allows(state: ResearchState, settings: dict[str, Any]) -> tuple[bool, str]:
    call_budget = settings.get("llm_call_budget")
    token_budget = settings.get("llm_token_budget")
    calls_used = int(state.values.get("llm_calls_used", 0))
    tokens_used = int(state.values.get("llm_tokens_used", 0))
    if isinstance(call_budget, int) and call_budget >= 0 and calls_used >= call_budget:
        return False, "skipped_call_budget"
    if isinstance(token_budget, int) and token_budget >= 0 and tokens_used >= token_budget:
        return False, "skipped_token_budget"
    return True, "allowed"


def record_llm_usage(state: ResearchState, usage: dict[str, Any]) -> None:
    state.values["llm_calls_used"] = int(state.values.get("llm_calls_used", 0)) + 1
    total_tokens = usage.get("total_tokens", 0)
    try:
        token_count = int(total_tokens)
    except (TypeError, ValueError):
        token_count = 0
    state.values["llm_tokens_used"] = int(state.values.get("llm_tokens_used", 0)) + token_count


def llm_usage_values(state: ResearchState) -> dict[str, int]:
    return {
        "llm_calls_used": int(state.values.get("llm_calls_used", 0)),
        "llm_tokens_used": int(state.values.get("llm_tokens_used", 0)),
    }
