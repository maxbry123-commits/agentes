# ARQUITECTURA WORDFLOW GLOBAL — con Forensic Enforcement 100%

## Control plane (fail-closed)
`standards/forensic_core.py` → CORE14 + 4-pass + counters + PASS rules  
`standards/gap_registry.py` → lifecycle gaps  
`standards/checklist_sheriff.py` + applicability + evidence_verifier  
`standards/verdict_authority.py` / closure_engine  

## Execution plane
`engine/code_path_runner.py` — BLOCK sin context; forensic evaluate obligatorio; llm DENY  

## Data
catalogs JSON · PIPELINE policy docs · CI forensic-gates  

## Regla de oro
CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS  
NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT  
REQUIRED no se bypasea  

Detalle programming: `PIPELINE/WORDFLOW_PROGRAMMING_COMO_FUNCIONA.md`  
Contrato: `PIPELINE/FORENSIC_ENFORCEMENT_REQUIRED.md`
