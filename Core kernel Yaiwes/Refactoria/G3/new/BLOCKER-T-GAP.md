# BLOCKER-T-GAP — G3

**Status:** BLOCKED_RUNTIME

## Problem
The deterministic AST test→assert scanner exists, but acceptance requires execution over the repository tests and a reproducible MD/JSON artifact. The GitHub connector cannot execute repository code.

## Evidence
- Scanner exists under `Refactoria/G3/new/`.
- `TASK-GAPS/03_TEST_REPORT.md` explicitly records G3 execution as pending.
- Canonical destination is `agente-yaiwes/code-programming-engine/module-tests/`.

## Impact
No assertion counts or per-test evidence may be invented.

## Recommended action
Run the scanner in repository runtime, verify every relevant test file is represented, verify assert counts/citations, repeat with the same tree and compare outputs, then commit artifacts and evidence.

## Decision
G3 remains BLOCKED_RUNTIME; no fake PASS.
