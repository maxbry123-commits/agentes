# EVIDENCE — PLAN30 T17 RUNTIME INSTALL REFUTATION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta concurrency check
- Main HEAD before delta: `761470ba25e8017055516a08eaa6542712107622`.
- HEAD message: `Persist T17 direct code-root inspection evidence`.
- No newer main commit was observed immediately before this write.

## StrategyDelta
The previous delta inspected the canonical `skills/research-download-chain/assets/plugin-bus/` code-root and refuted it as a registry donor. This delta changed inspection target to the existing Wordflow YAIWES runtime itself to prevent duplicate/parallel registry creation.

## Physical runtime inspected
Repository: `maxbry123-commits/agentes`
Ref: `main` at pre-delta HEAD `761470ba25e8017055516a08eaa6542712107622`
Runtime root: `➡️📂 Wordflow LOOP Yaiwes/runtime/`
Observed top-level runtime objects: `docs/`, `plugin-manifest.yaml`, `src/`, `tests/`.

`runtime/src/` contains subsystem directories including `agent`, `conn`, `core`, `governance`, `install`, `mission`, `observability`, `parallel`, `preflight`, `recovery`.

`runtime/src/core/` contains only:
- `dag_engine.py` blob `ed4361e9e2ca93e6744f9946d2334bf55b3ef63a`
- `event_bus.py` blob `fa2f5f5dd45b158d099d802b5f59b73dc6c9700a`
- `kernel.py` blob `805a9531782ef055002c8f783829fbfcbb383642`
- `state_machine.py` blob `d5c1454a008a043609bececdb9ff8b4300f2c57d`

`runtime/src/install/` contains only:
- `installation_engine.py` blob `af525da2cf3409a30fe2633c934d8ccb45cbda50`

Direct read-back of `installation_engine.py` proves it implements a 12-state installation FSM and returns generated health/Ficha metadata; it does **not** implement Capability Registry, plugin registration, loader, slot binding, or mount_guard behavior.

## Refutation / decision
- Current Wordflow runtime contains a plugin manifest and several runtime subsystems, but the inspected core/install roots do not demonstrate the missing T17 Capability Registry runtime.
- `installation_engine.py` is not a valid COPY_ONLY donor for T17.
- No registry/bus was generated, no existing runtime was moved, and no vendor code was modified.
- T17 remains `EN_CURSO`; presence of `plugin-manifest.yaml` is not counted as runtime binding.

## Evidence outcome
`CURRENT_RUNTIME_DUPLICATE_GUARD = PASS`
`INSTALLATION_ENGINE_REFUTED_AS_T17_DONOR = PASS`
`T17_VERIFY_FINAL = NOT_RUN`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Inspect `runtime/src/conn/` and `runtime/src/agent/` by direct tree/read-back for executable registration/binding/loader behavior. Select a donor only if path + blob SHA + behavior + non-duplicating destination are demonstrated; otherwise persist the next materially distinct refutation and keep T17 open.
