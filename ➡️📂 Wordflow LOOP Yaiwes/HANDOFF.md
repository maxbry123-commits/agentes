# HANDOFF — Wordflow LOOP Yaiwes

## ABRIR PRIMERO
Este archivo es el punto de entrada para Codex/GPT al proyecto Wordflow LOOP Yaiwes.

Ruta:
`➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`

## ESTADO ACTUAL
- Contrato: `tel.workflow/v3`
- Modo: `FAIL_CLOSED_LOOP`
- Estado: `XRAY_5_PASS_COMPLETE_WITH_LITERAL_GAPS`
- Nodo actual: `README_LITERAL_RECONCILIATION`
- Checkpoint activo: `WFLOOP-XRAY-0004`
- README actual blob: `fed000b54a80fd6dd9b7cea21097043e289d73f6`
- Parte 1: `PENDING_IMPLEMENTATION_LITERAL_INPUT_RESTORED`
- Parte 2: `READY_INPUT014_MAPPED_TO_ARCHIVO_DOWNLOAD_1`
- Parte 3: `PENDING_IMPLEMENTATION_GAP_LITERAL_SOURCE`
- Parte 4: `PENDING_IMPLEMENTATION_GAP_LITERAL_SOURCE`
- Plan: 25 capas/nodos
- Auditoría X-Ray: 5 pasadas + 5 refutaciones
- Resultado documental: `PASS_WITH_LITERAL_GAPS`
- LOOP horario: `NOT_ACTIVE`
- Plugins externos autorizados: `GitHub`, `Hugging Face`

## CADENA OBLIGATORIA
`GOALS 12/12 → leer INPUT BLOCK literal sin reinterpretar → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones si falla → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 pasos → 3 refutaciones → verificación cruzada global → checklist/salida`

## ORDEN DE LECTURA PARA CODEX/GPT
1. Abrir este `HANDOFF.md`.
2. Leer el README canónico de arquitectura YAIWES.
3. Leer el README canónico Wordflow LOOP Yaiwes y respetar todos los INPUT BLOCKS literalmente.
4. Leer `AUDITORIA-XRAY-PLAN-5-PASADAS.md`.
5. Leer `STATE.json`.
6. Leer `CHECKPOINT.json`.
7. Leer `RECOVERY-PATCH.md`.
8. Leer `BITACORA-CRAZY-WALL.md`.
9. Leer `ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`.
10. Antes de ejecutar cualquier nodo, leer las fuentes que el CHECKPOINT cablea para ese nodo.
11. No declarar DONE/INTEGRATED sin evidencia real: ruta/URL/SHA/test/evidence_hash.

## ENLACES VISIBLES

### README Arquitectura YAIWES
https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/README.md

### README Wordflow LOOP Yaiwes
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20readme%20wordflow%20loop%20Yaiwes.md

### HANDOFF — abrir primero
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md

### AUDITORIA X-RAY 5 PASADAS
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md

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

## DELTAS X-RAY YA APLICADOS
- INPUT 010–013 restaurados literalmente en README desde blob histórico `474af741...`.
- Director 12/12 prevalece sobre sección documental 10/10 sin borrar la fuente.
- DSL = YAML/JSON/schema existente; no DSL adicional.
- Límites: 200 líneas/archivo; 500 LOC/bloque; 2000 LOC/task.
- Cola actual: 1×1.
- Solo GitHub/Hugging Face externos.
- Ejecución dinámica de candidate code bloqueada hasta static-AST+sandbox+security PASS.
- Usage metering necesita ledger persistente.
- Deploy requiere `plan.json` + gates + verificación remota + `evidence.json`.

## GAPS LITERALES
- Parte 3: no existe evidencia accesible suficiente del mensaje definitorio original completo como INPUT literal; no reconstruir desde resumen.
- Parte 4: no existe evidencia accesible suficiente del mensaje definitorio detallado previo a INPUT 015; no reconstruir desde resumen.

## REGLAS DE RECUPERACIÓN
- Si README, XRAY, STATE, CHECKPOINT, RECOVERY, Crazy Wall o HANDOFF divergen, estado efectivo = `GAP`.
- Recuperar por SHA/commit; nunca reconstruir de memoria.
- Antes de mutar: registrar nodo, mission_id, trace_id, INPUT literal, fuentes, destino, SHA previo, evidencia esperada y rollback.
- En fallo: conservar evidencia → generar 20 alternativas distintas → elegir delta distinto → reintentar → no avanzar hasta PASS.
- Solo GitHub y Hugging Face están autorizados como conexiones externas; cualquier otro plugin/conector requiere autorización explícita del Director.

## VERDAD OPERATIVA
La arquitectura/plan pasó la auditoría X-Ray de 5 pasadas con deltas aplicados. Sigue prohibido declarar `VERIFIED_CLOSED`: permanecen GAPs literales Parte 3/4 y la implementación física/test de Partes 1/3/4 continúa pendiente.