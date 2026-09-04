# MÉTODO V4 — 2 pasos + forense al final

**Fecha:** 2026-08-18
**Tipo:** APPEND_ONLY · NO borra V3 · **esta sección prevalece** para ejecución nueva
**Padre:** `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`

## Modelo vigente (V4)
TASK_INTAKE → **PASO 1 SANDBOX_BUILD** → LOCAL_VERIFY → READY_FOR_PUBLISH → **PASO 2 GITHUB_PUBLISH** → REMOTE_VERIFY → PUBLISHED

**PASO 3 FORENSIC por tarea: DESACTIVADO.**

Auditoría forense: **una sola**, al **cierre del bloque** de code, no después de cada Txx.

## Pasos por tarea (2)
1. **PASO 1 SANDBOX_BUILD** — code en sandbox, smoke, confirmar sandbox. Sin enlaces GH. ≠ DONE de lote.
2. **PASO 2 GITHUB_PUBLISH** — persistir, enlaces de archivo, read-back remoto. Publicado ≠ claim C100.

## Forense (único, al final)
- Dominios: METHOD · REQUIREMENTS · TRACEABILITY · SANDBOX · LOCAL_VERIFY · PUBLISH · REMOTE · INTEGRITY · NO_UNAUTHORIZED · TESTS
- Gaps bloqueantes → FIX + re-paso 2
- Veredictos: PASS | REPAIR_REQUIRED | BLOCKED
- Afirmación LLM ≠ evidencia

## AUDIT-5 intermedio
**No obligatorio** mientras rige V4. Se absorbe en el forense final.

## Conservado
COPY-FIRST · GitHub=verdad · sandbox≠DONE · CONTROL DE TRABAJO · no C100 prematuro
