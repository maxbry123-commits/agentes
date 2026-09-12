# HANDOFF — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`

## Histórico conservado
El cierre local anterior permanece válido: fleet=18, Council12=12, routing/fail-closed local y router MVP fueron probados localmente. Evidencia: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json` · commit `6c4b10a49fa8de3bd85348f15bd5f5fa461d128c`.

Estado externo histórico y actual: `AUTH_PROVIDER_TEST_PENDING`. No se afirma PASS_REAL de proveedores/APIs o agentes remotos sin ejecución autenticada real.

# Fase activa — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Estado: `ACTIVE_LOOP_CODE_GRAPH_RESEARCH`  
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0019`  
Nodo: `G013_SOURCE_TRUTH_RECONCILIATION`.

Pipeline objetivo:
`archivo/componente → Ask Council/auditoría → arquitectura → requisitos → director_tasks + generated_tasks → DAG/cola → placement A|B|C|D|E|F|G → REUSE>PATCH>ADAPT>GENERATE → sandbox → reviewer independiente → deployment determinista → evidencia → STATE/CHECKPOINT`.

## GAP status verificado
- `G-001 CLOSED_VERIFIED_LOCAL`: workspace `wordflow_loop/code_graph/`; serialización determinista + SHA-256 + proyección al DAG existente. Evidence `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`.
- `G-002 CLOSED_VERIFIED_LOCAL`: contrato `yaiwes.file_audit/v1` en `runtime/src/core/file_audit_contract.py`, blob `e6624c0b39421a01d54cf0615920073c5dd1ee0f`; tests `runtime/tests/test_file_audit_contract.py`, blob `d490a7e15205c37a0f476e6e4c0de7f9429f36c6`; evidence `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`; simulación local equivalente `PASS_5_OF_5_ASSERTIONS`. Council es asesor: `executable_action_authorized=false` siempre.
- `G-003 CLOSED_VERIFIED_LOCAL`: task graph determinista; mantiene `director_tasks` y `generated_tasks` separados. Evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.
- `G-004 CLOSED_VERIFIED_LOCAL`: clasificador A–G + `PLACEMENT_REVIEW_REQUIRED`. Evidence `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.
- `G-005 CLOSED_VERIFIED_LOCAL`: selector `runtime/src/core/reuse_selector.py`, blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`, catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`, tests blob `1bcd0fca22d1238d28add1880e882e7af863ad52`, evidence `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`. Política `REUSE > PATCH > ADAPT > GENERATE`, máximo 10 candidatos, source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios, read-back PASS, `repo_pytest_execution=NOT_CLAIMED`. No se instaló/copió código externo.
- `G-010 CLOSED_VERIFIED`: Watchdog CODE GRAPH activo y limitado a la raíz autorizada.
- `G-013 RECONCILING_CHECKPOINT_0019`: owner `SOL_1`; reconciliador `yaiwes.truth_reconciliation/v1`; cierre condicionado a 8/8 fuentes en 0019 + test + read-back. Evidence `wordflow_loop/evidence/G013_CANONICAL_RECONCILIATION_2026-09-11.json`.
- `G-020 CLOSED_VERIFIED`: 12 fuentes de investigación en `wordflow_loop/research/community_sources.json`.
- El estado por nodo fresco se toma de `Crazy Wall Orquestador/TASK-NODES.json`; no se reabren nodos ya PASS ni se pisan nodos de otros workers.

## Reutilización clave
`runtime/src/core/dag_engine.py` sigue siendo el DAG topológico determinista y gana como `REUSE` para capability `dag`; NetworkX queda referencia externa, no reemplazo. Graphiti queda `ADAPT` únicamente para contexto temporal/provenance/memoria; Graphology `ADAPT` únicamente para grafo/visualización cuando exista GAP concreto. No se añade scheduler paralelo.

## GAPs críticos abiertos
- `G-006 BLOCKED_DEPENDENCY_G018`: la política de generación existe, pero no puede cerrarse hasta source proof + Ficha/registro Fables verificados.
- `G-018`: reclamado por `SOL_2`; SOL_1 no lo toca.
- `G-022`: bloqueo físico de aislamiento; no convertir en PASS sin backend enforceable.
- `G-017`: depende de G-022 y permanece sin cierre positivo de deployment real.
- `G-019`: pendiente y dependiente de G-013; será elegible solo después del cierre verificado de G-013.

## Reglas de continuación
1. No escribir fuera de `➡️📂 Wordflow LOOP Yaiwes/`.
2. No cerrar GAP por presencia de archivo.
3. Motores de descargar/extraer/copiar/mover: únicamente canónicos, inmutables, destino explícito, hash/read-back, no LFS, no force.
4. Todo módulo nuevo entra por Enchufe Universal Fables/Ficha; no buses paralelos.
5. LLM solo en análisis/generación/Council; DAG/routing/gates/state/sandbox/hash/deploy permanecen deterministas.
6. Si SOL_1 ya tiene un nodo CLAIMED/RUNNING, debe terminar ese nodo antes de reclamar otro.
7. Nodo actual de SOL_1: `G-013`; después del cierre y read-back, releer `TASK-NODES.json` y solo entonces reclamar un único PENDING libre con dependencias satisfechas.