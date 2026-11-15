# EVIDENCE — 3STEP STEP1 MOVE SOURCE GAP

Contract: `tel.workflow/v4`
Mode: `FAIL_CLOSED_EXECUTION_LOOP`
Scope: Director 3-step objective, Step 1 MOVE only.

## Reconciled HEAD
- Observed `main` HEAD before persistence: `d8a0348c13de44e794640c1fd4492b7559305bfd`.
- Concurrent activity exists; no force git used.

## Source control evidence
Expected source staging path:
`➡️📂 Wordflow LOOP Yaiwes/📂 archivos download/📂 LOOP open source 5/`

Manifest blob: `ad0f0c3b4b598e3d780c18b4568bcc33f6a88260`.
Checkpoint blob: `434a909fb6f96728bc870a31b32d0d466ef47593`.

Manifest/checkpoint declare exactly five extracted trees:
1. LangGraph — tree_sha256 `867541918ebe1907d7bae78e71e7b6ac82c87747fce78934b6d92ab8bf87acd9`
2. Temporal-Python-SDK — `1d125cc488dde70854b1a2f337edf433d8cb02f265289bfb86e50d20c90c7780`
3. Prefect — `eddc4ec0e0d4d6849071e90e05ff78932df0d02006584613d6a2daa01d1094be`
4. Hatchet-Python-SDK — `300d3154358ac5a6b8554fb645b492c3f3fdcf68cafd5e9adf9ffa20e2721873`
5. redun — `f18842d2d0749c580cc437e69027d69189c648da03552642465e915a122010c9`

## Physical tree verification
Git tree SHA for the staging directory: `2038965a82c6bc633ab1e8879967352c89676b53`.
Recursive read-back contains only:
- `LOOP5_CHECKPOINT.json`
- `LOOP5_MANIFEST.jsonl`

No extracted code roots are present in the Git tree at this path. Therefore a source→destination MOVE cannot be performed safely from repository contents without inventing/re-downloading data, both forbidden by the Director.

## Concurrency evidence
A real programming trigger already completed successfully on run `34179064259`, head SHA `7752fef9bb55336650aa95f37ba22e5c94f10901`.
A newer concurrent workflow `YAIWES Integrate Components 11-15` run `34179634309`, head SHA `d8a0348c13de44e794640c1fd4492b7559305bfd`, completed with `failure`.
These runs are evidence of concurrent repository mutation and must not be overwritten or force-reconciled.

## Sheriff decision
`STEP1_MOVE = BLOCKED_SOURCE_MATERIAL_NOT_IN_GIT_TREE`.
No MOVE/delete/copy was executed. This is not a research GAP; it is a physical source-location GAP. The next safe 1×1 delta is to resolve the already-created extraction artifact/source location from existing run/artifact evidence only, then move one verified tree without re-download or new OSS research.
