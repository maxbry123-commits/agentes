# Wordflow Kernel Extension — V1

Deterministic control plane for YAIWES / Wordflow. **GitHub is the source of truth.**

## How to connect components

### 1. Intelligence Gateway → Router Universal
```text
Loop / EnginePort
  → IntelligenceGateway (Mock | RouterHTTPGateway)
  → ROUTER_URL HTTP /v1/route
  → LLM providers / tools (outside Wordflow)
```
- Set `ROUTER_URL=https://your-router`
- Never put API keys in workflow YAML; use credential_ref
- File: `gateway/intelligence.py`, `gateway/router_http.py`

### 2. Memory Orchestrator
```text
Workflow
  → MemoryOrchestratorAdapter
  → capability memory.* via Router
  → OR local PersistentMemory (offline only)
```
- File: `memory_slot/adapter.py`
- Local: `memory.py` (append-only jsonl)

### 3. Engines (OpenClaw / Hermes)
```text
EngineRegistry.reason(name, EngineRequest, gateway)
  → OpenClawEngine / HermesEngine stubs
  → always via IntelligenceGateway (no direct vendor)
```
- File: `engines/`
- Acquire software separately via Acquire Recipe (`control-layer/subsheriffs/acquire_os/recipes/openclaw.example.yaml`)

### 4. Continuous loop + 12-stage hooks
```text
GoalLockView → goals_to_loop_state → maxbry_loop.Engine
GoalLockView → goals_to_stage_plan → stages.DeterministicLoopEngine
```
- Package: `extensions/maxbry_loop/`
- Stages: `stages/` (ADMIT…CLOSE)
- Model: `MockModel` or `GatewayModel(gateway)`

### 5. Forensic audit
```text
forensic_audit(target, requirements, claims) → EvidencePacket + recommended_tasks
```
- `forensic_api.py`, `repo_truth.py`, `crosscheck.py`

### 6. GitHub multi-account + deploy
```text
AccountRegistry + AccountResolver → credential_ref
GitDataAPIPort Fake (default) | Real if GITHUB_DEPLOY_REAL=1 and GITHUB_TOKEN
```
- `extensions/wordflow/accounts/`
- `extensions/github_deploy/git_data_port.py`

### 7. HF resources (PLAN_ONLY fetch)
```text
AdapterFactory · SkillLoader · DatasetLoader · SpaceAgentsLoader
FETCH_ENABLED=false by default
```
- `resources/`

### 8. UI plugin
```text
UIGatewayPlugin — mount in OpenClaw webui / chat host
```
- `ui_gateway/`

### 9. Enchufe
- `ficha.v2.json` at package roots; `llm_control: DENY` in kernel paths

## Residual (post V1 / next week)
| ID | Item |
|----|------|
| R2 | Kimi/Minimax fusion loops full code |
| R2 | Real HF/GitHub bulk fetch when policy allows |
| R2 | Full CI green matrix on every module |
| R2 | Real OpenClaw/Hermes binaries via Acquire when enabled |
| R0 | PIPELINE residual detail for next Grok instance |

## Tests
Run offline unit tests under `extensions/wordflow_kernel/tests` and related packages with `python -m unittest`.
