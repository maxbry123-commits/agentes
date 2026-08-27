# G2 — C-19 acceptance evidence

## Source
The canonical runner is `agente-yaiwes/code-programming-engine/code-path-execution/code_path_runner.py`. Its real `run_code_path` signature was inspected on `main` before this contract was generated.

## Closed portion
`C19_RUN_CODE_PATH_INPUT.schema.json` covers the actual named input parameters in the inspected runner signature. No invented p01–p19 stages or undocumented APIs are introduced.

## Validation example
A minimal valid example is `{ "raw_input": "C-19 schema validation input" }`; all other properties are optional exactly as the Python signature provides defaults.

## Residual
Per-stage output schemas for the internal execution stages (context, pre_gate, quality_bar, goal_lock, cognitive, path_gateway, evidence, quality_dag, forensic, closure) remain residual work unless their complete output contracts can be extracted and validated from source without guessing. They are not marked PASS by assumption.

## Plugin rule
The schema file is a stable contract artifact. Future connections use the registered plugin/contract mechanism; the schema itself is not edited merely to establish a connection.
