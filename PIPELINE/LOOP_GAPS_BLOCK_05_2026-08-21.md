# LOOP GAPS BLOCK 05 — 2026-08-21

## Objective
Close the remaining Wordflow programming gaps without claiming completion without evidence.

## Governing method
CONTEXT → COPY-FIRST/REUSE → IMPLEMENT → WIRE → TEST → FORENSIC 4-PASS → VERDICT → PIPELINE.

## Completed in this block

### T01 — Router / C-19
- FIX: the `PATH_GATEWAY_DENY` C-19 path now delegates to `RouterHTTPGateway(allow_mock_fallback=False)`.
- Result: no mock response is returned on the C-19 production path; missing/unreachable Router remains fail-closed.
- Commit: `15a889b39b84208f75e8a5e30ab7aae7cc6924f3`.
- Remote read-back: PASS.
- Status: IMPLEMENTED; executable verification remains pending for the next verification pass.

### T03/T04 — Gap lifecycle + persistence
- `GapRegistry` persists to `.wordflow/gap_registry.json` by default and supports an override through `WORDFLOW_GAP_REGISTRY_PATH`.
- Writes are atomic and every add/transition is persisted.
- Added `GapStateMachine` as a lifecycle adapter using GapRegistry as the single storage authority.
- Added restart/recovery and invalid-transition tests.
- Commits: `76485c7753b8da35133ee3a5613ac2b8325ece73`, `fff28d684a62eefc098d6c29e12db86688712e99`.
- Remote read-back: PASS.
- Status: IMPLEMENTED; executable verification remains pending.

### Security hygiene
- Embedded GitHub credential in deterministic-build workflow was replaced with `secrets.GITHUB_TOKEN` in the prior block.
- Commit: `af013acd844fa8854a7b1f33188393987aa4e4bc`.
- Remote read-back: PASS.

## Remaining gaps

T02 C100/T49 — BLOCKED until independent production/provider/git-apply evidence exists. No fabricated PASS.

T05 FourPass — OPEN: need caller graph proving one authoritative controller and tests for all four passes.

T06 Reception — PARTIAL: current runtime already performs convert → input compiler → classifier → locate → plugin → context pack → git hook; needs E2E evidence.

T07 Traceability — OPEN: prove DOC→REQ→CODE→TEST→EVIDENCE linkage on the real path.

T08 Connectivity — PARTIAL: runtime wiring exists; need real consumer/caller verification through the complete path.

T09 Audit history — OPEN: reuse or implement durable append-only history with replay/immutability tests.

T10 Fail-closed — OPEN: audit every caller/profile/configuration of context_verified, handoff_verified, enforce_post_verify and related gates.

## Next verification/repair order
1. T01 executable regression + Router integration boundary.
2. T06/T08 E2E reception/connectivity.
3. T10 caller-wide fail-closed audit.
4. T03/T04 lifecycle/restart tests.
5. T05 FourPass authority and caller graph.
6. T07 traceability/mismatch detector.
7. T09 durable audit history.
8. T02 C100 only when independent evidence exists.

## 10 resolution routes for any new blocking gap
1. Reuse existing component.
2. Copy-first nearest compatible implementation.
3. Narrow adapter at existing interface.
4. Explicit dependency injection.
5. Failing regression test first.
6. Integration test at real caller boundary.
7. Persistence/restart verification.
8. Source/caller/test forensic cross-check.
9. Public developer-practice comparison for the exact failure.
10. If evidence remains unavailable, record BLOCKED rather than fabricate PASS/DONE.

## Verification rule
PASS requires source read-back + changed-file evidence + test/CI evidence when executable + forensic cross-check + PIPELINE update. DONE is forbidden while any required gate remains unverified.
