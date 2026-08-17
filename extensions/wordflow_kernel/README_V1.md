# Wordflow Kernel Extension — V1

Deterministic control plane for YAIWES / Wordflow. **GitHub is the source of truth for system code.**

## Multi-account storage (método de trabajo)

```
Cuenta A (sistema)  →  este monorepo + router + osquestador + memoria
Cuenta B (software) →  forks / tools / agents externos (solo almacén)
HF                  →  datasets / models / skills grandes
Runtime             →  donde se ejecuta tras download + verify
```

- Full method: `PIPELINE/53_MULTI_ACCOUNT_STORAGE_METHOD.md`
- Connector: `extensions/wordflow/connectors/github_external.py`
- Accounts: `extensions/wordflow/accounts/` — **credential_ref only, never raw token in git**

When the Director enables Cuenta B, set env from secret store and register:

```yaml
account_id: external_software_b
provider: github
credential_ref: env:GITHUB_EXTERNAL_B_TOKEN
allowed_repositories:
  - abc1tienda-web/REPO_NAME
policy: { can_read: true, can_write: false, can_deploy: false }
```

## How to connect components

### 1. Intelligence Gateway → Router Universal
```text
Loop / EnginePort
  → IntelligenceGateway (Mock | RouterHTTPGateway)
  → ROUTER_URL HTTP /v1/route
```
- Files: `gateway/intelligence.py`, `gateway/router_http.py`

### 2. Memory Orchestrator
```text
Workflow → MemoryOrchestratorAdapter → memory.* via Router | local PersistentMemory
```
- `memory_slot/adapter.py`, `memory.py`

### 3. Engines (OpenClaw / Hermes)
```text
EngineRegistry.reason → stubs → always via IntelligenceGateway
```
- `engines/` — software binaries via Acquire + optional Cuenta B repos

### 4. Continuous loop + 12-stage
- `extensions/maxbry_loop/` + `stages/`

### 5. Forensic audit
- `forensic_api.py`, `repo_truth.py`, `crosscheck.py`

### 6. GitHub multi-account + deploy + external software
```text
AccountRegistry + AccountResolver
  → system deploy (Cuenta A write)
  → external read (Cuenta B credential_ref)
GitDataAPIPort Fake | Real under flags
```

### 7. HF resources (PLAN_ONLY default)
- `resources/` — FETCH_ENABLED=false by default

### 8. UI plugin
- `ui_gateway/`

### 9. Enchufe
- `ficha.v2.json`; `llm_control: DENY` on deterministic kernel paths

## Residual post V1
Kimi/Minimax fusion full · bulk fetch · full CI matrix · real engine binaries when Acquire ON

## Tests
`python -m unittest` under package `tests/` offline.
