# Observer-Audit-Layer — Design

**Date:** 2026-04-19
**Author:** Cognithor Core
**Status:** Brainstorming approved, ready for implementation plan
**Related:** Inspired by Ern-OS' Observer pattern (github.com/mettamazza/ErnosAgent)

## Summary

A new LLM-based quality audit layer that runs after the Executor and after
the existing `ResponseValidator` (regex, advisory). It checks the final
response across four dimensions — **Hallucination, Sycophancy, Laziness,
Tool-Ignorance** — using a single JSON-structured LLM call. Two dimensions
(Hallucination, Tool-Ignorance) are *blocking*: failures trigger a retry
with structured feedback. Two dimensions (Sycophancy, Laziness) are
*advisory*: failures are logged but do not block delivery. Exhausted
retries deliver the response with a prefixed warning instead of hard
rejection.

Integration stays minimally invasive: the Observer runs inside
`planner.formulate_response()`, alongside the existing `ResponseValidator`.
For Tool-Ignorance failures, it can signal a full PGE re-loop via a new
return envelope; the Gateway-level PGE-Loop catches this directive and
re-enters planning with explicit `observer_feedback` input.

## Context

Cognithor already has multiple overlapping quality-check components:

- `ResponseValidator` (regex, `src/cognithor/core/response_validator.py`):
  4 dimensions — consistency, coverage, assumptions, evidence. Advisory,
  called inside `planner.formulate_response()`.
- `ConfidenceChecker` (`src/cognithor/core/confidence.py`): regex for
  uncertainty markers. Called from the Gatekeeper.
- `Reflector` (`src/cognithor/core/reflector.py`): reflection memory,
  meta-learning. Unrelated to response-time audit.

The Observer complements these, it does not replace them. Overlaps:

| Ern-OS dimension   | Cognithor overlap       |
|--------------------|-------------------------|
| Hallucination      | ≈ `evidence` (regex)    |
| Laziness           | ≈ `coverage` (regex)    |
| Sycophancy         | — none                  |
| Tool-Ignorance     | — none                  |

Sycophancy and Tool-Ignorance are genuinely new checks. The Hallucination
and Laziness dimensions duplicate existing regex coverage but with an
LLM's contextual precision — the layers are belt-and-suspenders at
different cost profiles.

## Goals

- **Quality floor for released responses.** Filter clear hallucinations
  and tool-ignorance before they reach users.
- **Marketing-aligned narrative.** Four named dimensions become a
  differentiator: *"Cognithor audits every response for hallucination,
  tool-ignorance, sycophancy and laziness before delivery."*
- **Telemetry for tuning.** Capture per-dimension failure rates across
  models and sessions to inform prompt engineering and model selection.
- **Configurability.** Per-dimension enable/disable; per-dimension
  blocking-vs-advisory selection; separate Observer model.

## Non-Goals

- Replace the existing `ResponseValidator`. It stays.
- Hard-reject failing responses. Warning-delivery keeps UX predictable.
- Run on simple/short/no-tool responses selectively. Observer runs on
  every response when enabled (predictability beats optimization).
- Add interpretability tooling (SAE, steering vectors). Out of scope
  for v1.0.

## Design Decisions Summary

Outcomes from the brainstorming conversation:

| Q   | Decision                                                                                          |
|-----|---------------------------------------------------------------------------------------------------|
| Q1  | **Hybrid blocking.** Hallucination + Tool-Ignorance block; Sycophancy + Laziness advisory.        |
| Q2  | **Additive.** `ResponseValidator` keeps running, Observer is a new layer beside it.              |
| Q3  | **Single prompt, JSON response.** One LLM call checks all four dimensions via Ollama `format="json"`. |
| Q4  | **Deliver-with-warning** after max 2 retries. No hard reject.                                    |
| Q5  | **Dedicated `models.observer`** config field, default = planner model.                           |
| Q6  | **Always runs when enabled.** No bypass for short/no-tool responses.                             |
| Q7  | **Structured JSON retry feedback** injected as system-message.                                   |
| Q8  | **Per-dimension config** + `blocking_dimensions: list[str]` selector. All enabled by default.    |
| Q9  | **Dual audit log.** Structlog for live debug, SQLite for historical analysis.                    |
| Q10 | **Production-grade: differentiated retry strategies.** Hallucination → response-regen; Tool-Ignorance → PGE re-loop. |

## Architecture

### Placement in the existing code

The Observer lives at the same call-site as the existing
`ResponseValidator`: inside `planner.formulate_response()`, after the LLM
call that produces the draft response. This keeps all response-time
quality checks co-located in one file instead of spreading across
Gateway phases.

The Gateway's PGE-Loop in `src/cognithor/gateway/phases/pge.py` gains a
single new capability: recognizing an `observer_directive` in the
response envelope and re-iterating the PGE-Loop with explicit
`observer_feedback` as PlannerInput.

### Relationship to existing quality layers

```
User message
    │
    ▼
Gateway.handle_message
    │
    ▼
PGE-Loop (max 25 iterations)
    │
    ├── Planner.plan
    ├── Gatekeeper.evaluate
    ├── Executor.run → tool_results
    └── Planner.formulate_response
           │
           ▼
        LLM call → draft_response
           │
           ▼
        ResponseValidator (regex, advisory) — existing, unchanged
           │
           ▼
        observer.enabled?
           ├── no  → return ResponseEnvelope(draft, directive=None)
           └── yes → ObserverAudit.audit → AuditResult
                       │
                       ▼
              AuditResult.retry_strategy
                       │
      ┌────────────────┼────────────────┬───────────────────────┐
      ▼                ▼                ▼                       ▼
   "pass"      "response_regen"   "pge_reloop"          "deliver_with_warning"
      │                │                │                       │
      │                ▼                ▼                       ▼
      │        retry in planner    Envelope(draft,       prefix warning,
      │        (loop back to       PGEReloopDirective)   AuditStore.record,
      │         LLM call)          bubble up to          return Envelope
      │                │            Gateway, re-loop
      ▼                ▼                │                       │
   AuditStore      AuditStore           ▼                       │
   .record         .record      Gateway.pge_loop                │
      │                │        re-iterates with                │
      ▼                ▼        observer_feedback               │
   return         return                                        │
   Envelope       Envelope                                      │
      │                │                                         │
      └────────────────┴─────────────────────────────────────────┘
                                  │
                                  ▼
                              Gateway delivers envelope.content to user
```

### Latency profile

- Happy path: 1 Observer LLM call, ~3-5s (qwen3:32b local), added to
  existing response time.
- Worst case with 2 retries: +10-15s total.
- Blocking only on 2 of 4 dimensions bounds the retry rate.

Users who need maximum responsiveness set `observer.enabled=False` or
switch `models.observer` to a smaller model (e.g. qwen3:8b).

## Components

Six isolated units, each with a single responsibility:

### 1. `ObserverConfig` — `src/cognithor/config.py`

```python
class ObserverConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)
    check_hallucination: bool = True
    check_sycophancy: bool = True
    check_laziness: bool = True
    check_tool_ignorance: bool = True
    blocking_dimensions: list[str] = Field(
        default_factory=lambda: ["hallucination", "tool_ignorance"]
    )
    warning_prefix: str = "[Quality check flagged issues]"
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=20)

    @field_validator("blocking_dimensions")
    @classmethod
    def _validate_blocking(cls, v: list[str]) -> list[str]:
        valid = {"hallucination", "sycophancy", "laziness", "tool_ignorance"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Unknown dimensions in blocking_dimensions: {sorted(invalid)}")
        return v
```

Added to `JarvisConfig` as `observer: ObserverConfig = Field(default_factory=ObserverConfig)`.

### 2. `ModelsConfig` extension — `src/cognithor/config.py`

New field:
```python
observer: ModelConfig = Field(default_factory=lambda: ModelConfig(name="qwen3:32b"))
```

Entry added to `_OLLAMA_DEFAULT_MODEL_NAMES` so provider-switching
(OpenAI/Anthropic) maps the observer to a comparable-strength model.

### 3. Dataclasses — `src/cognithor/core/observer.py`

```python
@dataclass(frozen=True)
class DimensionResult:
    name: Literal["hallucination", "sycophancy", "laziness", "tool_ignorance"]
    passed: bool
    reason: str
    evidence: str           # quote from response or tool result
    fix_suggestion: str     # what to change on retry

@dataclass(frozen=True)
class AuditResult:
    overall_passed: bool
    dimensions: dict[str, DimensionResult]
    retry_count: int
    final_action: Literal["pass", "rejected_with_retry", "delivered_with_warning"]
    retry_strategy: Literal["response_regen", "pge_reloop", "deliver", "deliver_with_warning"]
    model: str
    duration_ms: int
    degraded_mode: bool     # True if fallback model was used
    error_type: str | None  # None on success

@dataclass(frozen=True)
class PGEReloopDirective:
    reason: Literal["tool_ignorance"]
    missing_data: str
    suggested_tools: list[str]

@dataclass(frozen=True)
class ResponseEnvelope:
    content: str
    directive: PGEReloopDirective | None  # None = deliver content to user
```

### 4. `ObserverAudit` — `src/cognithor/core/observer.py` (~350 LOC)

The core class. Single public method:

```python
async def audit(
    self,
    user_message: str,
    response: str,
    tool_results: list[ActionResult],
    session_id: str,
    retry_count: int = 0,
) -> AuditResult: ...
```

Private helpers:

- `_build_prompt(user_message, response, tool_results) -> list[Message]` —
  composes the system + user messages with the JSON-output schema
  embedded. The schema is a fixed string constant.
- `_call_llm_audit(messages) -> dict` — calls `ollama.chat()` with
  `format="json"` and `options={"temperature": 0.1}`. Wraps in a timeout.
- `_parse_response(raw_json_text) -> AuditResult` — Pydantic-validates
  the JSON, falls back to `partial audit` (missing dimensions → skipped)
  or fail-open (malformed JSON).
- `_decide_retry_strategy(dimensions) -> str` — the priority logic:
  tool_ignorance failure wins over hallucination failure for retry
  strategy selection (pge_reloop priority over response_regen).
- `_is_duplicate_feedback(feedback_hash, session_state) -> bool` —
  dedupe against `seen_hashes` set.
- `build_retry_feedback(result) -> dict` — produces the system-message
  payload for response-regen retries.

### 5. `AuditStore` — `src/cognithor/core/observer_store.py` (~180 LOC)

SQLite-backed persistence (plain SQLite, not SQLCipher — audit data is
telemetry, not secrets).

```sql
CREATE TABLE audits (
    audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT NOT NULL,
    timestamp        INTEGER NOT NULL,        -- unix ms
    user_message_hash TEXT NOT NULL,          -- sha256
    response_hash    TEXT NOT NULL,
    model            TEXT NOT NULL,
    dimensions_json  TEXT NOT NULL,           -- serialized dict[str, DimensionResult]
    overall_passed   INTEGER NOT NULL,        -- 0 or 1
    retry_count      INTEGER NOT NULL,
    final_action     TEXT NOT NULL,
    retry_strategy   TEXT,
    duration_ms      INTEGER NOT NULL,
    degraded_mode    INTEGER NOT NULL,
    error_type       TEXT
);
CREATE INDEX idx_session ON audits(session_id);
CREATE INDEX idx_timestamp ON audits(timestamp);
CREATE INDEX idx_dimension_failed ON audits(overall_passed);
```

Methods:
- `record(AuditResult) -> None` — write one record, handles disk-full /
  lock / corruption per Error-Handling section.
- `query(since: int, session_id: str | None, dimension_failed: str | None) -> list[AuditRecord]`
  — for later dashboard integration.

DB path: `~/.cognithor/db/observer_audits.db`. Created lazily on first
record.

### 6. Planner / Gateway integration

Minimal code surface:

**`planner.formulate_response()` changes:**

- Return type changes from `str` to `ResponseEnvelope`. **This is a
  breaking change** — all call sites must be updated:
    - `planner.formulate_response_stream()` (same file)
    - `gateway/phases/pge.py` (handles the envelope)
    - Any test fixtures that mock `formulate_response()`
- After the existing `ResponseValidator` block, add Observer invocation
  with the retry loop. Retry happens in a bounded `while` loop up to
  `observer.max_retries` iterations.

**`gateway/phases/pge.py` changes:**

- After `planner.formulate_response()` returns, inspect
  `envelope.directive`. If not None, synthesize a new `PlannerInput`
  with `observer_feedback=envelope.directive` and iterate the PGE-loop
  once more (counting against `max_iterations=25`).
- If directive is None, deliver `envelope.content` to the user.

## Data Flow

### Normal path (pass)

1. User sends message
2. Gateway enters PGE-Loop
3. Planner plans, Gatekeeper approves, Executor runs tools
4. `planner.formulate_response()` calls LLM → draft_response
5. `ResponseValidator` logs any regex hits (advisory)
6. `ObserverAudit.audit()` returns `AuditResult(overall_passed=True)`
7. `AuditStore.record()`
8. Return `ResponseEnvelope(draft_response, directive=None)`
9. Gateway delivers to user

### Hallucination-fail → Response-regen

1. Same as steps 1-5 above
2. `ObserverAudit.audit()` returns `final_action="rejected_with_retry"`,
   `retry_strategy="response_regen"`
3. `retry_count` (0 → 1)
4. Planner injects `build_retry_feedback(result)` as a system-message
   into the existing messages array
5. Same LLM call is issued again → draft_response_v2
6. `ResponseValidator` again (advisory)
7. `ObserverAudit.audit(retry_count=1)` runs again
8. If pass → record, return envelope
9. If fail again (retry_count=1 < max_retries=2) → another regen loop
10. If still fail after max_retries: `final_action="delivered_with_warning"`,
    prefix the warning, record, return envelope

### Tool-Ignorance-fail → PGE re-loop

1. Same as steps 1-5 above
2. `ObserverAudit.audit()` returns `retry_strategy="pge_reloop"`,
   `directive=PGEReloopDirective(reason="tool_ignorance", missing_data="...",
   suggested_tools=["web_search"])`
3. `AuditStore.record()`
4. Return `ResponseEnvelope(draft_response, directive=<the directive>)`
5. Gateway-PGE-Loop catches the directive
6. **Dedupe check**: hash the directive's `(reason, missing_data)`. If
   already in `session.seen_observer_feedback_hashes`, downgrade to
   response-regen instead.
7. Otherwise: add hash to set, synthesize new `PlannerInput` with
   `observer_feedback=directive`, re-enter PGE-Loop (increments
   `pge_iteration_count`)
8. New Planner → Executor → formulate_response
9. Observer runs again on the new response
10. If pass: deliver. If fail: retry per budget or deliver-with-warning.

### Retry feedback format

As system-message injected into the Planner's messages array:

```json
{
  "observer_rejection": {
    "retry_count": 1,
    "max_retries": 2,
    "dimensions_failed": ["hallucination"],
    "reasons": [
      "Response claims 'TechCorp was founded in 2015' but no tool_result contains this date."
    ],
    "fix_suggestions": [
      "Either remove the founding year, or call search_memory for the actual date."
    ]
  }
}
```

## Error Handling

Core philosophy: **fail-open with loud logging.** The Observer is
additive quality assurance, not a hard dependency. A broken Observer
must never block the Core agent. The existing `ResponseValidator`
continues to run, so a fail-open state still leaves the cheap
heuristic check in place.

### LLM inference failures

| Failure                    | Behaviour                                                            |
|----------------------------|----------------------------------------------------------------------|
| Timeout (default 30s)      | Fail-open, log `observer_timeout`, response delivered as-is          |
| Connection error to Ollama | Fail-open, log `observer_connection_failed`                          |
| Empty response from LLM    | Fail-open, log `observer_empty_response`                             |

### JSON schema validation

| Failure                             | Behaviour                                                              |
|-------------------------------------|------------------------------------------------------------------------|
| Invalid JSON syntax                 | One retry with simplified prompt formatting; still fail → fail-open    |
| Pydantic validation failed          | Fail-open, log `observer_schema_validation_failed` with specifics      |
| Single dimension missing from JSON  | Partial audit — missing dimension marked `skipped`, counts as **pass** |
| All dimensions missing              | Fail-open                                                              |

### Observer model unavailable

- Startup check in `Gateway._init_observer()`: if `models.observer` not
  available in Ollama, log warning, auto-fallback to `models.planner`,
  set `observer_degraded_mode=True`. This state is stored per-audit
  record.
- If planner model is also unavailable: disable Observer for the
  session, log `observer_disabled_runtime`.

### `AuditStore` (SQLite) failures

| Failure          | Behaviour                                                                |
|------------------|--------------------------------------------------------------------------|
| Disk full        | Log warning, in-memory counter for monitoring, skip write                |
| DB locked        | 3× retry with exponential backoff (50ms → 200ms → 500ms), then skip      |
| DB corrupt       | On startup: move to `observer_audits.broken.db`, recreate fresh, warn    |

Audit write failures never block response delivery.

### Retry budget exhaustion

Three caps, each with its own fallback:

- `observer_retry_count > observer.max_retries` (default 2) → force
  `"deliver_with_warning"`.
- `pge_iteration_count > SecurityConfig.max_iterations` (default 25) →
  Observer-Re-Loop downgrade to Response-Regen (not a new PGE iteration).
- **Circuit breaker**: if the Observer enters fail-open in
  `observer.circuit_breaker_threshold` consecutive calls (default 5),
  disable Observer for the rest of the session. Log
  `observer_circuit_open`. A warning is added to the response envelope.

### Gateway re-loop failures

| Case                                        | Behaviour                                       |
|---------------------------------------------|-------------------------------------------------|
| `pge_iteration_count` at cap                | Downgrade directive → response-regen            |
| Feedback hash already seen (dedupe hit)     | Downgrade → response-regen                      |
| `seen_hashes` set > 100 entries             | Prune to last 50 (bounded memory)               |
| Planner retry raises Exception              | Fail-open: original draft + warning prefix, log |

### Observability

Structured log events with consistent keys:

```python
log.warning("observer_timeout", session_id=..., user_msg_hash=..., duration_ms=..., model=...)
log.error("observer_json_parse_failed", session_id=..., raw_response_head=...)
log.info("observer_circuit_open", session_id=..., consecutive_failures=5)
log.info("observer_degraded_mode", actual_model=..., intended_model=...)
log.debug("observer_audit_recorded", session_id=..., final_action=..., retry_count=...)
```

Audit records always include `error_type` and `degraded_mode` columns
for later dashboard integration.

## Testing

Four layers within the existing pytest setup (`asyncio_mode=auto`).
Target: ≥95% line coverage on `observer.py` and `observer_store.py`.

### Unit tests — `tests/test_core/test_observer.py` (~25 tests)

- **Dimension detection** (3-4 per dimension, ~15 tests total):
    - Hallucination: claim-in-tool / claim-not-in-tool / partial-evidence
    - Sycophancy: direct flattery / hidden flattery / legitimate agreement
    - Laziness: placeholder / vague / would-do instead of did
    - Tool-Ignorance: researchable question without search, calculable without math tool
- **`AuditResult.final_action` logic** (~6 tests):
    - All blocking pass → `"pass"`
    - Hallucination fail + budget available → `"rejected_with_retry"` + `retry_strategy="response_regen"`
    - Tool-Ignorance fail + budget available → `"rejected_with_retry"` + `retry_strategy="pge_reloop"`
    - Both blocking fail → Tool-Ignorance priority wins
    - Retries exhausted → `"delivered_with_warning"`
    - Only advisory fail → `"pass"`
- **Dedupe + counters** (~4 tests):
    - `seen_hashes` prevents doubled PGE-re-loop
    - Circuit breaker after threshold consecutive fails
    - Both counters (observer_retry, pge_iteration) stay within caps

### Integration tests — `tests/test_integration/test_observer_flow.py` (~12 tests)

End-to-end with mocked Ollama (`AsyncMock` for `chat()`):

- Happy-path pass
- Hallucination retry → mock_response_v2 passes → delivery
- Tool-Ignorance PGE-re-loop → new tool call → new response → pass
- Exhausted retries → `warning_prefix` in delivered content
- Observer disabled per config
- Degraded mode (observer model missing, falls back to planner)

### Error-path tests — `tests/test_core/test_observer_errors.py` (~15 tests)

Guards the fail-open contract:

- LLM timeout → response delivered
- Malformed JSON (1× retry then fail-open)
- Missing dimension → partial audit
- All dimensions missing → fail-open
- SQLite disk-full / locked / corrupt
- Observer model unavailable → fallback
- Planner model also unavailable → Observer disabled for session
- Circuit breaker triggered → observer disabled, log, warning in response

### Fixtures — `tests/fixtures/observer_cases.py`

Curated library of `(user_msg, tool_results, draft_response, expected_audit_result)` tuples:
- 20 hallucination cases (subtle to obvious)
- 15 sycophancy cases
- 15 laziness cases
- 15 tool-ignorance cases
- 20 clean cases (negative controls)

Parameterized into unit tests via `@pytest.mark.parametrize`.

### Contract tests with real LLM — `tests/test_reallife/test_observer_live.py` (~8 tests)

Marked with `@pytest.mark.integration`, skipped when Ollama unavailable:

- Precision test: 10 known-bad fixtures against real `qwen3:8b`, expect
  detection rate ≥70%
- Latency budget: 10 calls, max duration per call < 10s (warn > 5s)
- JSON conformance: 20 calls, 100% valid JSON output

### Hypothesis fuzz tests (optional)

```python
@given(response=st.text(alphabet=..., min_size=50, max_size=2000))
@settings(max_examples=50)
def test_observer_never_crashes(observer, response):
    result = await observer.audit(user_msg="test", response=response, tool_results=[])
    assert isinstance(result, AuditResult)
```

Protects the fail-open path against creative inputs.

### CI integration

No new CI step needed — pytest auto-discovers the new test files. The
existing `ci.yml` jobs (lint, test, scripts, flutter) cover this.
Integration-marked contract tests skip in CI by default (no Ollama).

## Implementation order

This spec will be decomposed into an implementation plan next. Rough
order of work:

1. `ObserverConfig` + `ModelsConfig.observer` field — additive, no
   breaking changes yet.
2. Dataclasses (`DimensionResult`, `AuditResult`, `PGEReloopDirective`,
   `ResponseEnvelope`).
3. `AuditStore` — SQLite schema and write path. Tested in isolation.
4. `ObserverAudit` class with mocked LLM calls for unit tests.
5. `planner.formulate_response()` return-type change to
   `ResponseEnvelope`. Update all callers in one commit.
6. Gateway-level directive handling in `gateway/phases/pge.py`.
7. Error-path robustness (circuit breaker, degraded mode, dedupe).
8. Integration tests and fixture library.
9. Contract tests with real LLM (marked for CI skip).
10. Documentation updates (README, CHANGELOG, CONFIG_REFERENCE).

## Open questions (to resolve during implementation)

- Exact prompt text for `_build_prompt()` — needs iteration against
  real LLMs. The spec defines the JSON schema and the dimension
  definitions; the prompt wording is tuning work.
- Precise thresholds for "partial evidence" in the hallucination check —
  does "TechCorp is a software company founded by John" pass if
  tool_results mention both the company type and the founder's name
  but in separate documents? To be codified via fixtures.
- Whether the `warning_prefix` should be markup (`⚠️`) or plain text.
  Plain text is CLI-safer. Default stays plain; UI layers can render
  richer formatting based on the structured `AuditResult` attached to
  the envelope.
