# LOOP GAPS BLOCK 05 — 2026-08-21

## Objective
Close the remaining Wordflow programming gaps without claiming completion without evidence.

## Governing method
CONTEXT → COPY-FIRST/REUSE → IMPLEMENT → WIRE → TEST → FORENSIC 4-PASS → VERDICT → PIPELINE.

## Completed in this block

### T04 — GapRegistry persistence
- BEFORE: GapRegistry stored `_gaps` only in process memory.
- CHANGE: `GapRegistry(path=None)` now loads/saves a JSON registry, default `.wordflow/gap_registry.json`, or `WORDFLOW_GAP_REGISTRY_PATH`.
- WRITE SAFETY: atomic temporary-file write followed by `os.replace`.
- LIFECYCLE: every add/transition persists the registry.
- TEST: `extensions/wordflow/tests/test_gap_registry_persistence.py` verifies a second registry instance reloads a FIXED gap and its revision evidence.
- Git commits: `61dd1ab0e44785a175287b0d0b5c5f3e9573ac0a`, `d2f0041bbbba1eb62ea5465abc624ff04705d617`.
- Remote read-back: PASS.
- Runtime CI execution: NOT VERIFIED in this block.
- Status: IMPLEMENTED; verification gate remains OPEN until CI/test execution is observed.

### Security hygiene discovered during verification
- `.github/workflows/deterministic-build.yml` contained an embedded GitHub credential.
- Replaced the embedded credential with `${{ secrets.GITHUB_TOKEN }}` in checkout, clone environment, and push environment.
- Commit: `af013acd844fa8854a7b1f33188393987aa4e4bc`.
- Remote read-back: PASS.
- Status: FIXED; credential rotation/revocation must be handled outside repository code if the exposed credential was real.

## Remaining gaps

T01 Router hot path — PARTIAL. `RouterHTTPGateway` exists and a deny-path test exists, but `code_path_runner.consult_path_gateway()` still instantiates `MockIntelligenceGateway`. Requires a safe full-file change plus integration regression test.

T02 C100/T49 — BLOCKED. Existing repository evidence records C100 as NO. Do not manufacture a provider claim. Close only when the required real production/provider evidence is available and independently verified.

T03 State machine — OPEN. Need identify/reuse the authoritative persistent run-state store and prove restart continuity.

T05 FourPass — OPEN. Need caller graph proving one authoritative controller and tests for all four passes.

T06 Reception — PARTIAL. Current reception code already performs convert → input compiler → classifier → locate → plugin → context pack → git hook. Need end-to-end execution evidence, not a duplicate implementation.

T07 Traceability — OPEN. Need prove DOC→REQ→CODE→TEST→EVIDENCE linkage on the real code path.

T08 Connectivity — PARTIAL. Existing reception and kernel wiring exist; need real consumer/caller verification through the complete code path.

T09 Audit history — OPEN. Need identify/reuse an existing durable append-only history mechanism or implement one with replay/immutability tests.

T10 Fail-closed — OPEN. Need audit every caller/profile/configuration of context_verified, handoff_verified, enforce_post_verify and related gates; add regression tests before changing defaults.

## Next LOOP order
1. T01 safe gateway wiring + integration test.
2. T06/T08 end-to-end reception/connectivity verification.
3. T10 caller-wide fail-closed audit.
4. T03 reuse authoritative persistent state.
5. T05 FourPass caller/controller audit.
6. T07 evidence chain.
7. T09 durable audit history.
8. T02 C100 only if independent evidence becomes available.

## 10 resolution routes for any new blocking gap
1. Reuse an existing repository component.
2. Copy-first from the nearest compatible implementation.
3. Add a narrow adapter at the existing interface.
4. Introduce explicit dependency injection.
5. Add a failing regression test before changing behavior.
6. Add an integration test at the real caller boundary.
7. Add persistence/restart verification where state is involved.
8. Add forensic cross-check against source, caller graph, and tests.
9. Search public developer practice for the exact failure mode and compare alternatives.
10. If evidence remains unavailable, record BLOCKED rather than fabricate PASS/DONE.

## Verification rule
PASS requires: source read-back + changed-file evidence + test/CI evidence when executable + forensic cross-check + pipeline update. DONE is forbidden when any required gate is unverified.
