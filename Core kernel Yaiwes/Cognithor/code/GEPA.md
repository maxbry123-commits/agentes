# GEPA -- Guided Evolution through Pattern Analysis

> Cognithor's self-improvement system that analyzes execution traces to automatically identify failure patterns and propose targeted optimizations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [How It Works](#how-it-works)
- [Failure Categories](#failure-categories)
- [Optimization Types](#optimization-types)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Safety Constraints](#safety-constraints)
- [Data Model](#data-model)
- [Examples](#examples)

---

## Overview

GEPA is Cognithor's closed-loop self-improvement system. It records every tool call and decision point during PGE execution cycles, analyzes patterns in successes and failures, identifies root causes, and generates specific, actionable optimization proposals.

The key principle: **improvements are data-driven, not speculative**. GEPA only proposes changes after observing statistically significant patterns across multiple traces.

```
User Message
    |
    v
PGE Loop (Planner -> Gatekeeper -> Executor)
    |
    v
ExecutionTrace recorded (every tool call, duration, success/failure)
    |
    v
[Periodic] CausalAttributor analyzes traces -> finds root causes
    |
    v
[Periodic] TraceOptimizer generates proposals from findings
    |
    v
[Manual/Auto] EvolutionOrchestrator applies best proposal
    |
    v
[Automatic] Monitor for degradation -> auto-rollback if needed
```

---

## Architecture

GEPA lives in `src/jarvis/learning/` and consists of four core modules:

```
learning/
  execution_trace.py     # TraceStep, ExecutionTrace, TraceStore (SQLite)
  causal_attributor.py   # CausalAttributor: root-cause analysis
  trace_optimizer.py     # TraceOptimizer, ProposalStore, OptimizationProposal
  evolution_orchestrator.py  # EvolutionOrchestrator: full cycle management
```

The system is wired into the Gateway during startup (phase: `advanced`) and runs evolution cycles on a configurable schedule.

---

## Components

### ExecutionTrace (`execution_trace.py`)

Records every PGE execution cycle as a trace:

- **TraceStep**: A single tool call or decision point.
  - `step_id`, `parent_id` (for causal chains), `tool_name`
  - `input_summary`, `output_summary` (capped at 500 chars)
  - `status`: `"success"`, `"error"`, `"skipped"`, `"timeout"`
  - `error_detail`, `duration_ms`, `metadata`

- **ExecutionTrace**: Complete trace of one user message -> response cycle.
  - `trace_id`, `session_id`, `goal`
  - `steps`: list of TraceStep
  - `total_duration_ms`, `success_score` (0.0-1.0), `model_used`
  - Derived: `failed_steps`, `tool_sequence`, `get_causal_chain(step_id)`

- **TraceStore**: SQLite persistence with WAL mode.
  - `save_trace()`, `get_trace()`, `get_traces_since(timestamp)`
  - `get_failed_traces(since_hours=24)`, `get_trace_stats(since_hours=24)`
  - `delete_old_traces(older_than_days=30)` -- automatic cleanup

### CausalAttributor (`causal_attributor.py`)

Pure heuristic/graph-based root-cause analysis. No LLM calls, no I/O.

**Algorithm for each trace:**
1. Find all failed steps (status = `"error"` or `"timeout"`)
2. Walk up the `parent_id` chain to find the root cause (first failure in chain)
3. Classify the failure category using keyword heuristics on `error_detail`
4. Count downstream affected steps (BFS from root cause)
5. Compute confidence score based on chain clarity

**Confidence scoring:**
- Single-step failure: 0.9 (clear root cause)
- Chain with one identifiable root: 0.7
- Ambiguous chain (multiple failures): 0.5
- Cascade failure: 0.4

Aggregation groups findings by `(failure_category, tool_name, error_signature)` and ranks by priority = count x avg_confidence.

### TraceOptimizer (`trace_optimizer.py`)

Generates specific, actionable optimization proposals from causal findings.

Each failure category maps to a specialized handler that produces a proposal:

| Category | Handler | Typical Proposal |
|----------|---------|------------------|
| timeout | `_propose_for_timeout` | Increase timeout, add retry with backoff |
| wrong_tool_choice | `_propose_for_wrong_tool` | Add tool selection guidance to planner prompt |
| bad_parameters | `_propose_for_bad_params` | Add input validation and defaults |
| hallucination | `_propose_for_hallucination` | Add verification guardrail |
| missing_context | `_propose_for_missing_context` | Add pre-execution context lookup |
| cascade_failure | `_propose_for_cascade` | Add fallback strategy, limit cascade depth |
| permission_denied | `_propose_for_permission` | Evaluate gatekeeper allowlist update |
| rate_limited | `_propose_for_rate_limit` | Add caching and backoff |
| parse_error | `_propose_for_parse_error` | Add robust output parsing |

If an LLM client is available, proposals are enhanced with LLM-generated patches. Otherwise, template-based fallbacks are used.

**ProposalStore**: SQLite persistence for proposals with full lifecycle tracking (proposed -> applied -> rolled_back/rejected).

### EvolutionOrchestrator (`evolution_orchestrator.py`)

Manages the full GEPA lifecycle. Runs evolution cycles either on schedule or on demand.

**Each cycle:**
1. Collect traces since last cycle (or last 24h if first run)
2. Skip if fewer than `min_traces` (default: 10)
3. Evaluate currently applied proposals (auto-rollback if degraded)
4. Run causal analysis on recent traces
5. Identify improvement targets
6. Generate proposals via TraceOptimizer
7. If `auto_apply=True` and best proposal confidence >= 0.6, apply it
8. Return cycle result with statistics

---

## How It Works

### Phase 1: Trace Collection

During every PGE loop iteration, the Gateway records a `TraceStep` for each tool call:

```
User: "What's the weather in Berlin?"
  Step 1: planner -> plan (success, 450ms)
  Step 2: web_search -> "weather Berlin" (success, 1200ms)
  Step 3: formulate_response -> answer (success, 800ms)
  Total: 2450ms, success_score: 0.95
```

### Phase 2: Causal Analysis

The CausalAttributor processes accumulated traces:

```
Trace A: web_search -> timeout (3x in 24h)
Trace B: web_search -> timeout, downstream formulate_response -> error
Trace C: web_search -> success (but slow: 4500ms)

Finding: {
  failure_category: "timeout",
  tool_name: "web_search",
  count: 3,
  avg_confidence: 0.83,
  priority: 2.49
}
```

### Phase 3: Proposal Generation

The TraceOptimizer creates a proposal:

```
OptimizationProposal {
  optimization_type: "tool_param",
  target: "web_search.timeout_config",
  description: "Tool 'web_search' is timing out frequently (avg 4.5s).
                Increase timeout to 12s and add retry logic.",
  patch_before: "web_search.timeout = default",
  patch_after: "Set web_search.timeout = 12s. Add retry with exponential
                backoff: max_retries=2, base_delay=2s, max_delay=10s.",
  confidence: 0.75,
  estimated_impact: 0.12
}
```

### Phase 4: Application and Monitoring

When a proposal is applied (manually or via `auto_apply`):
1. Current metrics are captured as `metrics_before`
2. The proposal is marked as "applied" with a timestamp
3. After 5+ subsequent sessions, metrics are compared
4. If success rate drops > 10%, automatic rollback is triggered

---

## Failure Categories

GEPA classifies failures into 10 categories:

| Category | Description | Detection Method |
|----------|-------------|------------------|
| `timeout` | Tool exceeded time limit | Keywords: "timeout", "timed out", "deadline" |
| `wrong_tool_choice` | Planner selected wrong tool | Parent is planner + child failed |
| `bad_parameters` | Incorrect or missing parameters | Keywords: "parameter", "argument", "missing", "invalid" |
| `hallucination` | Factually incorrect output | Keywords: "incorrect", "wrong"; planner tools |
| `missing_context` | Insufficient context | Default category for unclassified failures |
| `tool_unavailable` | Tool not registered or available | Keywords: "not found", "not registered" |
| `cascade_failure` | Upstream failure caused downstream failures | Parent step also failed |
| `permission_denied` | Gatekeeper blocked the operation | Keywords: "blocked", "denied", "gatekeeper" |
| `rate_limited` | External API rate limit hit | Keywords: "rate limit", "429", "too many" |
| `parse_error` | Failed to parse output | Keywords: "json", "parse", "decode", "syntax" |

---

## Optimization Types

Proposals fall into 6 optimization types:

| Type | Description | Typical Target |
|------|-------------|----------------|
| `prompt_patch` | Modify planner or executor system prompt | `planner.system_prompt` |
| `tool_param` | Adjust tool defaults or validation | `{tool}.timeout_config`, `{tool}.params` |
| `strategy_change` | Change tool selection or execution strategy | `planner.system_prompt` |
| `new_procedure` | Add procedural memory entry | `procedure.{tool}_error_handling` |
| `guardrail` | Add gatekeeper rule | `gatekeeper.rules`, `gatekeeper.green_list` |
| `context_enrichment` | Add context pipeline step | `procedure.context_enrichment` |

---

## Configuration

In `~/.jarvis/config.yaml`:

```yaml
gepa:
  enabled: false                    # Opt-in (default: off)
  evolution_interval_hours: 6       # Run cycle every N hours (1-168)
  min_traces_for_proposal: 10      # Min traces before generating proposals (3-100)
  max_active_optimizations: 1      # Max simultaneously applied proposals (1-3)
  auto_rollback_threshold: 0.10    # Auto-rollback if success drops >10% (0.01-0.5)
```

Additional constants in `EvolutionOrchestrator`:

| Constant | Value | Description |
|----------|-------|-------------|
| `MIN_CONFIDENCE` | 0.6 | Minimum confidence for auto-apply |
| `MIN_SESSIONS_FOR_EVAL` | 5 | Sessions before evaluating applied proposal |
| `_MAX_CYCLE_HISTORY` | 100 | Cycle results kept in memory |
| `auto_apply` | `False` | Set to True for fully autonomous operation |

---

## API Endpoints

All endpoints require Bearer token authentication.

### Status

```
GET /api/v1/evolution/status
```

Returns:
```json
{
  "enabled": true,
  "auto_apply": false,
  "last_cycle": 1710842400.0,
  "cycles_completed": 12,
  "active_proposals": 1,
  "pending_proposals": 3,
  "total_applied": 5,
  "total_rolled_back": 1,
  "total_rejected": 2,
  "recent_success_rate": 0.87,
  "improvement_trend": 0.03,
  "top_issues": [...]
}
```

### Proposals

```
GET  /api/v1/evolution/proposals                         # List all (or filter: ?status=proposed)
GET  /api/v1/evolution/proposals/{proposal_id}           # Detail view
POST /api/v1/evolution/proposals/{proposal_id}/apply     # Apply a proposal
POST /api/v1/evolution/proposals/{proposal_id}/reject    # Reject a proposal
POST /api/v1/evolution/proposals/{proposal_id}/rollback  # Rollback an applied proposal
```

### Traces

```
GET /api/v1/evolution/traces?limit=20    # Recent execution traces
```

### Manual Cycle

```
POST /api/v1/evolution/run    # Trigger an evolution cycle manually
```

Returns:
```json
{
  "cycle_id": "a1b2c3d4e5f6",
  "traces_analyzed": 47,
  "findings_count": 5,
  "proposals_generated": 2,
  "proposal_applied": null,
  "auto_rollbacks": 0,
  "duration_ms": 340
}
```

---

## Safety Constraints

GEPA is designed with multiple safety layers:

1. **Max 1 active optimization** (`max_active_optimizations=1`): Only one proposal can be applied at a time, preventing compounding changes that make root-cause analysis impossible.

2. **Minimum 10 traces** (`min_traces_for_proposal=10`): No proposals are generated until enough data exists to identify statistically meaningful patterns.

3. **Auto-rollback on degradation**: After applying a proposal, if the success rate drops by more than 10% over 5+ subsequent sessions, the proposal is automatically rolled back.

4. **All changes are logged and reversible**: Every proposal records `patch_before` and `patch_after`, along with `metrics_before` and `metrics_after`. Nothing is destructive.

5. **Manual review by default**: `auto_apply` is `False` by default. Proposals are generated but require manual approval via the API or dashboard.

6. **Confidence threshold**: Even with `auto_apply=True`, only proposals with confidence >= 0.6 are automatically applied.

7. **Cycle history**: The last 100 cycle results are kept for audit and trend analysis.

---

## Data Model

### SQLite Tables

**execution_traces**:
```sql
trace_id TEXT PRIMARY KEY
session_id TEXT NOT NULL
goal TEXT NOT NULL
success_score REAL DEFAULT 0.0
model_used TEXT DEFAULT ''
total_duration_ms INTEGER DEFAULT 0
created_at REAL NOT NULL
```

**trace_steps**:
```sql
step_id TEXT PRIMARY KEY
trace_id TEXT NOT NULL REFERENCES execution_traces(trace_id) ON DELETE CASCADE
parent_id TEXT
seq INTEGER NOT NULL
tool_name TEXT NOT NULL
input_summary TEXT DEFAULT ''
output_summary TEXT DEFAULT ''
status TEXT NOT NULL DEFAULT 'success'
error_detail TEXT DEFAULT ''
duration_ms INTEGER DEFAULT 0
ts REAL NOT NULL
metadata_json TEXT DEFAULT '{}'
```

**optimization_proposals**:
```sql
proposal_id TEXT PRIMARY KEY
finding_id TEXT NOT NULL
optimization_type TEXT NOT NULL
target TEXT NOT NULL
description TEXT NOT NULL
patch_before TEXT DEFAULT ''
patch_after TEXT DEFAULT ''
estimated_impact REAL DEFAULT 0.0
confidence REAL DEFAULT 0.0
failure_category TEXT DEFAULT ''
tool_name TEXT DEFAULT ''
evidence_trace_ids_json TEXT DEFAULT '[]'
status TEXT DEFAULT 'proposed'
applied_at REAL DEFAULT 0.0
metrics_before_json TEXT DEFAULT '{}'
metrics_after_json TEXT DEFAULT '{}'
created_at REAL DEFAULT 0.0
```

### Proposal Lifecycle

```
proposed  ->  applied  ->  rolled_back
                       ->  rejected (manual)
          ->  rejected (manual, before apply)
```

---

## Examples

### Viewing Current Status

```bash
curl -s http://localhost:8741/api/v1/evolution/status \
  -H "Authorization: Bearer <token>" | jq .
```

### Triggering a Manual Cycle

```bash
curl -X POST http://localhost:8741/api/v1/evolution/run \
  -H "Authorization: Bearer <token>" | jq .
```

### Reviewing and Applying a Proposal

```bash
# List pending proposals
curl -s "http://localhost:8741/api/v1/evolution/proposals?status=proposed" \
  -H "Authorization: Bearer <token>" | jq '.proposals[] | {proposal_id, description, confidence}'

# Apply the best one
curl -X POST http://localhost:8741/api/v1/evolution/proposals/<proposal_id>/apply \
  -H "Authorization: Bearer <token>"
```

### Rolling Back

```bash
curl -X POST http://localhost:8741/api/v1/evolution/proposals/<proposal_id>/rollback \
  -H "Authorization: Bearer <token>"
```
