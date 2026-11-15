# EVIDENCE — PLAN30 T17 RUNTIME CONN/AGENT REFUTATION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta reconciliation
- Main HEAD before write: `5508832ace25f691321342861e4f858baa719516`.
- STATE current node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`.
- PLAN: T01–T16 `VERIFIED_CLOSED`; T17 `EN_CURSO`; T18–T30 `PENDIENTE`.
- Recovery requires RESEARCH_REUSE before generation and forbids reopening T16.
- Architecture requires separated `contracts/adapters/plugins/registry/loader/guards/tests` and no PASS by presence.

## StrategyDelta inspected
Repository: `maxbry123-commits/agentes`
Ref: `5508832ace25f691321342861e4f858baa719516`

### `runtime/src/conn/`
Observed files:
- `manager.py` blob `3fc12e6f2c161c63ebcddb79bd50ab37e143e797`
- `rate_limit.py` blob `f4c67b17987c4ddab2e5c66ddaaa5e394660962d`
- `secrets.py` blob `8aef0987fbcfc1ccda20bac02463298f9db7c4c1`

Direct read-back of `manager.py` shows `ConnectionManager` with an in-memory `registry` and `register_connection()` for supported external providers (`github`, `pypi`, `huggingface`, `aws`, `vault`) plus `preflight_check()`. This is a connection registry, not a Capability Registry/plugin registry: it does not register Ficha modules, adapters/plugins, slots, loader/mount_guard bindings, or plugin runtime handoff.

### `runtime/src/agent/`
Observed file:
- `agent_router.py` blob `90e98ca8a53c89abac16453176f54f20e9efe82c`

Direct read-back shows `AgentRouter.DEFAULT_REGISTRY`, a static list of agent capability metadata used only to choose an agent deterministically. It does not implement plugin registration, dynamic capability binding, loader/mount_guard, Ficha validation, or registry slot lifecycle.

## Refutation / decision
- Both inspected roots contain registry-like data structures, but neither satisfies the literal T17 requirement `adapter/plugin → registry` for reusable Capability Registry runtime.
- Reusing either as T17 registry would conflate connection/agent routing with plugin capability lifecycle and would violate the non-monolithic separation requirement.
- No code was moved, rewritten, generated, or copied.
- No vendor source was modified.
- T16 remains untouched and closed.
- T17 remains `EN_CURSO` / GAP; `verify_final` not run.

## Evidence outcome
`CONN_MANAGER_REGISTRY_SCOPE_CHECK = PASS_REFUTED_AS_T17_DONOR`
`AGENT_ROUTER_REGISTRY_SCOPE_CHECK = PASS_REFUTED_AS_T17_DONOR`
`NO_DUPLICATE_REGISTRY_CREATED = PASS`
`NO_FORCE_GIT = PASS`
`T17_VERIFY_FINAL = NOT_RUN`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Inspect the canonical `TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` selected/reference donor roots for a registry/loader/binding implementation by exact repo+ruta+commit/blob. Choose one donor only if it implements plugin/capability lifecycle and has a non-duplicating destination; otherwise persist the next materially distinct refutation and keep T17 open.
