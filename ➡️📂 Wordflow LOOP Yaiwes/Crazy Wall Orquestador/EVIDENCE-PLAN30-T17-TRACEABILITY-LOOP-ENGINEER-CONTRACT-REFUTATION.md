# EVIDENCE — PLAN30 T17 TRACEABILITY LOOP ENGINEER CONTRACT REFUTATION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta reconciliation
- Main HEAD before write: `930b89011e65dae1a8b0ae57e58c4cc032c21f0e`.
- Crazy Wall directory at that HEAD preserves STATE.json blob `f2ebd5931676c7afd285438603785a723ca5d260`, CHECKPOINT.json blob `414a16d0b43206fbe01dcf6aa677c20dfeb79539`, PLAN-LOOP-30-TAREAS.md blob `185986bfdd6dea4cf9e9beeb85e5c68f171e8324`, RECOVERY-PATCH.md blob `c51d5eb026c8fd309408d342ccd973abc1caa2fa`, BITACORA-CRAZY-WALL.md blob `50f410deb307c1b5b81617a4d30c4ab685bc6579`, and TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md blob `2b8e1cc91ea01d5a87fddf163c6316a0c16378a8`.
- Prior T17 evidence selected `Loop Engineer/Loop-Engineer/loop/contract.py` as the next exact RESEARCH_REUSE candidate after refuting `loop/runtime.py`.
- T16 remains untouched and `VERIFIED_CLOSED`; this delta does not reopen or rewrite verified work.

## Candidate inspected
Repository: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
Repository commit/ref: `0ca97d7c7e8a2e20e986d18e273c6171a2684d30`
Path: `Loop Engineer/Loop-Engineer/loop/contract.py`
Blob: `d17350025b5263db8ec0eeffba02e00febc87df8`
URL: `https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/0ca97d7c7e8a2e20e986d18e273c6171a2684d30/Loop%20Engineer/Loop-Engineer/loop/contract.py`
Required T17 function: runtime Capability Registry implementing Ficha/plugin registration, slot/binding lifecycle, loader/mount-guard handoff, and registry→router/handoff integration.

## Direct blob read-back
The exact blob was read successfully. Its responsibilities are contract validation and evidence integrity: manifest/state/tasks/terminal schema checks, YAML/JSON parsing, lifecycle validation, verification-surface checks, optional repair/rollout/receipt/evidence record validation, chain-bound evidence checks, strict success evidence rules, and doctor reporting.

The file imports/uses FSM, chain, completion, paths, evidence, verifier and runtime event-store helpers. It validates existing loop contracts and evidence; it does not implement a plugin lifecycle registry.

Direct repository code search for `plugin` returned zero results at the inspected repository default/current search surface.

Not demonstrated in this donor:
- Ficha Contract v2 plugin registration;
- capability/plugin registry entries or slots;
- adapter/plugin activation lifecycle;
- registry lookup/binding to runtime components;
- plugin loader;
- mount_guard;
- registry→router/handoff wiring.

## Decision
`DECISION = REFERENCE_ONLY / REJECT_AS_T17_REGISTRY_DONOR`

Reason: `contract.py` is valuable as a fail-closed contract/evidence validator, but copying it as the T17 registry would conflate validation/evidence semantics with plugin lifecycle and violate modular separation. Presence of strong contract checks is not evidence of runtime registration/binding.

No donor source was modified or moved. No destination runtime code was copied/generated. No vendor source changed. No duplicate registry or monolith was created. `verify_final` is not applicable because functional-fit failed before COPY_ONLY.

## Evidence outcome
`SOURCE_BLOB_READ_BACK = PASS`
`SOURCE_PROVENANCE = PASS`
`CONTRACT_VALIDATION_FUNCTION = PASS`
`T17_REGISTRY_FUNCTIONAL_FIT = FAIL`
`NO_COPY_ON_FAILED_FIT = PASS`
`NO_DUPLICATE_REGISTRY_CREATED = PASS`
`NO_MONOLITH = PASS`
`NO_FORCE_GIT = PASS`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Inspect `Loop Engineer/Loop-Engineer/loop/chain.py` only as the next materially distinct traceability candidate. Select it only if it demonstrates executable registration/binding/loader semantics; otherwise persist the refutation and continue RESEARCH_REUSE without copying.
