# BLOCKER-T-GAP — G1

**Status:** BLOCKED_RUNTIME

## Problem
The deterministic AST exporter exists, but the acceptance condition requires an actual generated non-empty artifact in the canonical destination and reproducibility evidence. GitHub connector access is repository-only and cannot execute the exporter.

## Evidence
- Source preserved under `Refactoria/G1/source/`.
- Exporter under `Refactoria/G1/new/`.
- Canonical artifact required at `agente-yaiwes/control-governance/symbol-index-wiring-graph/SYMBOL_INDEX_PROGRAMMING.md`.
- `TASK-GAPS/03_TEST_REPORT.md` explicitly records execution as pending.

## Impact
Without execution, generated content and reproducibility cannot be claimed PASS.

## Recommended action
Run the exporter in a repository runtime, verify non-empty output, verify runner/pipeline symbols, run a second identical export and compare output, then commit the artifact and evidence.

## Decision
G1 remains BLOCKED_RUNTIME; no fake PASS.
