# HANDOFF — Wordflow LOOP Yaiwes

## ABRIR PRIMERO
Este archivo es el punto de entrada para Codex/GPT al proyecto Wordflow LOOP Yaiwes.

Ruta:
`➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`

## ESTADO ACTUAL
- Contrato: `tel.workflow/v3`
- Modo: `FAIL_CLOSED_LOOP`
- Estado: `PLAN_PRESENTATION_READY`
- Nodo actual: `PLAN_LAYERED_ARCHITECTURE`
- Checkpoint activo: `WFLOOP-BUILD-0003`
- Parte 1: `PENDING_IMPLEMENTATION`
- Parte 2: `READY`
- Parte 3: `PENDING_IMPLEMENTATION`
- Parte 4: `PENDING_IMPLEMENTATION`
- Plan: 25 capas/nodos
- Fuentes cableadas: 13
- Inventario de fuentes: verificado
- Validación documental: 12 goals entrada + 12 goals salida + Ask Consil 12/12 + 3 auditorías de instrucciones + 4 verificaciones + 3 refutaciones
- Resultado actual del plan: `PASS_PLAN_DOCUMENTAL`
- LOOP horario: `NOT_ACTIVE`
- Próximo estado permitido: `DIRECTOR_REVIEW_PLAN_THEN_BUILD_NEXT_PENDING_NODE`

## CADENA OBLIGATORIA
`GOALS 12/12 → leer INPUT BLOCK literal sin reinterpretar → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones si falla → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 pasos → 3 refutaciones → verificación cruzada global → checklist/salida`

## ORDEN DE LECTURA PARA CODEX/GPT
1. Abrir este `HANDOFF.md`.
2. Leer el README canónico de arquitectura YAIWES.
3. Leer el README canónico Wordflow LOOP Yaiwes y respetar todos los INPUT BLOCKS literalmente.
4. Leer `STATE.json`.
5. Leer `CHECKPOINT.json`.
6. Leer `RECOVERY-PATCH.md`.
7. Leer `BITACORA-CRAZY-WALL.md`.
8. Leer `ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`.
9. Antes de ejecutar cualquier nodo, leer las fuentes que el CHECKPOINT cablea para ese nodo.
10. No declarar DONE/INTEGRATED sin evidencia real: ruta/URL/SHA/test/evidence_hash.

## ENLACES VISIBLES

### README Arquitectura YAIWES
https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/README.md

### README Wordflow LOOP Yaiwes
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20wordflow%20loop%20Yaiwes.md

### HANDOFF — abrir primero
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md

### STATE.json
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/STATE.json

### CHECKPOINT.json
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/CHECKPOINT.json

### RECOVERY-PATCH.md
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/RECOVERY-PATCH.md

### BITACORA-CRAZY-WALL.md
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md

### ANEXO plan de capas/fuentes/recovery
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md

## REGLAS DE RECUPERACIÓN
- Si README, STATE, CHECKPOINT, RECOVERY, Crazy Wall o HANDOFF divergen, estado efectivo = `GAP`.
- Recuperar por SHA/commit; nunca reconstruir de memoria.
- Antes de mutar: registrar nodo, mission_id, trace_id, INPUT literal, fuentes, destino, SHA previo, evidencia esperada y rollback.
- En fallo: conservar evidencia → generar 20 alternativas distintas → elegir delta distinto → reintentar → no avanzar hasta PASS.
- Solo GitHub y Hugging Face están autorizados como conexiones externas; cualquier otro plugin/conector requiere autorización explícita del Director.

## VERDAD OPERATIVA
El plan documental está preparado y validado, pero no equivale a que Parte 1, Parte 3 o Parte 4 estén físicamente implementadas ni a `VERIFIED_CLOSED`.
