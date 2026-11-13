# GAPS — INVESTIGACIÓN + CODE GRAPH — WORDFLOW LOOP YAIWES

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0019`.  
Regla de cierre: investigación/provenance + decisión + implementación cuando aplique + test/simulación + read-back/commit + persistencia en fuentes de verdad. Presencia ≠ PASS.

## G-001 — CODE GRAPH workspace
`CLOSED_VERIFIED_LOCAL`. `runtime/src/core/code_graph_workspace.py` blob `6fe57e6c4233532623a8de589892de2d28897cb9`; tests blob `c7f00e3155d22c559907d50af31bf95403a5eb68`; evidence `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`. Cubre nodos/aristas, canonical JSON, SHA-256, fail-closed y proyección al DAG existente.

## G-002 — Ask Council + auditoría del archivo de entrada
`CLOSED_VERIFIED_LOCAL`. Contrato `yaiwes.file_audit/v1` en `runtime/src/core/file_audit_contract.py`, blob `e6624c0b39421a01d54cf0615920073c5dd1ee0f`. Exige source_id/filename basename/provenance; fingerprint SHA-256; detecta Python/JSON/YAML/Markdown/text; extrae arquitectura, interfaces, dependencias, capacidades, riesgos y requisitos. Riesgos peligrosos generan `BLOCK_AND_REVIEW`. Council normalizado a `ADOPT|ADAPT|REJECT|RESEARCH_MORE`, findings/evidence/confidence/dissent; schema inválido falla cerrado; `executable_action_authorized=false` siempre. Tests `runtime/tests/test_file_audit_contract.py`, blob `d490a7e15205c37a0f476e6e4c0de7f9429f36c6`; read-back PASS; simulación local equivalente `PASS_5_OF_5_ASSERTIONS`; repo test execution no reclamada. Evidence `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`.

## G-003 — Generador de tareas
`CLOSED_VERIFIED_LOCAL`. `runtime/src/core/code_task_graph.py`; separa `director_tasks` y `generated_tasks`; reutiliza `DAGEngine`. Evidence `G003_TASK_GRAPH_2026-09-10.json`.

## G-004 — Placement A–G
`CLOSED_VERIFIED_LOCAL`. `runtime/src/core/placement_classifier.py`, blob `69698ad30ba1903e0780efcea1952a3737aeb23e`; fallback `PLACEMENT_REVIEW_REQUIRED`; evidence `G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.

## G-005 — Investigación/reutilización previa a code
`CLOSED_VERIFIED_LOCAL`. `runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044` aplica selector determinista `REUSE > PATCH > ADAPT > GENERATE`; valida source URL/licencia/mantenimiento/compatibilidad/riesgo/footprint, máximo 10 candidatos, IDs únicos y fail-closed de catálogo. Catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8` con 8 opciones: 4 capacidades locales + Graphiti + Graphology + NetworkX + Tree-sitter. Licencias externas verificadas contra upstream: Graphiti Apache-2.0, Graphology MIT, NetworkX BSD-3-Clause, Tree-sitter MIT. Tests `runtime/tests/test_reuse_selector.py`, blob `1bcd0fca22d1238d28add1880e882e7af863ad52`; read-back PASS; `repo_pytest_execution=NOT_CLAIMED`; simulación equivalente `PASS_3_OF_3_DECISIONS`. Evidence `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`. No se instaló/copió ningún componente externo.

## G-006 — Creación de code nuevo
`BLOCKED_DEPENDENCY_G018`. La política existe, pero el cierre requiere Fables/Ficha con source proof canónico + registro/contract + test antes de cablear generación.

## G-007 — Ingesta de code existente
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS. Evaluar REUSE/PATCH/ADAPT, conservar provenance; copiar/mover solo con motores canónicos y read-back.

## G-008 — Neutralización de comportamiento inseguro
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS. Bloqueo pre-ejecución y sustitución benigna solo cuando sea justificable.

## G-009 — NO_VALUE_GAP
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS. Rechazo justificado cuando no aporta valor o degrada seguridad/mantenibilidad.

## G-010 — Watchdog supervisor
`CLOSED_VERIFIED`. Supervisa exclusivamente la raíz autorizada y no inventa PASS.

## G-011 — Recepción componente + copy/move
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS. Motores canónicos disponibles/read-back dentro del LOOP + blobs preservados.

## G-012 — Lista download/extract
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS. Intake schema + queue + adapter a motores + CRC/hash/path safety/read-back.

## G-013 — Fuentes de verdad
`RECONCILING_CHECKPOINT_0019`, owner `SOL_1`. Contrato `yaiwes.truth_reconciliation/v1`; STATE/CHECKPOINT son anchors. El parser acepta un único marcador explícito `Checkpoint canónico:` para documentos con historial y falla cerrado ante marcadores canónicos conflictivos. Módulo físico actual `runtime/src/core/source_truth_reconciler.py` blob `fb93ce9ee5b86439b0ba36ef72c404134d1984b1`; tests físicos `runtime/tests/test_source_truth_reconciler.py` blob `f39cb13a84d1dbb7fcb1c1467f712bf003a431df`. Cierre actual exige read-back 8/8 en checkpoint `0019`, reconciliador `CONSISTENT`, tests y evidencia actualizada.

## G-014 — Memoria de 18 agentes
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-015 — 12 GOALS entrada/salida
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-016 — Chat A ↔ Chat B
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-017 — Deployment determinista
`PENDING` dependiente de G-022 según `TASK-NODES.json`; no declarar PASS mientras el aislamiento físico siga bloqueado.

## G-018 — Enchufe Universal Fables
`CLAIMED` por `SOL_2` en el read-back de `TASK-NODES.json`; SOL_1 no lo toca. `G-006` continúa dependiendo de este nodo.

## G-019 — Auditoría global Wordflow
`PENDING`, depende de G-013. Solo será elegible cuando G-013 figure PASS y el nodo siga libre.

## G-020 — 12 fuentes comunidad
`CLOSED_VERIFIED`. `wordflow_loop/research/community_sources.json`, blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## G-021 — Cola/paralelismo
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-022 — Sandbox → reviewer → deploy
`BLOCKED_PHYSICAL_ISOLATION` según evidencia reciente; no cerrar sin backend enforceable real.

## G-023 — Hugging Face bridge
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-024 — Determinismo vs LLM
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-025 — Patrones MAVIS/PARALLEL
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-026 — UI/visual LOOP
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-027 — Graphiti
Mantener estado por nodo fresco en `TASK-NODES.json`; no inferir integración por mera presencia de source.

## G-028 — Graphology
Mantener estado por nodo fresco en `TASK-NODES.json`; no inferir integración por mera presencia de source.

## G-029 — Planificación organizada
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-030 — Crazy Wall multiagente
Estado por nodo fresco: consultar `TASK-NODES.json`; no reabrir si está PASS.

## Estado operativo para SOL_1 en checkpoint 0019
Nodo único actual: `G-013`, owner `SOL_1`, `SOURCE_OF_TRUTH_DRIFT`. `G-018` pertenece a `SOL_2`. `G-019` espera el cierre de G-013. La lista completa y concurrente de estados se toma de `TASK-NODES.json`; este ledger conserva definición/criterio y no debe sobrescribir cierres de otros workers. `AUTH_PROVIDER_TEST_PENDING` permanece abierto.