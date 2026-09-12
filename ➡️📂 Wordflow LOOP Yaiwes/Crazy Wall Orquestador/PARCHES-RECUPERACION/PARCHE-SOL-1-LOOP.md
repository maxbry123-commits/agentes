# PARCHE DE RECUPERACIÓN — SOL 1 LOOP

Contrato: `tel.workflow/v4` · `FAIL_CLOSED_EXECUTION_LOOP`.

## ARRANQUE OBLIGATORIO
Leer frescos, en este orden:
1. `HANDOFF.md`
2. `Crazy Wall Orquestador/TASK-NODES.json`
3. `Crazy Wall Orquestador/STATE.json`
4. `Crazy Wall Orquestador/CHECKPOINT.json`
5. `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`

Raíz única de escritura: `➡️📂 Wordflow LOOP Yaiwes/`.

## REGLA DE OWNERSHIP
- Si existe un nodo `CLAIMED`, `RUNNING` o equivalente con `claimed_by=SOL_1`, SOL_1 **debe continuar únicamente ese nodo**.
- Solo cuando SOL_1 no tenga nodo activo puede reclamar **un único** nodo `PENDING`, libre y con dependencias satisfechas.
- Nunca reclamar ni modificar nodos de otro owner.
- Toda modificación compartida usa SHA/CAS + read-back; ante 409, releer y reintentar solo el delta propio.

## FLUJO 1×1
`1 investigar → 2 motor canónico solo si hace falta → 3 cablear/test/evidence → read-back → actualizar mismo nodo`.

Motor `NOT_REQUIRED` es válido cuando la tarea no mueve/descarga/extrae/copia componentes; no inventar uso de motor para cumplir una casilla.

## ESTADO DE REENTRADA ACTUAL — 2026-09-12
- `G-013`: `PASS`, cierre verificado en checkpoint `WFLOOP-CODE-GRAPH-20260911-0019`.
- Nodo actual SOL_1: `G-019 GLOBAL WORDFLOW AUDIT`, `CLAIMED`, investigación en curso.
- `G-022`: bloqueado por aislamiento físico; no tocar mientras pertenezca a otro owner.
- `COMP-BROWSER-USE`: pertenece a `SOL_ORCHESTRATOR`; no tocar.
- `G-017`: depende de G-022.
- `G-027`/`G-028`: pendientes, pero no reclamar mientras G-019 siga activo.

## G-019 — GATE ACTUAL
Auditar el Wordflow completo: inventario, capabilities, duplicados exactos, huérfanos, rutas rotas, código no usado y ledger.

Implementación actual:
- `runtime/src/core/wordflow_global_audit.py`
- `runtime/tests/test_wordflow_global_audit_g019.py`
- evidence `wordflow_loop/evidence/G019_GLOBAL_WORDFLOW_AUDIT_2026-09-12.json`

No cerrar G-019 hasta ejecutar el auditor sobre el árbol real completo y clasificar los candidatos. Duplicado/huérfano no autoriza borrado automático.

## PROHIBICIONES
- No LFS.
- No force.
- No Step4.
- No refactor lateral.
- No escribir fuera de la raíz autorizada.
- No restaurar documentos/rutas históricas sin source canónico.
- No declarar PASS por presencia de archivos ni por ejecución no realizada.

HANDOFF:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/HANDOFF.md

CRAZY WALL:
https://github.com/maxbry123-commits/agentes/blob/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes/Crazy%20Wall%20Orquestador/BITACORA-CRAZY-WALL.md