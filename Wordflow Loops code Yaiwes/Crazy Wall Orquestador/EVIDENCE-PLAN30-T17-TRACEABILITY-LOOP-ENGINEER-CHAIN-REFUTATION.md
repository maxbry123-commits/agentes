# EVIDENCE — PLAN30 T17 TRACEABILITY LOOP ENGINEER CHAIN REFUTATION

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Node: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Director step: `2/4 — COPY_ONLY`
Queue: `1x1`

## Pre-delta reconciliation
- Main HEAD before write: `942d938a1822ed911b1661bd4b06e9d30a820d34`.
- STATE confirms T01–T16 `VERIFIED_CLOSED`, T17 `EN_CURSO`, T18–T30 pending, 53.33% PLAN30.
- CHECKPOINT confirms `WFLOOP-PLAN30-0017-ACTIVE`, contract `tel.workflow/v4`, queue `1x1`.
- PLAN confirms T17 objective `Cablear adapters/plugins a registry` and T16 evidence remains closed.
- RECOVERY requires RESEARCH_REUSE before generation and forbids reopening T16.
- README architecture is historical/stale for T16 and explicitly defers to later STATE/CHECKPOINT/PLAN evidence.
- HEAD re-read immediately before mutation remained `942d938a1822ed911b1661bd4b06e9d30a820d34`; no concurrent commit interposed.

## Candidate inspected
Repository: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
Repository commit/ref: `0ca97d7c7e8a2e20e986d18e273c6171a2684d30`
Path: `Loop Engineer/Loop-Engineer/loop/chain.py`
Blob: `97a044066566c54409f77b9304a4b66161efe76c`
URL: `https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/0ca97d7c7e8a2e20e986d18e273c6171a2684d30/Loop%20Engineer/Loop-Engineer/loop/chain.py`
Required T17 function: runtime Capability Registry implementing Ficha/plugin registration, slot/binding lifecycle, loader/mount-guard handoff and registry→router/handoff integration.

## Direct source read-back
`chain.py` is pure, I/O-free event hash-chain canonicalization and verification. It defines `canonical_json`, `compute_event_hash`, `link_issue`, `head_sequence`, and `verify_chain` over event records.

Demonstrated function:
- deterministic event hashing;
- prev-hash link validation;
- chain-head verification;
- tamper/rewrite evidence checking.

Not demonstrated:
- Ficha Contract v2 plugin registration;
- capability/plugin registry entries;
- slots or binding lifecycle;
- adapter/plugin activation;
- plugin loader;
- mount_guard;
- registry lookup;
- registry→router/handoff wiring.

## Decision
`DECISION = REFERENCE_ONLY / REJECT_AS_T17_REGISTRY_DONOR`

Reason: hash-chain verification belongs to evidence integrity and can support later verification, but it is not a runtime capability/plugin registry. Copying it into T17 registry would misclassify responsibilities and violate modular separation.

No donor source was modified or moved. No destination runtime code was copied or generated. No verified T01–T16 work was rewritten. No duplicate registry, parallel bus, vendor edit, monolith, LFS, or force operation was introduced.

## Evidence outcome
`SOURCE_BLOB_READ_BACK = PASS`
`SOURCE_PROVENANCE = PASS`
`HASH_CHAIN_FUNCTION = PASS`
`T17_REGISTRY_FUNCTIONAL_FIT = FAIL`
`NO_COPY_ON_FAILED_FIT = PASS`
`NO_REWRITE_VERIFIED_WORK = PASS`
`NO_DUPLICATE_REGISTRY_CREATED = PASS`
`NO_MONOLITH = PASS`
`NO_FORCE_GIT = PASS`
`T17_STATUS = EN_CURSO`

## Next exact 1x1 delta
Continue traceability-driven RESEARCH_REUSE with one materially distinct source-root that can actually expose registry/plugin/binding semantics. Inspect the next candidate in `TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md`; require repo + exact path + URL + commit/blob SHA + executable registration/binding/loader behavior + non-duplicate destination before any COPY_ONLY.