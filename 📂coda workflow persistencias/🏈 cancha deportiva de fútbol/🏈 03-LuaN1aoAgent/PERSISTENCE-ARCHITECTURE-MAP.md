# 03 — LuaN1aoAgent → CODA persistence link

## Provenance

- Source: `SanMuzZzZz/LuaN1aoAgent`
- Source commit: `2efe2c5020332d90ee82d108fc82a6604a6610eb`
- Verified source/extracted tree SHA-256: `09910912fabc3176a14bde84144c226dbe03734b068fa533ab4bb93474d1227a`
- Files verified by motor: 220

## Retained architecture

The copied source contains reusable durable-control structures: `stores/graph-store.ts`, `stores/runtime-store.ts`, `stores/execution-log.ts`, `planner-commands.ts`, `projection.ts`, `projector-coordinator.ts`, `operation-identity.ts`, `connectivity/runtime-owner-lease.ts`, and `epoch-budget-clock.ts`.

These become the design model for a persistent DAG link: state has explicit graph nodes, revisions, dependencies, checkpoint writes and bounded retry semantics.

## Excluded execution plane

The source also contains connectivity management, host egress, network/executor sandboxes, traffic proxying and target-facing tools. CODA does not use those paths. `src/coda-persistence-policy.ts` records the allow/deny boundary, and `code/coda_persistence/link.py` implements a local inert execution adapter with connectivity and sandbox use disabled.

The resulting link follows:

`LOAD_GRAPH_STATE → APPLY_SAFE_GRAPH_DELTA → CHECKPOINT → SAFE_EXECUTE → VERIFY → GRAPH_COMMIT → HANDOFF`

Next link: `04-AI-Pentest`.

## Test evidence

GitHub Actions run `34810674795`, job `103871220697`: **PASS**. The complete transformed set at that point ran 12 tests (4 per links 01, 02 and 03); all passed. Link 03 specifically passed graph handoff, idempotent resume, fail-closed rejection of a network-scan task category and checkpoint path containment.
