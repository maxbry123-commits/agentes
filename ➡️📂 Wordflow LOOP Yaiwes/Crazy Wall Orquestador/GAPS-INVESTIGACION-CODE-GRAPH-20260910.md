# GAPS — INVESTIGACIÓN + CODE GRAPH — WORDFLOW LOOP YAIWES

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
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
`CLOSED_VERIFIED_LOCAL`. `runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044` aplica selector determinista `REUSE > PATCH > ADAPT > GENERATE`; valida source URL/licencia/mantenimiento/compatibilidad/riesgo/footprint, máximo 10 candidatos, IDs únicos y fail-closed de catálogo. Catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8` con 8 opciones: 4 capacidades locales + Graphiti + Graphology + NetworkX + Tree-sitter. Licencias externas verificadas contra upstream: Graphiti Apache-2.0, Graphology MIT, NetworkX BSD-3-Clause, Tree-sitter MIT. Tests `runtime/tests/test_reuse_selector.py` blob `1bcd0fca22d1238d28add1880e882e7af863ad52`; read-back PASS; `repo_pytest_execution=NOT_CLAIMED`; simulación equivalente `PASS_3_OF_3_DECISIONS`. Evidence `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`. No se instaló/copió ningún componente externo.

## G-006 — Creación de code nuevo
`GAP_OPEN` · siguiente nodo 1×1. Solo si G-005 demuestra que no existe pieza adecuada. Cierre: ABI/Protocol + módulo mínimo + tests + registro/cableado Fables.

## G-007 — Ingesta de code existente
`GAP_OPEN`. Evaluar REUSE/PATCH/ADAPT, conservar provenance; copiar/mover solo con motores canónicos y read-back. Cierre: source proof + decisión + destino + test.

## G-008 — Neutralización de comportamiento inseguro
`GAP_OPEN`. Bloqueo pre-ejecución y sustitución benigna solo cuando sea justificable. Cierre: scanner/gates + reason codes + sandbox tests + evidence.

## G-009 — NO_VALUE_GAP
`GAP_OPEN`. Rechazo justificado cuando no aporta valor o degrada seguridad/mantenibilidad. Cierre: plantilla `.md` + alternativas + reviewer independiente.

## G-010 — Watchdog supervisor
`CLOSED_VERIFIED`. Supervisa exclusivamente la raíz autorizada y no inventa PASS.

## G-011 — Recepción componente + copy/move
`GAP_OPEN`. Cierre: motores canónicos disponibles/read-back dentro del LOOP + blobs preservados + operación simulada/real autorizada.

## G-012 — Lista download/extract
`GAP_OPEN`. Cierre: intake schema + queue + adapter a motores + CRC/hash/path safety/read-back.

## G-013 — Fuentes de verdad
`GAP_OPEN`. Core truths reconciliadas manualmente hasta checkpoint `0008`; PLAN/RECOVERY presentaron drift histórico detectado durante el ciclo G-005 y se reconciliarán al nuevo checkpoint; falta reconciliador automático + drift/conflict test.

## G-014 — Memoria de 18 agentes
`GAP_OPEN`. Cierre: 18 `agente-readme-memoria.md` + loader determinista + test pre-injection.

## G-015 — 12 GOALS entrada/salida
`GAP_OPEN`. Cierre: schema + runner + Council/simulaciones/refutaciones/cross-check + evidence.

## G-016 — Chat A ↔ Chat B
`GAP_IN_RESEARCH`. Chat-B localizado en T001/T007/T011; Chat-A aún no. Cierre: artefacto localizado/adaptado o `NOT_FOUND` probado.

## G-017 — Deployment determinista
`GAP_OPEN`. Installation engine actual contiene PASS/health estáticos no aceptados. Cierre: validate/build/sandbox/tests/reviewer/promote/checkpoint/rollback con checks reales.

## G-018 — Enchufe Universal Fables
`GAP_IN_RESEARCH`. Cierre: source proof canónico + Ficha/contract + registro/test; prohibidos buses paralelos.

## G-019 — Auditoría global Wordflow
`GAP_OPEN`. Cierre: inventario/capability map + duplicados/huérfanos/rutas rotas/code no usado + ledger reconciliado.

## G-020 — 12 fuentes comunidad
`CLOSED_VERIFIED`. `wordflow_loop/research/community_sources.json`, blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## G-021 — Cola/paralelismo
`GAP_OPEN`. Cierre: priority/dependencies/fan-out/fan-in/dedup/idempotency/concurrency/backpressure + tests.

## G-022 — Sandbox → reviewer → deploy
`GAP_OPEN`. Sandbox actual es descriptor lógico, no aislamiento demostrado. Cierre: adapter enforceable filesystem/network/time/memory + reviewer/promotion rejection tests.

## G-023 — Hugging Face bridge
`GAP_IN_RESEARCH`. Cierre: inventario por conector real + bridge determinista + refs + test sin secretos. No asumir token ni acceso.

## G-024 — Determinismo vs LLM
`GAP_OPEN`. Cierre: matriz `DETERMINISTIC|LLM_ALLOWED` + enforcement tests; LLM nunca autoriza ejecución.

## G-025 — Patrones MAVIS/PARALLEL
`GAP_OPEN`. Cierre: matriz ADOPT/ADAPT/REJECT de pools/priority/cache/batching/backpressure/async/dedup/ABI/registry/FSM/checkpoints/DLQ/durable recovery + benchmarks para claims de rendimiento.

## G-026 — UI/visual LOOP
`GAP_OPEN`. Cierre: stack visual + data schema + adapter/prototype cuando gates lo autoricen.

## G-027 — Graphiti
`GAP_IN_RESEARCH`. Candidato a contexto/provenance/memoria temporal, no scheduler. G-005 confirma licencia Apache-2.0 y decisión preliminar `ADAPT`; sigue abierto hasta copia exacta con motor + adapter + sandbox test.

## G-028 — Graphology
`GAP_IN_RESEARCH`. Candidato a graph object/algoritmos/layout/visualización, no durable execution. G-005 confirma licencia MIT y decisión preliminar `ADAPT`; sigue abierto hasta investigación + copia exacta + serializer/visual integration si aporta valor.

## G-029 — Planificación organizada
`GAP_IN_RESEARCH`. Default REUSE=`runtime/src/core/dag_engine.py`; G-005 confirma que DAGEngine local gana para capability `dag` frente a NetworkX por compatibilidad nativa/footprint. Comparar frameworks solo contra gaps no cubiertos. Cierre: matriz comparativa + decisión.

## G-030 — Crazy Wall multiagente
`GAP_OPEN`. Cierre: ownership/version/checkpoint/idempotency + optimistic concurrency/merge conflict protocol + tests.

## Estado del grupo tras checkpoint 0008
30 GAPs. Cerrados: `G-001`, `G-002`, `G-003`, `G-004`, `G-005`, `G-010`, `G-020` = 7. En investigación: `G-016`, `G-018`, `G-023`, `G-027`, `G-028`, `G-029`. Siguiente: `G-006`. `AUTH_PROVIDER_TEST_PENDING` permanece abierto; Graphiti/Graphology no integrados; no se crea bus paralelo.
