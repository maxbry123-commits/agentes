# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
Arquitectura: modular, determinista por defecto, no monolítica.

## Flujo base previamente verificado
`documentos → requisitos → Task Contract/Ficha → agent_fleet_plugin_registration → AgentFleetAdapter → registry → binding ID/slot/rol → router disponibilidad/prioridad → transporte API/MCP/command → agente → evidencia → STATE/CHECKPOINT`.

## Fleet + router previamente verificados localmente
Fleet=18 · Council12=12. Routing determinista por ID/rol. Sin runtime configurado, `fail_closed`.
Router: `wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Prioridad: `Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS`; dentro de una familia se agotan rutas/API antes de bajar. El GAP externo `AUTH_PROVIDER_TEST_PENDING` continúa abierto hasta prueba autenticada real.

# FASE ACTIVA — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0008`.  
Nodo activo: `CG06_NEW_CODE_POLICY_G006`.  
Ledger: `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`.

Pipeline operativo autorizado:
`archivo/componente → auditoría determinista + Ask Council normalizado → arquitectura/requisitos → director_tasks + generated_tasks → DAG/cola → placement A|B|C|D|E|F|G → REUSE>PATCH>ADAPT>GENERATE → sandbox → reviewer independiente → deployment determinista → evidence → STATE/CHECKPOINT`.

## G-001 — Raíz anclada de CODE GRAPH
Estado: `CLOSED_VERIFIED_LOCAL`.
Workspace canónico `wordflow_loop/code_graph/`. `runtime/src/core/code_graph_workspace.py` define 13 tipos de nodo, 14 tipos de arista, JSON canónico, SHA-256, validación fail-closed y proyección de dependencias al `DAGEngine` existente. No crea un orquestador paralelo. Module blob `6fe57e6c4233532623a8de589892de2d28897cb9`; tests blob `c7f00e3155d22c559907d50af31bf95403a5eb68`; evidence `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`; simulación local equivalente `PASS_5_OF_5_ASSERTIONS`.

## G-002 — Ask Council + auditoría del archivo de entrada
Estado: `CLOSED_VERIFIED_LOCAL`.
Contrato `yaiwes.file_audit/v1` en `runtime/src/core/file_audit_contract.py`, blob `e6624c0b39421a01d54cf0615920073c5dd1ee0f`. Cada entrada exige `source_id`, basename seguro y `provenance`; conserva SHA-256 y tamaño; detecta Python/JSON/YAML/Markdown/texto; para Python usa AST para símbolos/dependencias/capacidades y riesgos; Markdown extrae secciones; produce arquitectura, interfaces, dependencias, capacidades, riesgos y requisitos estructurados. Riesgos como `eval`, `exec`, `compile`, `os.system`, `subprocess.Popen`, `subprocess.run` y marcadores textuales inseguros generan gate `BLOCK_AND_REVIEW`. Ask Council se normaliza solo a `ADOPT|ADAPT|REJECT|RESEARCH_MORE`, findings tipados, references, confidence y dissent; schema inválido falla cerrado. Regla crítica: `executable_action_authorized=false` siempre; Council/LLM nunca otorga ejecución, filesystem, red ni deployment. Tests `runtime/tests/test_file_audit_contract.py`, blob `d490a7e15205c37a0f476e6e4c0de7f9429f36c6`; evidence `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`; read-back PASS; simulación local equivalente `PASS_5_OF_5_ASSERTIONS`; `repo_test_execution=NOT_CLAIMED`.

## G-003 — Generación de tareas de code
Estado: `CLOSED_VERIFIED_LOCAL`.
`runtime/src/core/code_task_graph.py` transforma requisitos en tareas atómicas con id/dependencias/prioridad/capability/owner/inputs/outputs/destino/sandbox/tests/evidence/idempotency/retry/status. Mantiene `director_tasks` y `generated_tasks` separados. Reutiliza `runtime/src/core/dag_engine.py`; no añade scheduler alternativo. Evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.

## G-004 — Placement arquitectónico A–G
Estado: `CLOSED_VERIFIED_LOCAL`.
Clasificador `runtime/src/core/placement_classifier.py`, blob `69698ad30ba1903e0780efcea1952a3737aeb23e`, decide entre A Kernel, B Extension Kernel, C Reasoning Layer, D Wordflow, E Pool, F Tools, G Other usando señales de privilegio, lifecycle, estado, latencia, invariantes kernel, reasoning, agent-chain, fan-out, tool reuse e I/O. Señal insuficiente/conflictiva => `PLACEMENT_REVIEW_REQUIRED`. Evidence `G004_PLACEMENT_CLASSIFIER_2026-09-10.json`; simulación `PASS_10_OF_10_ASSERTIONS`.

## G-005 — Investigación técnica antes de crear/adaptar code
Estado: `CLOSED_VERIFIED_LOCAL`.
Política `REUSE > PATCH > ADAPT > GENERATE` implementada en `runtime/src/core/reuse_selector.py`, blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`. El selector valida source URL, licencia, mantenimiento, compatibilidad, riesgo, footprint, máximo 10 candidatos e IDs únicos; una opción externa nunca se transforma en ejecución directa, sino en `ADAPT`, y riesgo alto/compatibilidad nula obliga `RESEARCH_MORE`. Catálogo `wordflow_loop/research/reuse_catalog_g005.json`, blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`, contiene 8 opciones: DAGEngine, CodeGraphWorkspace, FileAuditContract, PlacementClassifier, Graphiti, Graphology, NetworkX y Tree-sitter. Licencias upstream verificadas: Graphiti Apache-2.0 (`5feb0d9d...`), Graphology MIT (`158967c...`), NetworkX BSD-3-Clause (`02547fc...`), Tree-sitter MIT (`971b81f...`). Tests `runtime/tests/test_reuse_selector.py`, blob `1bcd0fca22d1238d28add1880e882e7af863ad52`; read-back PASS; simulación equivalente `PASS_3_OF_3_DECISIONS`; `repo_pytest_execution=NOT_CLAIMED`. Evidence `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`. No se instaló/copió código externo.

## G-006 — Creación de code nuevo
Estado: `GAP_OPEN` y siguiente nodo 1×1.
Solo después de que G-005 produzca `GENERATE` por ausencia de candidato válido. Código mínimo, modular, tipado/schema, idempotente, fail-closed, observable y testeable. Integración exclusivamente por Enchufe Universal Fables/Ficha. LLM genera propuestas; gates deterministas autorizan o rechazan.

## G-007 — Archivo que ya contiene code ejecutable
Estado: `GAP_OPEN`.
Analizar antes de reescribir. Evaluar REUSE/PATCH/ADAPT. Copiar/mover únicamente mediante motores canónicos inmutables con source/destination explícitos, hash y read-back. Cambio de lenguaje/extensión solo si contrato de destino lo exige y conserva provenance.

## G-008 — Seguridad y neutralización
Estado: `GAP_OPEN`.
Escanear antes de ejecutar. Conducta maliciosa/insegura se bloquea; solo puede sustituirse por acción benigna funcionalmente justificable sin ejecutar primero la conducta peligrosa. Cierre requiere reason codes, gates, sandbox tests y evidencia.

## G-009 — Componente sin valor
Estado: `GAP_OPEN`.
Si no aporta capacidad, duplica sin beneficio, empeora seguridad/mantenibilidad o no puede cablearse útilmente, marcar `NO_VALUE_GAP`; producir `.md` con justificación, alternativas y revisión independiente.

## G-010 — Watchdog supervisor
Estado: `CLOSED_VERIFIED`.
Supervisa la raíz Wordflow, relee fuentes de verdad, opera 1×1, no inventa PASS, registra novedades materiales y conserva `AUTH_PROVIDER_TEST_PENDING` hasta evidencia externa real.

## G-011 — Recepción de componentes + motores copiar/mover
Estado: `GAP_OPEN`.
Entrada `source + destination` obligatoria. Motores canónicos byte-a-byte, destino explícito, hash/read-back, no LFS, no force. Fuentes externas/Core Kernel son lectura/adquisición; esta fase no escribe fuera del Wordflow.

## G-012 — Lista de descarga/extracción
Estado: `GAP_OPEN`.
Convertir lista del Director en cola determinista y usar motores canónicos con allowlist, CRC/hash, bloqueo de path traversal/symlinks cuando aplique, persistencia y read-back antes de PASS.

## G-013 — Fuentes de verdad
Estado: `GAP_OPEN`.
Core truths reconciliadas manualmente hasta checkpoint 0008. En ciclo G-005 se detectó drift real: PLAN y RECOVERY seguían en checkpoint 0005 aunque STATE/CHECKPOINT/HANDOFF estaban en 0007. Se corrige la documentación a 0008, pero G-013 no cierra: falta política automática + test de drift/conflict.

## G-014 — `agente-readme-memoria.md` de los 18 agentes
Estado: `GAP_OPEN`.
Cada agente tendrá rol, capacidades, prohibiciones, contratos, fuentes, gates, evidence format, errores aprendidos y mejoras aprobadas. Loader determinista antes de trabajo; actualización solo con aprendizaje verificado.

## G-015 — 12 GOALS entrada/salida + Council + simulaciones
Estado: `GAP_OPEN`.
Cada capacidad nueva deberá pasar 12 gates de entrada y 12 de salida, Council/Ask Council, simulaciones, refutaciones y cross-check. El razonamiento puede usar LLM, pero aceptación/estado son deterministas.

## G-016 — Conversión arquitectura Chat A ↔ Chat B
Estado: `GAP_IN_RESEARCH`.
Localizados contratos Chat-B en `runtime/docs/T001_CHAT_B_CONTRACT.md`, `T007_CHAT_B_CONTRACT.md`, `T011_CHAT_B_CONTRACT.md`. Chat-A sigue sin localizar. No crear reemplazo hasta búsqueda completa o `NOT_FOUND` probado.

## G-017 — Deployment determinista
Estado: `GAP_OPEN`.
Cadena requerida `validate → prepare/build → sandbox → tests → reviewer → promote → checkpoint → rollback/compensation`. `runtime/src/install/installation_engine.py` contiene campos PASS/health estáticos, no aceptados como prueba real.

## G-018 — Enchufe Universal Fables
Estado: `GAP_IN_RESEARCH`.
Debe confirmarse source proof canónico + Ficha/Contract. Todo módulo nuevo se registra/cablea por ese ABI; prohibidos buses paralelos o integraciones ad hoc.

## G-019 — Auditoría global del Wordflow
Estado: `GAP_OPEN`.
Inventariar capacidades, duplicados, huérfanos, rutas rotas, docs obsoletas y code no usado. Regla: no rehacer trabajo ya verificado.

## G-020 — 12 fuentes comunidad/desarrollo
Estado: `CLOSED_VERIFIED`.
Catálogo `wordflow_loop/research/community_sources.json`, blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## G-021 — Cola + paralelismo
Estado: `GAP_OPEN`.
Prioridad, dependencias, fan-out/fan-in, dedup, idempotency, límites de concurrencia y backpressure. Solo tareas independientes corren paralelas; bloqueadas esperan dependencias verificadas.

## G-022 — Sandbox → segundo reviewer → deploy
Estado: `GAP_OPEN`.
`runtime/src/uek/sandbox_manager.py` actual es descriptor lógico; no demuestra aislamiento físico de process/filesystem/network/time/memory. No cerrar hasta adapter enforceable + límites + reviewer gate + promotion rejection test.

## G-023 — Hugging Face dataset/skills bridge
Estado: `GAP_IN_RESEARCH`.
Inventario solo con conector/acceso verificable; no asumir secretos. Bridge determinista inyectará únicamente recursos aprobados y referencias, sin exponer token. `AUTH_PROVIDER_TEST_PENDING` no se altera por referencias a credenciales.

## G-024 — Separación determinismo/LLM
Estado: `GAP_OPEN`.
Contracts/scheduler/DAG/routing/FSM/state/gates/hash/sandbox/deploy/evidence son deterministas. LLM permitido en análisis/síntesis/generación/Council/clasificación semántica y siempre normalizado/validado.

## G-025 — Patrones MAVIS/PARALLEL
Estado: `GAP_OPEN`.
Evaluar 1×1 persistent pool, priority queue, cache, batching, backpressure, asyncio pipeline, dedup, Job ABI, registry/factory/DI/event bus/middleware/FSM/checkpoints/audit/tests/versioning/sandbox/capability routing, fan-out/fan-in, DLQ/outbox/multi-pool/durable recovery. Cifras de aceleración son hipótesis hasta benchmark.

## G-026 — UI/visual del LOOP
Estado: `GAP_OPEN`.
Visualizar DAG/grafo, cola, tareas, GAPs, agentes, evidence y checkpoints. Priorizar componentes existentes, mantener UI modular y no crear frontend monolítico.

## G-027 — Graphiti
Estado: `GAP_IN_RESEARCH`.
Fuente localizada en `maxbry123-commits/osquestador-auditor/graphiti`. Candidato a contexto/provenance/memoria temporal; no reemplaza DAG scheduler. G-005 confirma licencia Apache-2.0 y resultado preliminar `ADAPT`; integración solo tras copia exacta mediante motor, adapter y sandbox test.

## G-028 — Graphology
Estado: `GAP_IN_RESEARCH`.
Fuente localizada en `maxbry123-commits/osquestador-auditor/graphology`. Candidato a graph object/algoritmos/traversal/layout y backend visual tipo Sigma.js; no durable execution. G-005 confirma licencia MIT y resultado preliminar `ADAPT`; requiere copia exacta + adapter/serializer/test si se adopta.

## G-029 — Planificación organizada
Estado: `GAP_IN_RESEARCH`.
`DAGEngine` local es default REUSE y G-005 lo prioriza frente a NetworkX para capability `dag`. Comparar Dagster/Prefect/Argo/Inngest/Trigger.dev/Restate/Airflow solo contra capacidades faltantes; prohibido añadir otro orquestador sin GAP demostrado.

## G-030 — Crazy Wall multiagente
Estado: `GAP_OPEN`.
Estado lógico compartido con ownership de task/node, version/checkpoint, idempotency, optimistic concurrency y reglas de merge/conflict. Cierre de grupos conserva historial/evidence y abre siguiente grupo sin pisar agentes.

# Persistencia canónica
- `Crazy Wall Orquestador/STATE.json`
- `Crazy Wall Orquestador/CHECKPOINT.json`
- `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`
- `HANDOFF.md`
- `wordflow_loop/evidence/`

## Estado actual del grupo
30 GAPs · 7 cerrados: `G-001`, `G-002`, `G-003`, `G-004`, `G-005`, `G-010`, `G-020`.  
Siguiente nodo: `G-006`.  
`AUTH_PROVIDER_TEST_PENDING` permanece abierto. Graphiti/Graphology no están integrados todavía. Fables sigue en investigación; no se crea bus paralelo.
