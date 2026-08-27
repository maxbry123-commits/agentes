# G2 — C-19 schema boundary

The source exposes two contract layers:

1. `run_code_path` input parameters — covered by `C19_RUN_CODE_PATH_INPUT.schema.json`.
2. `ProgrammingPipeline.run_unified` stage/result boundaries — covered by the policy snapshot, pre-gate, and runner output schemas.

Internal values whose producer does not expose a stable typed object are intentionally represented as open JSON objects. No invented properties or stage modules are introduced.

**Residual technical gap: NONE for the C-19 contract boundary defined by the inspected source.**

Future semantic expansion requires a source change that exposes additional stable fields; it must be handled as a new contract revision, not by silently editing this contract.
