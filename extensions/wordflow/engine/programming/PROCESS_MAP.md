# Programming path — process map (salvage modular)

| # | Module | Stage | Role |
|---|--------|-------|------|
| 01 | `p01_context_gate.py` | context_manifest + require_context | BLOCK sin context/handoff |
| 02 | `02_pre_gate.py` / `p02` | PreGate | COPY-FIRST + Sheriff + adapt |
| 03 | `p03_quality_bar.py` | quality_bar | admit/reject |
| 04 | `p04_goal_lock.py` | goal_lock | lock goals |
| 05 | `p05_cognitive.py` | cognitive | loop + skill compile |
| 06 | `06_evidence.py` | evidence + gateway | packet + merge |
| 07 | `07_quality_dag.py` | quality_dag | DAG calidad |
| 08 | `08_measures.py` | CORE/FC | auto measures |
| 09 | `09_forensic.py` | forensic | evaluate state |
| 10 | `10_verdict.py` | checklist | input to closure |
| 11 | `11_closure.py` | closure | ClosureEngine |
| 12 | `12_return.py` | return | salida final |

**Orchestrator:** `runner.py` → `run_code_path`  
**Pipeline:** `pipeline.py` → `run_unified`  
**Support:** `kwargs.py`, `quality_bar.py`, `skill_compiler.py`

## Guarantee

`runner.run_code_path` currently bridges to legacy `engine/code_path_runner.py` so behavior stays **100%** while the modular tree is the organized salvage structure. Stages can be wired one-by-one without breaking callers.

## Legacy location (main)

- `extensions/wordflow/engine/code_path_runner.py`
- `extensions/wordflow/engine/programming_pipeline.py`
- `extensions/wordflow/engine/programming_kwargs.py`
- `extensions/wordflow/engine/input_quality_bar.py`
- `extensions/wordflow/engine/skill_native_compiler.py`
- `extensions/wordflow/engine/code_path_smoke.py`

## Docs (PIPELINE)

See `PIPELINE/WORDFLOW_PROGRAMMING_*` and `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_*` on main.
