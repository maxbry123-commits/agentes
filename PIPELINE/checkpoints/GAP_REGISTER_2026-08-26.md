# GAP REGISTER — 2026-08-26

**Scope:** post S2–S12 forensic remediation / S10 + OpenClaw cable loop.
**Truth:** GitHub `main`.
**Policy:** FAIL-CLOSED / NO_FAKE_PASS / NO_APAGAR_MONOLITO. G5 uses an explicit Director-authorized derived modularization because original p01–p12 source was absent.

| ID | Gap | Destination | Status | Evidence |
|---|---|---|---|---|
| G1 | SYMBOL_INDEX_PROGRAMMING.md | `agente-yaiwes/control-governance/symbol-index-wiring-graph/` | CLOSED/PASS | Final deterministic run `33032745705`, job `98388725584`; artifact `9630853631`, digest `sha256:2d75ed90824e9dd8b91c4da234d279a5fcd7e023d8faf6b99d8df6285ef9465a`. |
| G2 | Stage C-19 schemas | `agente-yaiwes/code-programming-engine/schema-contracts-io/` | CLOSED/PASS-PENDING-CI | Four source-derived schemas cover the real C-19 input and observable pipeline boundaries; `Refactoria/G2/new/validate_c19_schemas.py` performs Draft 2020-12 validation. |
| G3 | test→asserts index | `agente-yaiwes/code-programming-engine/module-tests/` | CLOSED/PASS | Final deterministic run `33032745705`, job `98388725584`; artifact `9630853631`. |
| G4 | Real CI log/trace | `agente-yaiwes/observability/trace-history/` | CLOSED/PASS | Real trace `G1_G3_VERIFY_RUN_33032745705.md`. |
| G5 | p01→p12 E2E wire | `agente-yaiwes/code-programming-engine/code-path-execution/` | IMPLEMENTED/PASS-PENDING-CI | Original p01–p12 source was absent. Director authorized derived modularization over the canonical runner. Twelve cable nodes, deterministic guard chain, p12 canonical-runner entrypoint, parity tests and CI workflow created. No canonical runner rewrite. |
| G6 | Real intelligence adapter | `agente-yaiwes/execution-engine-pool/adapter-layer/` | CLOSED/PASS | `OpenClawHTTPGateway` and plugin registration verified by existing cable evidence. |
| G7 | OpenClaw Wordflow route/body integration | `agente-yaiwes/execution-engine-pool/auxiliary-role-agents/` | CLOSED/PASS | Existing OpenClaw engine preserved; route/adapter/cable verified. Hermes intentionally excluded. |

## Latest G5 recovery evidence
- Canonical provenance: `Refactoria/G5/source/CANONICAL_SOURCE.md`.
- Derived orchestrator: `Refactoria/G5/new/pipeline_p01_p12.py`.
- Parity tests: `Refactoria/G5/new/test_p01_p12.py`.
- Twelve cable nodes: `agente-yaiwes/code-programming-engine/code-path-execution/p01_context.py` through `p12_closure.py`.
- CI workflow: `.github/workflows/verify-g5-wordflow.yml`.
- Latest commit containing the CI workflow: `d0cda5a247dd6e9202e2e548f3ae6628b95e8fc9`.
- CI evidence is emitted only by the real GitHub Actions run; no manual PASS artifact is generated.

## G5 recovery rule
The repository did not contain the historical p01–p12 source set. Rather than fabricate historical source, this loop implements a clearly marked derived cable over the existing `code_path_runner.py` and `programming_pipeline.py`, reusing the canonical implementation. The distinction is recorded permanently in `Refactoria/G5/source/`.

## Hot-path protection
`extensions/wordflow/engine/code_path_runner.py` remains the operational source. Its verified blob SHA is `f1c3e519e317d06352945b230ad4a03b02422ad5`. The G5 workflow fails if this protected source changes.
