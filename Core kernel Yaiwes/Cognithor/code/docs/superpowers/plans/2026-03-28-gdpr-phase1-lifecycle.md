# GDPR Phase 1: Data Lifecycle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make user rights (erasure, access) technically enforceable. TTL enforcement automated. Delete tools available.

**Architecture:** Extend existing ErasureManager, add vault_delete + entity/relation delete MCP tools, wire RetentionEnforcer into cron, add purpose field to memory operations.

---

### Task 1: vault_delete MCP Tool

**Files:**
- Modify: `src/jarvis/mcp/vault.py`
- Modify: `src/jarvis/core/gatekeeper.py` (add to RED)

Add `vault_delete` method to VaultTools class:

```python
async def vault_delete(self, path: str) -> str:
    """Delete a vault note by path. Returns confirmation or error."""
    full = self._resolve_path(path)
    if not full.exists():
        return f"Note not found: {path}"
    full.unlink()
    return f"Deleted: {path}"
```

Register as MCP handler with RED gatekeeper classification.

Input schema: `{"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}`

---

### Task 2: delete_entity + delete_relation MCP Tools

**Files:**
- Modify: `src/jarvis/mcp/memory_server.py`
- Modify: `src/jarvis/core/gatekeeper.py` (add to RED)

Add to MemoryTools:

```python
def delete_entity(self, name: str) -> str:
    """Delete an entity and all its relations by name."""
    # Delete from indexer
    deleted = self._manager.semantic.delete_entity(name)
    return f"Deleted entity '{name}' and {deleted} relations"

def delete_relation(self, source: str, target: str, relation: str = "") -> str:
    """Delete a specific relation between entities."""
    deleted = self._manager.semantic.delete_relation(source, target, relation)
    return f"Deleted {deleted} relation(s) between '{source}' and '{target}'"
```

If the semantic indexer doesn't have delete methods, add them directly via SQL:
```python
# In the indexer or memory_server directly:
conn.execute("DELETE FROM entities WHERE name = ?", (name,))
conn.execute("DELETE FROM relations WHERE source = ? OR target = ?", (name, name))
```

Register both as MCP handlers with RED gatekeeper classification.

---

### Task 3: Extended Erasure API

**Files:**
- Modify: `src/jarvis/security/gdpr.py` (extend ErasureManager)
- Create: `tests/test_security/test_erasure.py`

Add `erase_all()` method to ErasureManager:

```python
async def erase_all(self, user_id: str, mcp_client=None, memory_manager=None,
                     consent_manager=None, vault_tools=None) -> dict:
    """Delete ALL personal data for user_id across every tier."""
    counts = {}

    # 1. Processing logs
    counts["processing_logs"] = self._processing_log.delete_user_records(user_id) if hasattr(self, "_processing_log") else 0

    # 2. Consent records
    if consent_manager:
        counts["consents"] = consent_manager.delete_user(user_id)

    # 3. Call registered handlers (memory, sessions, etc.)
    for handler in self._handlers:
        try:
            counts[f"handler_{len(counts)}"] = handler(user_id)
        except Exception:
            pass

    return counts
```

Wire into REST endpoint: `DELETE /api/v1/user/data`

Tests:
- test_erase_all_deletes_processing_logs
- test_erase_all_deletes_consents
- test_erase_all_calls_handlers

---

### Task 4: TTL Enforcement Cron Job

**Files:**
- Modify: `src/jarvis/config.py` (add RetentionConfig)
- Modify: `src/jarvis/gateway/gateway.py` (register cron job)

Add RetentionConfig:
```python
class RetentionConfig(BaseModel):
    episodic_days: int = 90
    processing_log_days: int = 90
    him_report_days: int = 30
    session_days: int = 180
```

Register daily cron job `retention_enforcer` at 03:00 that calls:
1. `RetentionEnforcer.enforce()` for processing logs
2. Episodic memory `prune_old(retention_days=90)`
3. Vault OSINT cleanup (delete files in `recherchen/osint/` older than 30 days)

---

### Task 5: REST Endpoints for User Data

**Files:**
- Modify: `src/jarvis/channels/config_routes.py`

Add endpoints:
- `DELETE /api/v1/user/data` — triggers erase_all(), requires auth
- `GET /api/v1/user/data` — exports all user data as JSON

Both require `_verify_cc_token` authentication.
