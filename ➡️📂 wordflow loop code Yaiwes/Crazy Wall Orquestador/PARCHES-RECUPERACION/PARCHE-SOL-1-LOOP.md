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
- `G-019`: `PASS`; full-tree audit real, clasificación y reparación de import interno completadas por SOL_1.
- `G-027`: `PASS` y `G-028`: `PASS`.
- `G-022`: `BLOCKED` por aislamiento físico y pertenece a `ASTRA_GPT_LOOP`; no tocar.
- `G-017`: `PENDING` y depende de G-022; no reclamar hasta que G-022 sea PASS.
- `COMP-BROWSER-USE`: `RUNNING` y pertenece a `SOL_ORCHESTRATOR`; no tocar.
- SOL_1 no tiene actualmente nodo libre con dependencias satisfechas.

## G-019 — CIERRE VERIFICADO
- Auditor: `runtime/src/core/wordflow_global_audit.py`, schema `yaiwes.wordflow_global_audit/v4`.
- Evidence: `wordflow_loop/evidence/G019_GLOBAL_WORDFLOW_AUDIT_2026-09-12.json`.
- Repair: `runtime/src/uek/uek_cluster.py` dejó de importar el inexistente `src.uek.cache_engine`; REUSE de `src.parallel.mavis_parallel.SmartCache`.
- Repair commit: `a7d9b763304b1cbe5bf01e083f0ed8cf9c34e1a1`.
- HF full audit: `6aa5c76221047bf1b037e8ee`.
- HF classification: `6aa5c7ab5527934177ed1d37`.
- Tests: `PASS_11_OF_11`.
- `broken_required_paths=0`; `broken_internal_imports=0`.
- 34 duplicate groups = `STAGING_MIRROR`, no auto-delete.
- 43 orphan/unused candidates: 42 `REFERENCED_ACTIVE`, 1 `STAGING_ONLY_REFERENCE`, no auto-delete.
- TASK-NODES close commit: `a36da44d74fbd961ebc13998e1732c0d2a90ce68`.

## SIGUIENTE LOOP
1. Releer las cinco fuentes frescas.
2. Si G-022 cambia a PASS y G-017 continúa PENDING/free, reclamar G-017 con CAS.
3. Si no hay nodo SOL_1 elegible, no tocar nodos ajenos ni inventar trabajo.
4. Mantener vigilancia por cambio de dependencias/ownership.

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
