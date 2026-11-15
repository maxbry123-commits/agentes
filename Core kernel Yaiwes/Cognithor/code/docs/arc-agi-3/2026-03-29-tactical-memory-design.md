# Tactical Memory (Tier 6) — Design Specification

**Version:** 1.0
**Date:** 2026-03-29
**Status:** Approved

---

## Goal

Add a 6th memory tier to Cognithor's cognitive memory system that tracks action-to-effect causal relationships in real-time. Unlike existing tiers, Tactical Memory learns which tools work best in which contexts, detects repeated failures, and injects this knowledge into both the Planner (via Context Pipeline) and the Executor (via pre-execution checks).

## Architecture Decisions

1. **Hybrid Persistence** — Hot data in RAM (<1ms access), periodic flush to SQLite for high-confidence insights (confidence > 0.7). Loads persisted data on startup.
2. **Dual Integration** — Context Pipeline injects strategic insights for the Planner; Executor uses tactical data for pre-execution avoidance checks and records outcomes post-execution.
3. **Adaptive Feedback** — Success/fail + duration + replan-detection. Auto-creates avoidance rules after 3 consecutive failures of the same tool+context. Rules decay after 24h TTL.

## Data Structures

### ToolOutcome (dataclass)
- tool_name: str
- params_hash: str (MD5 of sorted params, first 12 chars)
- success: bool
- duration_ms: int
- context_hash: str (MD5 of user message, first 12 chars)
- timestamp: float
- error_snippet: str | None (first 100 chars of error)
- caused_replan: bool = False

### ToolEffectiveness (in-memory dict per tool)
- total: int
- successes: int
- failures: int
- avg_duration_ms: float
- consecutive_failures: int (resets on success)
- last_success_at: float | None
- last_failure_at: float | None
- contexts_succeeded: set[str] (context hashes where tool worked)
- contexts_failed: set[str] (context hashes where tool failed)

### AvoidanceRule (dataclass)
- tool_name: str
- params_pattern: str | None (specific param hash, or None for all params)
- context_pattern: str | None
- reason: str
- created_at: float
- expires_at: float (created_at + TTL, default 24h)
- trigger_count: int (how many failures triggered this)

## TacticalMemory Class API

```python
class TacticalMemory:
    def __init__(self, db_path: Path, ttl_hours: float = 24.0, flush_threshold: float = 0.7)

    # Recording
    def record_outcome(self, tool: str, params: dict, success: bool,
                       duration_ms: int, context: str, error: str | None = None,
                       caused_replan: bool = False) -> None

    # Querying
    def get_tool_effectiveness(self, tool: str) -> float  # 0.0-1.0
    def get_best_tool_for_context(self, context: str, candidates: list[str]) -> str | None
    def check_avoidance(self, tool: str, params: dict) -> AvoidanceRule | None
    def get_insights_for_llm(self, context: str, max_chars: int = 400) -> str

    # Lifecycle
    def flush_to_db(self) -> int  # returns count of flushed records
    def load_from_db(self) -> int  # returns count of loaded records
    def decay_rules(self) -> int  # removes expired rules, returns count
    def close(self) -> None

    # Stats
    def get_stats(self) -> dict
```

## Integration Points

### 1. MemoryTier Enum (models.py)
Add `TACTICAL = "tactical"` after `WORKING = "working"`.

### 2. MemoryManager (memory/manager.py)
- Initialize TacticalMemory after WorkingMemoryManager
- Load persisted data on startup
- Flush + close in close() methods

### 3. Context Pipeline (core/context_pipeline.py)
After Wave 2, inject tactical insights:
```python
# Wave 3: Tactical insights
if tactical_memory:
    tactical_text = tactical_memory.get_insights_for_llm(msg.text)
    if tactical_text:
        wm.injected_tactical = tactical_text  # new field on WorkingMemory
```

### 4. Working Memory (memory/working.py)
- New budget category: `budget_tactical_insights: int = 400`
- New field: `injected_tactical: str = ""`
- Include in build_context_parts() output

### 5. Executor (core/executor.py)
After tool execution (line ~309-318), record outcome:
```python
if tactical_memory:
    tactical_memory.record_outcome(
        tool=action.tool,
        params=action.params,
        success=result.success,
        duration_ms=result.duration_ms,
        context=session_context.last_user_message,
        error=result.content if not result.success else None,
    )
```

### 6. Config (config.py)
```python
class TacticalMemoryConfig(BaseModel):
    enabled: bool = Field(default=True)
    db_name: str = Field(default="tactical_memory.db")
    ttl_hours: float = Field(default=24.0, ge=1.0, le=168.0)
    flush_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
    max_outcomes: int = Field(default=50_000)
    avoidance_consecutive_failures: int = Field(default=3, ge=2, le=10)
    budget_tokens: int = Field(default=400, ge=100, le=2000)
```

## SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS tool_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    params_hash TEXT,
    success INTEGER NOT NULL,
    duration_ms INTEGER,
    context_hash TEXT,
    error_snippet TEXT,
    caused_replan INTEGER DEFAULT 0,
    timestamp REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_effectiveness (
    tool_name TEXT PRIMARY KEY,
    total INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    avg_duration_ms REAL DEFAULT 0,
    effectiveness REAL DEFAULT 0.5,
    last_updated REAL
);

CREATE TABLE IF NOT EXISTS avoidance_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    params_pattern TEXT,
    context_pattern TEXT,
    reason TEXT NOT NULL,
    trigger_count INTEGER DEFAULT 3,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outcomes_tool ON tool_outcomes(tool_name);
CREATE INDEX IF NOT EXISTS idx_outcomes_ts ON tool_outcomes(timestamp);
CREATE INDEX IF NOT EXISTS idx_avoidance_tool ON avoidance_rules(tool_name);
```

## Avoidance Rule Lifecycle

1. Tool X fails → consecutive_failures++ for tool X
2. consecutive_failures >= 3 → create AvoidanceRule(tool_name=X, expires_at=now+24h)
3. Context Pipeline injects: "WARNUNG: tool X hat 3x versagt in aehnlichem Kontext"
4. Executor pre-check: if check_avoidance(tool, params) → log warning (does NOT block)
5. After 24h: decay_rules() removes expired rule
6. If tool X succeeds: consecutive_failures resets to 0, active rule removed

## LLM Insight Format

```
Taktische Einsichten:
  search_and_read: 92% Erfolg (24 Aufrufe), bevorzugen fuer Fakten
  web_search: 67% Erfolg (12 Aufrufe)
  exec_command: 45% Erfolg (9 Aufrufe), haeufig Timeout
  WARNUNG: vault_update hat 3x versagt (letzte 2h) — pruefen
```

## Files

### Create
- `src/jarvis/memory/tactical.py`
- `tests/test_memory/test_tactical.py`

### Modify
- `src/jarvis/models.py` — add TACTICAL to MemoryTier
- `src/jarvis/memory/manager.py` — init + close tactical
- `src/jarvis/memory/working.py` — budget + injected_tactical field
- `src/jarvis/core/context_pipeline.py` — Wave 3 injection
- `src/jarvis/core/executor.py` — post-execution recording
- `src/jarvis/config.py` — TacticalMemoryConfig

## Not In Scope

- No automatic tool-switching in Executor (too dangerous)
- No Gatekeeper changes
- No new MCP tools
- No UI changes
- No Flutter integration
