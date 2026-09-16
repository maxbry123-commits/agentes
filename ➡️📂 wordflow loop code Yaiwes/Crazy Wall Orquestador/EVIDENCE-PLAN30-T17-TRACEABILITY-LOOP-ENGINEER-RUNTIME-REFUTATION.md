# EVIDENCE — PLAN30 T17 TRACEABILITY LOOP ENGINEER RUNTIME REFUTATION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta reconciliation
- Main HEAD before write: `b796a8d5da2316752b33244c3d39e468ee0b7c3a`.
- STATE: T01–T16 `VERIFIED_CLOSED`; T17 `EN_CURSO`; T18–T30 pending.
- PLAN confirms T17 literal task: adapters/plugins → registry.
- Recovery requires RESEARCH_REUSE before generation and forbids reopening T16.
- Traceability classifies Loop Engineer supporting files as `REFERENCE / DEPENDENCY_CONTEXT`, not integrated by presence.

## Candidate inspected
Repository: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
Repository HEAD observed: `0ca97d7c7e8a2e20e986d18e273c6171a2684d30`
Path: `Loop Engineer/Loop-Engineer/loop/runtime.py`
Blob: `6c3af6b9b40d1061cc34647cffd4f47bfb6ac477`
URL: `https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/0ca97d7c7e8a2e20e986d18e273c6171a2684d30/Loop%20Engineer/Loop-Engineer/loop/runtime.py`
Intended T17 need: Capability Registry runtime implementing Ficha/plugin registration, slot/binding lifecycle and loader/mount-guard handoff.

## Direct code read-back
The blob implements read-only event-store/runtime reporting and verification: SQLite read-only access, event replay/reduction, state divergence detection, terminal desync checks, chain-head/ancestor verification, bound-evidence hashing and consistency findings.

Observed imports and runtime responsibilities are centered on `chain`, `completion`, `contract`, `events`, `paths`, `reducer`, `evidence` and SQLite state/event inspection.

No implementation was observed for:
- Ficha Contract v2 registration;
- adapter/plugin registration;
- Capability Registry slots;
- plugin activation/allowlist lifecycle;
- mount_guard;
- plugin loader;
- registry→router/handoff binding.

## Decision / refutation
- Candidate is useful reference runtime for event/evidence integrity, but is not a T17 Capability Registry donor.
- Copying it into registry/loader would conflate event-store verification with plugin lifecycle and violate the required modular separation.
- `DECISION = REFERENCE_ONLY / REJECT_AS_T17_REGISTRY_DONOR`.
- No source file was modified or moved.
- No destination code was copied/generated.
- No vendor source was modified.
- T16 remains untouched and `VERIFIED_CLOSED`.
- T17 remains `EN_CURSO`; `verify_final` not run.

## Evidence outcome
`SOURCE_BLOB_READ_BACK = PASS`
`SOURCE_PROVENANCE = PASS`
`T17_REGISTRY_FUNCTIONAL_FIT = FAIL`
`NO_DUPLICATE_REGISTRY_CREATED = PASS`
`NO_MONOLITH = PASS`
`NO_FORCE_GIT = PASS`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Inspect the next Loop Engineer `REFERENCE / DEPENDENCY_CONTEXT` file most likely to contain binding lifecycle — `loop/contract.py` then `loop/chain.py` only as needed — by exact blob/URL. Select a donor only if it implements Ficha/plugin registration + slot/binding/loader semantics; otherwise persist a materially distinct refutation and continue RESEARCH_REUSE.