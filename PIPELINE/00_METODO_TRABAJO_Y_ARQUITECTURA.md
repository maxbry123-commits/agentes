# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

**Arquitectura REAL programación:** `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md`  
**Mapa forense:** `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`  
**Forense checklist:** `PIPELINE/FORENSIC_CODE_AUDIT.md`  
**Gaps:** `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`  
**Pipeline code:** `extensions/wordflow/engine/programming_pipeline.py`  
**Hot path:** `extensions/wordflow/engine/code_path_runner.py`

## Cadena obligatoria (política)
CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED | FIX LOOP

## Cadena REAL en code_path (arquitectura)
pre_gate → quality_bar → goal_lock → cognitive_loop → evidence → post_verify(VerdictAuthority)

## COPY-FIRST
name + catalog + AST → COPY/ADAPT; GENERATE last. Evidence SOURCE→DEST+SHA si copy_file_deterministic.

## CONTROL DE TRABAJO
1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE · 5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad
