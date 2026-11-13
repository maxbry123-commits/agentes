# V5: Context-Window Preflight — Design Spec

> **Goal:** Prevent oversized LLM requests by checking estimated token count against the target model's context window before every API call. Auto-compact if exceeded, inform user if unrecoverable.

## Architecture

### New Module
`src/jarvis/core/preflight.py` (~80 lines)

### Integration Point
`UnifiedLLMClient.chat()` in `src/jarvis/core/unified_llm.py` — the single choke point for all LLM calls (Planner, Reflector, SkillGenerator, MediaPipeline, etc.). Preflight runs after model selection, before the actual backend call.

## Data Model

```python
from dataclasses import dataclass

@dataclass
class PreflightResult:
    ok: bool
    estimated_tokens: int
    context_window: int
    usage_pct: float           # 0.0 - 1.0
    compacted: bool = False    # True if messages were auto-compacted
    dropped_count: int = 0     # Number of messages dropped during compaction


class ContextWindowExceeded(Exception):
    """Raised when context window cannot be satisfied even after compaction."""

    def __init__(self, model: str, estimated: int, limit: int) -> None:
        self.model = model
        self.estimated = estimated
        self.limit = limit
        super().__init__(
            f"Context window exceeded for {model}: "
            f"{estimated} estimated tokens > {limit} limit"
        )
```

## Token Estimation

Pure heuristic, no tokenizer dependency:

```python
def estimate_tokens(messages: list, system: str = "", tools: list | None = None) -> int:
    import json
    total_bytes = 0
    if system:
        total_bytes += len(system.encode("utf-8"))
    if messages:
        total_bytes += len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))
    if tools:
        total_bytes += len(json.dumps(tools, ensure_ascii=False).encode("utf-8"))
    # Conservative: ~4 bytes per token for English/German mixed content
    return total_bytes // 4
```

Factor 4 bytes/token is conservative (real ratio is ~3.5 for English, ~2.5 for CJK). This means we may over-estimate slightly, which is safer than under-estimating.

## Preflight Check Algorithm

```
preflight_check(model, messages, system, tools, max_output_tokens)
  1. Get context_window from ModelRouter.get_model_config(model)
     - If model unknown: return PreflightResult(ok=True) — skip check
  2. estimated_input = estimate_tokens(messages, system, tools)
  3. estimated_total = estimated_input + max_output_tokens
  4. usage_pct = estimated_total / context_window
  5. If usage_pct <= 0.8:
     → return PreflightResult(ok=True, usage_pct=usage_pct)
  6. If usage_pct <= 1.0:
     → log.warning("context_window_near_limit", model=model, usage_pct=usage_pct)
     → return PreflightResult(ok=True, usage_pct=usage_pct)
  7. If usage_pct > 1.0:
     → attempt auto_compact(messages)
     → re-estimate
     → if now ok: return PreflightResult(ok=True, compacted=True, dropped_count=N)
     → if still exceeded: raise ContextWindowExceeded(model, estimated, limit)
```

## Auto-Compaction Strategy

When preflight detects overflow:

1. Preserve: system prompt (never dropped) + last 4 message pairs (user+assistant)
2. Drop oldest messages first, one at a time
3. After each drop: re-estimate tokens
4. Stop when estimated_total <= context_window (with 10% safety margin)
5. If only system + 4 pairs remain and still exceeded: raise ContextWindowExceeded

The compaction modifies the `messages` list in-place (caller passes mutable list). A log entry records how many messages were dropped.

This is NOT LLM-summarization — it's simple truncation. LLM-based summarization would require an LLM call which itself might exceed the context window. Simple truncation is predictable and free.

## Error Handling in PGE Loop

`ContextWindowExceeded` is caught in `gateway.py` at the PGE loop level:

```python
except ContextWindowExceeded as e:
    user_msg = (
        f"Der Kontext ist zu groß für {e.model} "
        f"({e.estimated} von {e.limit} Tokens). "
        f"Bitte starte eine neue Session oder wechsle zu einem Modell "
        f"mit größerem Context-Window."
    )
    # Return as direct_response to user
```

This uses i18n via `t("error.context_window_exceeded")` with placeholders.

## Warning Threshold

At 80% usage: log a structured warning but do not block.

```python
log.warning(
    "context_window_near_limit",
    model=model,
    estimated_tokens=estimated_input,
    context_window=context_window,
    usage_pct=round(usage_pct * 100, 1),
)
```

This lets operators monitor context pressure in logs without disrupting users.

## Model Context Window Registry

Uses existing `ModelRouter.get_model_config()` which returns `context_window` from config. For models not in config, the check is skipped (unknown model = no preflight, let the provider handle it).

No hardcoded model registry needed — Cognithor already has this data in its model configuration.

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/jarvis/core/preflight.py` | **CREATE** — PreflightResult, ContextWindowExceeded, estimate_tokens(), preflight_check(), auto_compact() |
| `src/jarvis/core/unified_llm.py` | **MODIFY** — Call preflight_check() before backend.chat() |
| `src/jarvis/gateway/gateway.py` | **MODIFY** — Catch ContextWindowExceeded in PGE loop |
| `src/jarvis/i18n/locales/en.json` | **MODIFY** — Add error.context_window_exceeded key |
| `src/jarvis/i18n/locales/de.json` | **MODIFY** — Add error.context_window_exceeded key |
| `tests/test_preflight.py` | **CREATE** — 5 test cases |

## Test Cases

1. **test_preflight_ok** — 1000 tokens, 32K window → ok=True, usage_pct ~3%
2. **test_preflight_warning_threshold** — 26K tokens, 32K window → ok=True, warning logged
3. **test_preflight_exceeded_auto_compacts** — 40K tokens in 20 messages, 32K window → drops oldest messages → ok=True, compacted=True
4. **test_preflight_exceeded_unrecoverable** — Single massive system prompt > window → raises ContextWindowExceeded
5. **test_estimate_tokens_accuracy** — Known strings → estimated within 30% of tiktoken reference
6. **test_unknown_model_skips_check** — Unknown model name → ok=True (no check)
