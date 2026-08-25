# Wordflow Programming Path — Modular (C-19)

**Branch:** `programming-modular-v1`  
**Goal:** flujo completo de programación de code dividido por proceso (no monolito).

## Estructura

```
programming/
├── __init__.py          # API pública
├── runner.py            # Orquestador 01→12 (run_code_path)
├── pipeline.py          # ProgrammingPipeline + run_unified
├── kwargs.py            # full_pass / minimal_block
├── quality_bar.py       # admit/reject input
├── skill_compiler.py    # compile skill → code seed
├── 01_context_gate.py   # context + handoff BLOCK
├── 02_pre_gate.py       # COPY-FIRST + Sheriff + adapt
├── 03_quality_bar.py    # quality stage wrapper
├── 04_goal_lock.py      # goal lock
├── 05_cognitive.py      # cognitive + skill
├── 06_evidence.py       # evidence + gateway
├── 07_quality_dag.py    # QualityDAG
├── 08_measures.py       # CORE + FC auto
├── 09_forensic.py       # forensic decide
├── 10_verdict.py        # checklist → closure input
├── 11_closure.py        # ClosureEngine
└── 12_return.py         # respuesta final
```

## Uso

```python
from extensions.wordflow.engine.programming import run_code_path, full_pass_kwargs

result = run_code_path(
    "Objetivo: implementar X...",
    **full_pass_kwargs(mission_id="M1", ci_attestation=True, attestation_source="ci"),
)
```

## Semántica

Misma secuencia FA-04 / ANEXO X que el runner legacy.
`llm_control=DENY` siempre.
`path=UNIFIED_RUNNER_V1_MODULAR`.

## Compatibilidad

Los paths legacy en `engine/code_path_runner.py` etc. siguen en `main`.
Esta rama **salva** el flujo modular sin borrar el legacy hasta merge controlado.
