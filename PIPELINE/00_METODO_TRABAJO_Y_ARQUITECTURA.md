# PIPELINE 00 — MÉTODO DE TRABAJO

**Forense:** PIPELINE/FORENSIC_CODE_AUDIT.md  
**Estándar:** PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md  
**Standards:** extensions/wordflow/standards/

## Obligatorio en toda tarea de code
1. Context + Handoff verificados o BLOCK
2. **COPY-FIRST:** buscar code existente → COPY/ADAPT; GENERATE solo si no hay match
3. DONE literal
4. Commit + Evidence (incluir SOURCE→DEST si hubo copia)
5. Post-verify: auditoría forense 4 pasadas + VerdictAuthority
6. Gap → FIX → RE-AUDIT hasta PASS

## Cadena ejecutor
```
CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE
→ FORENSIC 4-PASS → VERDICT AUTHORITY → CLOSED | FIX LOOP
```

## CONTROL DE TRABAJO
1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE · 5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad
