# CHECKPOINT — G2 C-19 schema recovery

## Repository truth
- Repo: `maxbry123-commits/agentes`
- Branch: `main`
- Hot path: `extensions/wordflow/engine/code_path_runner.py`
- Rule: NO_INVENTAR / NO_FAKE_PASS / NO_APAGAR_MONOLITO

## Source inspected
- `extensions/wordflow/engine/code_path_runner.py`
- `extensions/wordflow/engine/programming_pipeline.py`
- `Refactoria/G2/source/programming_pipeline.py`

## Patch
Added source-derived C19 contract artifacts under:
`agente-yaiwes/code-programming-engine/schema-contracts-io/`

Contracts:
- `C19_RUN_CODE_PATH_INPUT.schema.json`
- `C19_POLICY_SNAPSHOT_OUTPUT.schema.json`
- `C19_PRE_GATE_OUTPUT.schema.json`
- `C19_RUNNER_OUTPUT.schema.json`

Added deterministic validator:
`Refactoria/G2/new/validate_c19_schemas.py`

CI workflow now installs `jsonschema` and executes the validator:
`.github/workflows/verify-gap-indexes.yml`

## Verification
- JSON Schema dialect: Draft 2020-12.
- Every C19 schema contains an example.
- Validator checks schema validity and validates every example.
- CI is read-only and includes protected hot-path diff verification.
- No p01–p12 module was invented.

## Status
G2 implementation: CLOSED / PASS candidate.
Final CI evidence: PENDING until the new workflow run executes on the updated workflow.

## Recovery
If CI fails, restore from the current `Refactoria/G2/source/` reference and inspect only the validator/schema patch. Do not modify `extensions/wordflow/engine/code_path_runner.py`.

## G5 remains separate
G5 is OPEN/BLOCKER because no real p01–p12 source exists. See `Refactoria/G5/new/20_SOURCE_RECOVERY_PATHS.md`.
