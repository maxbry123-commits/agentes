# EVIDENCE — PLAN30 T17 DIRECT CODE-ROOT INSPECTION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta concurrency check
- Main HEAD before this evidence delta: `5118c56ff6e87fd93bfb2ab1733076d54fe6bf26`.
- Main tree SHA: `914be68f7a417620edeafbb0c0705385a2653c11`.
- HEAD message: `Persist T17 equivalent-pattern reuse search`.
- This matches the immediately previous T17 research checkpoint; no foreign concurrent mutation was observed before the delta.

## StrategyDelta
Previous indexed searches for `CapabilityRegistry`, `PluginRegistry`, `plugin manager`, `register`, `factory`, `loader`, `slot`, `mount`, and equivalent patterns did not yield a selectable runtime donor. This delta changed method materially: direct inspection of the canonical source code-root already cited by T16/T17 provenance.

## Direct code-root inspected
Repository: `maxbry123-commits/agentes`
Commit: `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`
Path: `skills/research-download-chain/assets/plugin-bus/`
URL: `https://github.com/maxbry123-commits/agentes/tree/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus`

GitHub directory read-back proves this code-root contains exactly one file:
- `ficha_contract_v2.py`
- blob SHA `b27f14b4d64f77bccf53a893c49b6f20bd58e745`
- URL `https://github.com/maxbry123-commits/agentes/blob/37bef3a8a8f6dadca067638b8ea0c32995fc1d63/skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py`

## Refutation / decision
- The canonical `plugin-bus/` code-root at the T16 source commit does **not** contain a Capability Registry runtime, loader, mount guard, adapter/plugin runtime bus, or registry implementation alongside the validator.
- Therefore it is **not** a valid COPY_ONLY donor for the missing T17 registry runtime.
- No code was generated, rewritten, moved, or copied in this delta.
- T17 remains `EN_CURSO`; presence of the `plugin-bus` directory is not treated as integration.

## Evidence outcome
`DIRECT_CODEROOT_REFUTED_AS_T17_REGISTRY_DONOR = PASS`
`T17_VERIFY_FINAL = NOT_RUN`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Inspect the Director-selected source roots recorded in `TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` by exact path/commit rather than indexed keyword search; choose one donor only if it provides executable registry/loader/binding behavior with source blob SHA and a non-duplicating destination. Otherwise persist the next materially distinct refutation and keep T17 open.
