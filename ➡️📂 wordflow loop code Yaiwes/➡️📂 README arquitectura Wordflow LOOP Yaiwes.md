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
Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0019`.  
Nodo activo de SOL_1: `G013_SOURCE_TRUTH_RECONCILIATION`.  
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
Estado: `BLOCKED_DEPENDENCY_G018`.
La política existe, pero solo puede cerrar después de que G-018 demuestre source proof + Ficha/contract + registro/test de Fables. Solo después de que G-005 produzca `GENERATE` por ausencia de candidato válido. Código mínimo, modular, tipado/schema, idempotente, fail-closed, observable y testeable. Integración exclusivamente por Enchufe Universal Fables/Ficha. LLM genera propuestas; gates deterministas autorizan o rechazan.

## G-007 — Archivo que ya contiene code ejecutable
Estado: consultar `Crazy Wall Orquestador/TASK-NODES.json`; no reabrir si está PASS. Analizar antes de reescribir. Evaluar REUSE/PATCH/ADAPT. Copiar/mover únicamente mediante motores canónicos inmutables con source/destination explícitos, hash y read-back.

## G-008 — Seguridad y neutralización
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS. Conducta insegura se bloquea antes de ejecución y solo puede sustituirse por acción benigna funcionalmente justificable.

## G-009 — Componente sin valor
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS. `NO_VALUE_GAP` exige justificación, alternativas y revisión independiente.

## G-010 — Watchdog supervisor
Estado: `CLOSED_VERIFIED`.
Supervisa la raíz Wordflow, relee fuentes de verdad, opera 1×1, no inventa PASS y conserva `AUTH_PROVIDER_TEST_PENDING` hasta evidencia externa real.

## G-011 — Recepción de componentes + motores copiar/mover
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS. Motores canónicos byte-a-byte, destino explícito, hash/read-back, no LFS, no force.

## G-012 — Lista de descarga/extracción
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS. Cola/intake determinista con allowlist, CRC/hash, path safety y read-back.

## G-013 — Fuentes de verdad
Estado: `RECONCILING_CHECKPOINT_0019`, owner `SOL_1`.
Contrato `yaiwes.truth_reconciliation/v1` en `runtime/src/core/source_truth_reconciler.py`, blob físico actual `fb93ce9ee5b86439b0ba36ef72c404134d1984b1`; tests físicos `runtime/tests/test_source_truth_reconciler.py`, blob `f39cb13a84d1dbb7fcb1c1467f712bf003a431df`. STATE/CHECKPOINT son anchors; conflicto falla cerrado. El parser histórico acepta un único marcador explícito `Checkpoint canónico:` y rechaza marcadores canónicos contradictorios. Cierre actual: read-back 8/8 de README/STATE/CHECKPOINT/BITÁCORA/GAPS/HANDOFF/PLAN/RECOVERY en `0019` + reconciliador/tests + evidencia actualizada.

## G-014 — `agente-readme-memoria.md` de los 18 agentes
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-015 — 12 GOALS entrada/salida + Council + simulaciones
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-016 — Conversión arquitectura Chat A ↔ Chat B
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-017 — Deployment determinista
Estado: `PENDING` dependiente de G-022. No aceptar PASS/health estáticos como prueba real.

## G-018 — Enchufe Universal Fables
Estado: `CLAIMED` por `SOL_2`; SOL_1 no lo toca. G-006 sigue bloqueado por esta dependencia.

## G-019 — Auditoría global del Wordflow
Estado: `PENDING`, depende de G-013. Solo será elegible después del cierre verificado de G-013 y read-back fresco.

## G-020 — 12 fuentes comunidad/desarrollo
Estado: `CLOSED_VERIFIED`.
Catálogo `wordflow_loop/research/community_sources.json`, blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## G-021 — Cola + paralelismo
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-022 — Sandbox → segundo reviewer → deploy
Estado: `BLOCKED_PHYSICAL_ISOLATION`. No cerrar hasta aislamiento enforceable de process/filesystem/network/time/memory con prueba positiva real.

## G-023 — Hugging Face dataset/skills bridge
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-024 — Separación determinismo/LLM
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-025 — Patrones MAVIS/PARALLEL
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-026 — UI/visual del LOOP
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-027 — Graphiti
Estado: consultar `TASK-NODES.json`; source localizado no equivale a integración.

## G-028 — Graphology
Estado: consultar `TASK-NODES.json`; source localizado no equivale a integración.

## G-029 — Planificación organizada
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

## G-030 — Crazy Wall multiagente
Estado: consultar `TASK-NODES.json`; no reabrir si está PASS.

# Persistencia canónica
- `Crazy Wall Orquestador/STATE.json`
- `Crazy Wall Orquestador/CHECKPOINT.json`
- `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`
- `HANDOFF.md`
- `wordflow_loop/evidence/`

## Estado operativo actual de SOL_1
Checkpoint `0019`. Nodo único actual `G-013`, reclamado por `SOL_1`, con GAP `SOURCE_OF_TRUTH_DRIFT`. `G-018` pertenece a `SOL_2` y no se toca. `G-019` permanece pendiente hasta que G-013 cierre. `AUTH_PROVIDER_TEST_PENDING` permanece abierto.

## Motor de descarga — recuperación 2026-09-17

Autoridad operativa: `Crazy Wall Orquestador/MOTOR-DESCARGA-RECOVERY-CHECKPOINT-2026-09-17.json`.

Flujo vigente:
`READ_FRESH → RESEARCH → MOTOR DOWNLOAD/EXTRACT/COPY/MOVE → SHA/READBACK → GAP/FIX/RETEST → README → CRAZY WALL → EVIDENCE → VALIDACIÓN FINAL`.

Destino de fuentes de agentes:
`wordflow_loop/agent_sources/`.

Orca ya está replicado y verificado en ese destino. CL-002/003/004 permanecen fail-closed hasta publicación/read-back físico de MiniMax/Kimi/mcode; una descarga temporal o una extracción remota no equivale a entrega.

## Notas de integración — componentes MiniMax / Kimi / Orca — auditoría 2026-09-18

Regla de verdad: **descarga/extracción temporal verificada no equivale a presencia física en `wordflow_loop/agent_sources/` ni a integración runtime**. Solo Orca está publicado físicamente en el destino nuevo en este checkpoint.

| Componente | Evidencia de adquisición | Presencia física en agent_sources | Nota de integración |
|---|---|---|---|
| Orca | Motor 3; tree `4a70b119890500c638cdc5e5115bc13a97fee974`; commit `50b657b4a914f6fcc4452f1cb74cc08ff08146c6` | **SÍ**: `agent_sources/orca` | Fuente interna ya replicada. No implica runtime PASS por sí sola. |
| MiniMax Mini-Agent | commit `d76a4f6389688cabda39c224a6cdfa274215d47c`; Motor 2 dry-run verificado | **NO** | CL-006 clasificación → CL-007 fleet si pasa gates → CL-008 transporte. |
| MiniMax OpenRoom | commit `02468154c4d99f8925916425bf444d672454fb3d`; Motor 2 dry-run verificado | **NO** | CL-006 clasificar UI/agent; CL-010 solo si aporta valor único. |
| MiniMax mmx CLI | commit `bfbb4cb75ec343149eaccfd668c5011aa27bcf2b`; Motor 2 dry-run verificado | **NO** | CL-010 infraestructura; no crear bus paralelo. |
| MiniMax Code Plugins | commit `d592f422893846c2aac48f8b407a92bd0293c6b1`; Motor 2 dry-run verificado | **NO** | CL-010 capa plugin detrás de ports/bus existentes. |
| MiniMax MCP | commit `0856b9aef8a9d676bb63bdd6b6426d7b640a3b7a`; 28 archivos; tree hash `cf3ed570...` | **NO** | CL-010 MCP port. |
| MiniMax MCP JS | commit `8032f830203a1c61e56760b1680db923654bcb1b`; 38 archivos; tree hash `d3d0e65f...` | **NO** | CL-010 MCP JS port. |
| MiniMax Coding Plan MCP | commit `5dbf3494d7dac35d154958e0c1dab03910b89bbd`; 27 archivos; tree hash `daa6bf47...` | **NO** | CL-010 planning capability. |
| @minimax-ai/code / mcode | npm `0.4.10`; shasum `f4564e4fe8c92f4f496efb75e9718b28716be126`; instalación efímera PASS | **NO** | CL-003 adquisición física → CL-007 fleet → CL-008 ACP/stdio. |
| Kimi Code | commit `1fddc16e3ea2de4c26a18acd764380adf9e2ed64`; Motor 3: 4.471 archivos, symlink materializado | **NO** | CL-004 publicación → CL-007 fleet → CL-008 ACP/stdio. |
| Kimi CLI | commit `86f136422a0aae6b217ea49e7ea1d2e8a1defcd2`; Motor 3: 988 archivos, 2 symlinks materializados | **NO** | CL-004 publicación; CL-011 legacy/fallback solo si demuestra valor. |
| Kimi Agent SDK | commit `ed4be6be5280d02191da88bbafb3f828dcd33d72`; Motor 2 dry-run verificado | **NO** | CL-011 SDK/transport. |
| Kimi Agent RS | commit `f9186cd20b28c02d33721c05fd248e65d56e3e53`; 172 archivos; tree hash `39a2cc96...` | **NO** | CL-011 SDK/transport. |
| Kimi Researcher | commit `9406d821348471bceb6d5fa0b7eba05411106f93`; 16 archivos; tree hash `ce5d2be3...` | **NO** | CL-011 research capability, sujeto a NO_VALUE_GAP. |

**GAP común de publicación:** `PUBLISH_TRANSPORT_SECURITY_GATE`. La adquisición/verificación existe, pero los 13 objetivos nuevos MiniMax/Kimi/mcode todavía no cuentan como entregados físicamente en `agent_sources/`. No marcar CL-002/003/004 como PASS hasta presencia física + hash/read-back en `main`.
