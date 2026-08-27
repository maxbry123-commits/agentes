# G2 — C-19 acceptance evidence

## Source
Canonical sources inspected on `main`:
- `extensions/wordflow/engine/code_path_runner.py`
- `extensions/wordflow/engine/programming_pipeline.py`

## Closed portion
The C-19 contract set now covers:
1. `C19_RUN_CODE_PATH_INPUT.schema.json` — actual named runner inputs.
2. `C19_POLICY_SNAPSHOT_OUTPUT.schema.json` — actual `policy_snapshot` stage output exposed by `ProgrammingPipeline.run_unified`.
3. `C19_PRE_GATE_OUTPUT.schema.json` — actual `pre_gate` output boundary (`allow` is consumed by the pipeline).
4. `C19_RUNNER_OUTPUT.schema.json` — actual runner result boundary consumed by `run_unified` (`ok`, `verdict`, `path`, plus observed optional result fields).
5. Internal runner stage contracts are represented by minimal object schemas only where the source exposes an object boundary; no invented properties are asserted.

No p01–p19 modules, undocumented APIs, or fabricated fields are introduced.

## Validation
`Refactoria/G2/new/validate_c19_schemas.py` validates every C19 schema with JSON Schema Draft 2020-12 and validates every schema `examples` entry. JSON Schema Draft 2020-12 is the normative schema dialect used by these artifacts.

## Residual boundary
The schemas intentionally do not claim semantic field-level contracts for internal objects whose producers do not expose a stable typed structure. Those values remain open objects rather than fabricated structures. This is a contract boundary, not an untracked gap.

## Plugin rule
Schema files are stable contract artifacts. Future connections use the registered plugin/contract mechanism; the schemas themselves are not edited merely to establish a connection.
