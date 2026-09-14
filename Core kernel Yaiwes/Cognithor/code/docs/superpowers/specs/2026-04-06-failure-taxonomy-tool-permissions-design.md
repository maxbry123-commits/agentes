# V3+V6: Failure-Taxonomy + Recovery Recipes + Per-Tool Permission Annotations

> **Goal:** Classify every runtime failure into a structured taxonomy with automatic recovery recipes, and annotate tools with risk levels at registration time instead of hardcoded Gatekeeper lists.

## V3: Failure-Taxonomy + Recovery Recipes

### New Module: `src/jarvis/core/recovery.py`

**FailureClass** — 8 categories covering all Cognithor failure modes:
- `LLM_TIMEOUT` — LLM provider didn't respond
- `LLM_CONNECTION` — Can't reach LLM provider
- `LLM_RATE_LIMIT` — Provider rate-limited
- `TOOL_RUNTIME` — MCP tool threw an exception
- `TOOL_TIMEOUT` — Tool execution timed out
- `GATEKEEPER_BLOCK` — Action blocked by security
- `MCP_ERROR` — MCP server/handshake failure
- `INFRA` — Disk, memory, network infrastructure

**RecoveryStep** — atomic recovery actions:
- `RETRY` — Retry the same operation
- `SWITCH_PROVIDER` — Try alternate LLM backend
- `CLEAR_CACHE` — Clear relevant caches
- `RESTART_MODULE` — Restart the failed MCP module
- `ESCALATE_TO_USER` — Inform user, stop retrying

**RecoveryRecipe** — ordered steps per failure class with max attempts and escalation.

**RecoveryEngine** — classifies exceptions into FailureClass, executes recipe steps, returns structured RecoveryResult.

### Integration
- Wraps the existing retry logic in `Executor._execute_single()`
- Executor calls `RecoveryEngine.classify()` on exception
- Recovery steps run before falling through to existing retry/escalation

## V6: Per-Tool Permission Annotations

### Changes to MCPToolInfo
Add `risk_level: str = "green"` field to MCPToolInfo in models.py.

### Changes to register_builtin_handler
Add optional `risk_level` parameter. Default: `"green"`.

### Changes to Gatekeeper._classify_risk()
1. First check `tool_registry[tool_name].risk_level` if available
2. Fall back to existing hardcoded lists (backwards compat)
3. Log when using fallback (helps track unannotated tools)

### Tool Annotation
Annotate all 122+ tools at their registration sites with explicit risk_level.
This is done gradually — existing hardcoded lists remain as fallback.

## Files

| File | Action |
|------|--------|
| `src/jarvis/core/recovery.py` | CREATE — FailureClass, RecoveryStep, RecoveryRecipe, RecoveryEngine |
| `src/jarvis/models.py` | MODIFY — Add risk_level to MCPToolInfo |
| `src/jarvis/mcp/client.py` | MODIFY — Accept risk_level in register_builtin_handler |
| `src/jarvis/core/gatekeeper.py` | MODIFY — Check tool registry for risk_level first |
| `tests/test_recovery.py` | CREATE — Recovery engine tests |
| `tests/test_tool_permissions.py` | CREATE — Permission annotation tests |
