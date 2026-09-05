# 00_METODO_TRABAJO_Y_ARQUITECTURA — YAIWES / WORDFLOW LOOP

Estado: CANONICAL BRIDGE / FAIL-CLOSED
Contrato: `tel.workflow/v3`

Este archivo existe para resolver la autoridad declarada por `AGENTS.md` sin crear una arquitectura paralela ni reescribir las fuentes canónicas.

## Fuentes canónicas que gobiernan este método
1. Arquitectura YAIWES: `Readme arquitectura Yaiwes/README.md`
2. Skill vivo de orquestación: `Readme arquitectura Yaiwes/Skills de trabajo/SKILL-ORQUESTACION-YAIWES.md`
3. Wordflow LOOP canónico: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
4. HANDOFF activo: `➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`
5. STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
6. CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
7. RECOVERY: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/RECOVERY-PATCH.md`
8. Crazy Wall: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
9. X-Ray 5 pasadas: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md`

## Cadena obligatoria
`GOALS 12/12 → INPUT BLOCK literal sin reinterpretar → prioridades → plan → cola 1×1 → verifica/refuta → 20 alternativas si falla → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 → 3 refutaciones → verificación cruzada global → checklist/salida`.

## Principios
- 1 instrucción literal = 1 nodo.
- `REUSE > COPY/MOVE > PATCH PEQUEÑO > ADAPTER > GENERATE DELTA`.
- Kernel/control: 0% LLM.
- LLM solo cuando no exista resolución determinista suficiente.
- GitHub es fuente de verdad operativa del repo.
- No PASS por presencia de archivo: se exige contrato + wiring + test + evidencia.
- No secretos en README/STATE/logs/source; solo `secret_ref`.
- Plugins externos autorizados por el Director: GitHub y Hugging Face únicamente.
- Todo cambio real requiere checkpoint pre-mutation, SHA/commit de rollback y evidencia post-change.

## Roles
- Sol/Chat A: arquitectura, X-Ray, contratos, mapas, integración documental y verificación.
- Codex/Chat B: una task cerrada, sin rediseñar arquitectura global, con tests y EvidencePacket.
- Luna/Checker: verificación independiente cuando aplique.

## Regla de precedencia
Cuando dos documentos difieren, no se fusionan silenciosamente. Se conserva cada fuente y prevalece la instrucción literal más reciente del Director para el nodo activo, siempre que no contradiga una restricción superior del repo/seguridad.

## Cierre
Solo `VERIFIED_CLOSED` con evidencia reproducible. Falta de fuente, contrato, test, wiring o evidencia = `GAP`.