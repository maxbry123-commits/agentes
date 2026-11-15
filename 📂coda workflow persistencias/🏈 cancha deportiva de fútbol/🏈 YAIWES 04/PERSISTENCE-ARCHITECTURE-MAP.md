# 04 — AI_Pentest → CODA persistence link

## Provenance

- Source: `yuanweipeifang/AI_Pentest`
- Source commit: `de242f062a79afc2c61e3aaf2a877a3ceacc1644`
- Verified source/extracted tree SHA-256: `abbe0288a25989adfd5a779c9b72a020f5eb5eb501716fb30d68fd84842ec4f2`
- Files verified by motor: 93

## Architecture retained

The copied project contains useful control-plane primitives in `backend/core/event_store.py` and `backend/core/interaction_bus.py`: session events, collaboration rounds, inter-agent messages and bounded event history. The base agent package also provides task abstractions and sequential/parallel coordination patterns; coordinator/report roles are retained as architecture inputs.

## Surgical transformation

The transformed public `backend.agents` surface no longer imports `ReconAgent`, `VulnAgent` or `ExploitAgent`. The transformed `backend.tools` surface exposes only abstract tool/result/registry primitives and no longer imports network/web/vulnerability scanners, brute-force, post-exploitation or ToolManager. The transformed `backend.core` public surface exposes event/message persistence and reporting primitives rather than loading the upstream pentest orchestrator/decision engine.

`code/coda_persistence/link.py` implements an inert event-checkpoint workflow:

`SESSION_CREATED → ATTEMPT_STARTED → SAFE_TASK → TASK_VERIFIED → HANDOFF_READY`

Snapshots use atomic JSON replacement, retries are bounded, completed work is idempotent, raw IDs are hashed before becoming paths, and disallowed task categories fail closed. The safe adapter performs no scanner, brute-force or post-exploitation action.

Next link: `05-AI-Infra-Guard`.

## Test evidence

GitHub Actions run `34811012821`, job `103872206202`: **PASS**. At that point the transformed set ran 16 safe tests total (4 per links 01–04), all passing. Link 04 passed event-checkpoint handoff, idempotent resume, fail-closed rejection of a brute-force task category and checkpoint path containment.
