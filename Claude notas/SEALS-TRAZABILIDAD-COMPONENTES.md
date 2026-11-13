# SEALS TEAM YAIWES - TRAZABILIDAD DE COMPONENTES
Version 1. Scope exclusivo: Seals Team YAIWES.

## REGLA DE TRAZABILIDAD

Ningun agente puede integrar un mecanismo por nombre, README, reputacion o inferencia.

Cada mecanismo debe resolver esta cadena antes de tocar Seals:

SOURCE_REPO
-> SOURCE_COMMIT/BLOB
-> SOURCE_FILE
-> SOURCE_SYMBOL
-> BEHAVIOR_EXTRACTED
-> SEALS_DESTINATION
-> TEST
-> EVIDENCE

Estados permitidos:
PROVEN = fuente, archivo y simbolo comprobados.
REFERENCE = patron util comprobado, pero no autorizado para copiar/integrar hasta cerrar simbolo/destino.
GAP = capacidad pedida sin implementacion/fuente demostrada.
HOST_ONLY = pertenece a Wordflow/host y Seals solo consume el contrato.
EXCLUDED = no entra en el runtime interno de Seals.

Regla fail-closed:
si SOURCE_SYMBOL esta vacio o no fue leido en el commit fijado, NO INTEGRAR.

## T-001 - BASE LOOP MINIMO

Status: PROVEN
Source repo: huggingface/smolagents
Source commit: 30bb1161095dbae2271e6bc3cc4c219cc3897a57
Copia local: Core kernel Yaiwes/Backend watchdog workflow adaptativo/adaptive-planning/smolagents/
Source file: src/smolagents/agents.py
Source symbols: MultiStepAgent, ToolOutput, ToolCallingAgent, final_answer_checks
Extraer:
- loop step-by-step action/observation
- max_steps
- ToolOutput
- gate de cierre extensible
No extraer:
- managed_agents
- delegacion/subagentes
- serializacion de flotas
Destino planificado:
- fsm_loop
- tool_result
- completion_gate
Test:
- max_steps bloquea loop infinito
- tool error vuelve como observation
- final answer sin acceptance/evidence no cierra

## T-002 - STRUCTURED TOOL PARSING Y MICRO-LOOP

Status: PROVEN
Source: copia Meta Muse Glimmer del proyecto
Source file 1: Core kernel Yaiwes/Meta-Muse-Glimmer-Agent-2026/code/agentic-fundamentals/response_parser.py
Blob SHA: 82bb70b0d3b539d1740bc7bdab3646054622aeb9
Source symbol: MuseGlimmerATEMParser.parse
Source file 2: Core kernel Yaiwes/Meta-Muse-Glimmer-Agent-2026/code/agentic-fundamentals/agent_loop.py
Blob SHA: f3087c13214e97b97d2a871f378cffaf1a393bf5
Behavior confirmado: plan -> call tool -> execute -> feed result back -> self-correct
Extraer:
- raw output -> reasoning/tool_calls/final
- tool call estructurada
- result -> observation -> correction
No extraer:
- modelo completo
- servidor/inference stack
Destino planificado:
- structured_action/parser
- fsm_loop

## T-003 - COMMAND ID / IDEMPOTENCY / REPLAY

Status: PROVEN
Source: Muse Code SDK copiado en Core kernel Yaiwes
Source file: Core kernel Yaiwes/Meta-Muse-Code-SDK-2026/code/clients/sdk-ts/src/pending/pending-command-set.ts
Blob SHA: d250ffd284ca0fb4ff42839b43155c7487d92494
Source symbols: PendingCommandEntry, ReplayAnswer, PendingJoinPlan
Extraer:
- command_id como identidad de side effect
- replay/resubmit con el mismo command_id
- conflicto para misma identidad con distinto input
- estado suficiente para evitar doble side effect
No extraer:
- cola global/scheduler propio
- autoridad durable de Wordflow
Destino planificado:
- idempotency
Test:
- mismo command_id + mismo payload -> JOIN/REPLAY
- mismo command_id + payload distinto -> IDEMPOTENCY_CONFLICT
- retry no duplica side effect

## T-004 - SAFE EDIT

Status: PROVEN
Source repo: anomalyco/opencode
Source commit: d7b115f623760e68a4749d16508a9eca350f246f
Source file: packages/opencode/src/tool/edit.ts
Source symbols: EditTool, lock(), replace()
Mecanismos comprobados:
- Semaphore por filePath
- oldString/newString exactos
- error por multiples matches
- diff
- permission antes de escribir
Source file adicional: packages/opencode/src/tool/write.ts
Source symbol: WriteTool
Extraer:
- exact-match-before-patch
- single writer local por path
- diff/receipt/read-back
No extraer:
- runtime OpenCode
- agente OpenCode
Destino planificado:
- safe_edit

## T-005 - ACTION/OBSERVATION

Status: REFERENCE
Source repo: OpenHands/OpenHands
Source commit fijado por el proyecto: f7fb0c4b21f5ed726edbba8a6309634ef434b004
Aporte aprobado:
- separar action de observation
- error/timeout/success como observacion
Restriccion:
- SOURCE_FILE/SOURCE_SYMBOL exactos del commit fijado deben localizarse antes de extraer codigo.
No extraer:
- OpenHands completo
- CodeActAgent
- controller/orquestador

## T-006 - SANDBOX/POLICY DE EJECUCION

Status: PROVEN
Source repo: openai/codex
Source commit: be6e8eac029b183056b7e4402879f15d2c85f61b
Source file 1: codex-rs/core/src/exec.rs
Source symbol: process_exec_tool_call
Source file 2: codex-rs/core/src/tools/sandboxing.rs
Source symbols: ApprovalStore, ExecApprovalRequirement, SandboxOverride, ToolRuntime
Source file 3: codex-rs/core/src/apply_patch.rs
Source symbol: prepare_apply_patch
Extraer:
- policy antes de side effect
- sandbox/workspace scope
- approval requirement
- fail-closed execution
No extraer:
- Codex agent
- multi-agent
- TUI

## T-007 - SESSION LIFECYCLE / RESUME CONTRACT

Status: PROVEN
Source repo: MoonshotAI/kimi-agent-sdk
Source commit: ed4be6be5280d02191da88bbafb3f828dcd33d72
Source file: python/src/kimi_agent_sdk/_session.py
Source symbol: Session
Metodos comprobados: create, resume, prompt, cancel, close
Extraer:
- lifecycle/resume contract
- rechazo de session cerrada o ya ejecutandose
No extraer:
- Kimi agent completo
- provider/model routing

## T-008 - PROTOCOLO TIPADO DE REQUESTS

Status: PROVEN
Source repo: MoonshotAI/kimi-agent-rs
Source commit: f9186cd20b28c02d33721c05fd248e65d56e3e53
Source file: kimi-agent/src/wire/server.rs
Source symbols: PendingRequest, WireServer
Mecanismos:
- PendingRequest distingue Approval y ToolCall
- validacion JSON-RPC
- rechazo de method/request/state invalidos
Extraer:
- estados cerrados
- invalid input -> typed failure
No extraer:
- servidor Kimi entero
- otra cola/orquestador

## T-009 - PLUGIN/CAPABILITY CONTRACT

Status: REFERENCE
Source repo: MiniMax-AI/MiniMax-Code-Plugins
Source commit: d592f422893846c2aac48f8b407a92bd0293c6b1
Source file comprobado: README.md
Contrato documentado: plugin.json + skill/MCP opcional + checks
Uso:
- referencia para manifest declarativo de capability
- adaptar al Enchufe Universal Fables
Restriccion:
- localizar schema/validator ejecutable exacto antes de copiar codigo

## T-010 - VISUAL LOOK-ACT-LOOK

Status: REFERENCE
Fuente local: wordflow_loop/agent_sources/metacua/
Archivo verificado: README.md
Blob SHA: 7b69c111150041b52a7bf32076dd914ff4fa34e8
Comportamiento:
- screenshot
- coordenadas 0-1000
- action
- screenshot nuevo
- repeat
Regla:
ACTION -> SCREENSHOT NUEVO -> VERIFY
Restriccion:
- localizar SOURCE_FILE/SOURCE_SYMBOL de implementacion antes de extraer codigo
- MetaCua nunca tiene autoridad de PASS

## T-011 - CUA SANDBOX / MCP BRIDGE

Status: REFERENCE
Fuente local: wordflow_loop/agent_sources/cua_mcp/
Archivo verificado: README.md
Blob SHA: e56ec0c9a8a48d4f2b52e9e22708a2ad46c34b8f
Comportamiento documentado:
AGENT -> MCP TOOL -> CUA SANDBOX -> ACTION -> OBSERVATION
Restriccion:
- localizar bridge/tool implementation exacta antes de extraer codigo
- CUA/MCP no decide PASS

## T-012 - META AGENT COOKBOOK

Status: REFERENCE
Fuente local: Core kernel Yaiwes/Meta-Agent-Cookbook-2026/
Capacidades solicitadas:
- acceptance-driven close
- objective oracle
- stuck detection
- safe edit patterns
Restriccion:
- registrar notebook/file/symbol exacto para cada capacidad antes de extraer codigo

## T-013 - KIMI RESEARCHER

Status: GAP
Source repo: MoonshotAI/Kimi-Researcher
Source commit: 9406d821348471bceb6d5fa0b7eba05411106f93
Hallazgo:
- el commit fijado expone una project page; no se encontro codigo ejecutable del motor multi-source/cross-check.
Decision:
- NO declarar Kimi-Researcher integrado.
Requisito Seals:
ResearchResult(query, sources, source_type, claims, cross_check, new_evidence, conclusion)
NO_NEW_EVIDENCE -> cambiar estrategia o BLOCKED_WITH_TRACE.

## T-014 - MINIMAX CODING PLAN MCP

Status: GAP PARA "PLANNER"
Source repo: MiniMax-AI/MiniMax-Coding-Plan-MCP
Source commit: 5dbf3494d7dac35d154958e0c1dab03910b89bbd
Source file revisado: minimax_mcp/server.py
Simbolos comprobados: web_search, understand_image
Hallazgo:
- no se demostro un planner estructurado.
Decision:
- prohibido etiquetarlo como planner sin SOURCE_SYMBOL adicional.

## T-015 - MINI-AGENT

Status: REFERENCE
Source repo: MiniMax-AI/Mini-Agent
Source commit: d76a4f6389688cabda39c224a6cdfa274215d47c
Source file: mini_agent/agent.py
Source symbol: Agent
Comprobado:
- single agent
- tools
- max_steps
- workspace
Uso:
- segunda referencia de arquitectura minima
Decision:
- no copiar Agent entero; smolagents es la base elegida

## T-016 - NO ENTRAN COMO AGENTES INTERNOS

Status: EXCLUDED
kimi_code @ 1fddc16e3ea2de4c26a18acd764380adf9e2ed64
kimi_cli @ 86f136422a0aae6b217ea49e7ea1d2e8a1defcd2
OpenRoom @ 02468154c4d99f8925916425bf444d672454fb3d
mmx CLI @ bfbb4cb75ec343149eaccfd668c5011aa27bcf2b
mcode @ 73a2581c6c7525628342f33b53907d4f7bdc146e

Pueden estudiarse como fuentes; no quedan vivos dentro de Seals.

## T-017 - MCP GENERICO MINIMAX

Status: HOST_ONLY / REFERENCE
MiniMax-MCP @ 0856b9aef8a9d676bb63bdd6b6426d7b640a3b7a
MiniMax-MCP-JS @ 8032f830203a1c61e56760b1680db923654bcb1b
Decision:
- no forman el cerebro de Seals
- si Wordflow/Command Center usa MCP compartido, Seals recibe tools/contexto por contrato
- MCP nunca aporta autoridad

## T-018 - DAG / CLAIM / LEASE / QUEUE / WATCHDOG

Status: HOST_ONLY
Owner: Wordflow central
Seals consume:
node_id, mission_id, claim_id, lease_id, write_scope, base_sha, acceptance, work_surface, capability, secret_refs, command_id.
Seals puede:
validar, reportar heartbeat, checkpoint, gap, evidence y release.
Seals NO crea:
- DAG global
- durable queue global
- scheduler
- watchdog/reenqueue global
- segundo claim manager
- segundo provider router

## T-019 - MOTORES CANONICOS DE SEALS COMO TOOLS

Status: HOST_TOOL / COPY_EXACT / BUILD_TASK

Decision arquitectonica:
los motores NO viven dentro de seals_core.
Se copian 1:1 dentro de Wordflow como adapters/tools fisicos y Seals los consume
mediante schemas tipados.

Destino exacto de codigo:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/adapters/seals_motors/`

Destino exacto de schemas:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/contracts/seals_motors/`

Fuente canonica:
`maxbry123-commits/frontend@main`

Motores requeridos:

1. EXTRACT
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/➡️📂 Motor de extracción zip/motor_1_extract_only.py`
Blob SHA:
`a52d5dc0e6ff26f75d753b848dcc1a40c5dd4500`
Source symbol:
`main()`
Schema requerido:
`extract_only.schema.json`

2. DOWNLOAD_EXTRACT_QUEUE
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`
Blob SHA:
`84d566e2ee4e98e42eb3a864026d067d48caabd9`
Source symbols:
`main(), run_item(), balance()`
Schema requerido:
`download_extract_queue.schema.json`

3. DOWNLOAD_EXTRACT_ENGINE
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`
Blob SHA:
`91e6e4486692eab314be5c7130d8310d3c855397`
Source symbol:
`main()`
Schema:
forma parte de `download_extract.schema.json`; no exponer un segundo cerebro.

4. COPY
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/➡️📂motor de copiar archivos/motor_3_copy_batches.py`
Blob SHA:
`3689924361ce4a1a9fde4ae2b6f6009c37a6042d`
Source symbols:
`main(), manifest(), copy_verified()`
Schema requerido:
`copy_batches.schema.json`

5. MOVE
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/➡️📂motor de moves archivos/motor_4_move_batches.py`
Blob SHA:
`9a21facfe11327cf60a2afca8f415ad52f0ecbe5`
Source symbols:
`main(), first_manifest(), move_verified()`
Schema requerido:
`move_batches.schema.json`

6. ZIP_ROOT
Source file:
`➡️📂motores de descarga extracción copiado movimiento archivos fromtend/📂Motor descarga de componentes y extracción de zip/motor_5_zip_root.py`
Blob SHA:
`2516d85d81f691f86c32a70b90c2599639eb83c6`
Source symbols:
`main(), inventory(), build_zip(), verify_zip()`
Schema requerido:
`zip_root.schema.json`
Funcion:
empaquetar una raiz completa a ZIP excluyendo cualquier `.git/`, conservando
el resto del arbol, con manifest + tree_sha256 + zip_sha256 + read-back.
Estado:
`CODE_CREATED / RUNTIME_TEST_PENDING`.

Regla de copia:
- fetch desde fuente canonica;
- comparar blob SHA;
- copiar contenido EXACTO;
- releer destino;
- blob SHA destino debe ser IDENTICO;
- si cambia una sola linea -> `MOTOR_CODE_LOCK_GAP`;
- PROHIBIDO adaptar/refactorizar el motor copiado.

Regla de exposicion como tool:
schema -> validacion -> Sheriff/Policy -> adapter/motor -> ToolResult/receipt.

El schema puede mapear inputs/outputs, pero NO puede reescribir la logica del motor.

Inputs minimos por schema:
- extract: ARCHIVE_INPUT, DEST_DIR, STATE_FILE
- download_extract: SOURCE_REPO/ref o queue contract + destinos explicitos
- copy: SOURCE_DIR, DEST_DIR, STATE_FILE, BATCH_SIZE
- move: SOURCE_DIR, DEST_DIR, STATE_FILE, BATCH_SIZE
- zip_root: ROOT_DIR, OUTPUT_ZIP, MANIFEST_PATH, COLLISION_POLICY

Acceptance de esta tarea:
- 6 archivos fisicos en `adapters/seals_motors/`;
- cada blob coincide con la fuente canonica;
- 5 schemas de tool en `contracts/seals_motors/`;
- schema invalid -> no ejecucion;
- motor error -> ToolResult FAILED/OBSERVATION;
- test real por cada tool;
- evidence con source blob, destination blob, command, exit_code y read-back.

PROHIBIDO:
- crear un downloader/copy/move alternativo;
- meter los motores dentro de seals_core;
- modificar motores para hacerlos encajar;
- declarar integrado solo porque el archivo exista.

## T-020 - ORACLE Y EVIDENCE

Status: CORE REQUIREMENT
Base reutilizable:
- smolagents final_answer_checks @ 30bb116...
- receipts de tools/sandbox/safe-edit
Regla:
LLM_OPINION != OBJECTIVE_ORACLE
TEST -> ACCEPTANCE -> EVIDENCE -> COMPLETION AUDIT -> PASS
EvidenceRecord minimo:
path, sha256, receipt, test, exit_code, artifact, source_commit, timestamp, mission_id/node_id, acceptance_id.
PASS sin evidence valida = INVALID_STATE.

## T-021 - PLAN_MODE AVANZADO NATIVO

Status: CORE REQUIREMENT / DESIGN_NATIVE / OFFICIAL_REFERENCE_VERIFIED

Fuentes oficiales verificadas:
- https://code.claude.com/docs/en/agent-sdk/python
  - PermissionMode incluye "plan".
  - La documentacion describe "plan" como planning mode sin ejecucion.
  - La referencia expone ExitPlanMode para presentar el plan y recibir aprobacion.
- https://code.claude.com/docs/en/commands
  - /plan cambia a Plan Mode antes de cambios grandes.
- https://code.claude.com/docs/en/desktop
  - Plan mode permite leer/explorar y proponer un plan sin editar source code.
  - La UI puede cambiar modos; el atajo/control de UI no es autoridad del kernel.

Regla:
estas fuentes definen comportamiento de referencia, NO codigo a copiar.
Seals implementa PLAN_MODE de forma nativa con FSM + StructuredAction +
Sheriff/Policy + Evidence. No se integra Claude Code ni codigo propietario.



Destino:
- ExecutionMode enum
- PlanContract
- PlanGate
- transiciones PLAN/EXECUTE/REPLAN

Contrato:
`ExecutionMode = PLAN | EXECUTE`

PlanContract:
plan_id
mission_id
node_id
goal_id
base_sha
write_scope
objective
acceptance[]
evidence_refs[]
findings[]
actions[]
dependencies[]
expected_outputs[]
rollback[]
unknowns[]
created_from_state_hash
plan_sha256

Reglas:
- PLAN_MODE solo read/list/search/inspect/hash/research.
- mutacion en PLAN_MODE -> PLAN_MODE_SIDE_EFFECT_DENIED.
- EXECUTE requiere PlanGate PASS.
- toda mutacion requiere plan_id + action_id.
- target fuera de write_scope -> DENY.
- base_sha drift -> PLAN_STALE -> REPLAN.
- REPLAN conserva evidence anterior.
- Shift+Tab, si existe UI, solo emite SET_MODE; no es autoridad.

Tests:
PLAN_MODE_MUTATION_DENIED
EXECUTE_WITHOUT_PLAN_DENIED
UNPLANNED_MUTATION_DENIED
STALE_PLAN_DENIED
PLAN_ACTION_SCHEMA_INVALID
PLAN_WRITE_SCOPE_ESCAPE
PLAN_ACCEPTANCE_UNCOVERED
VALID_PLAN_EXECUTES
GAP_REPLAN_PRESERVES_EVIDENCE

Trazabilidad de implementacion obligatoria:
- OFFICIAL_SOURCE_1 = https://docs.claude.com/en/api/agent-sdk/python
- OFFICIAL_SOURCE_2 = https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- SOURCE_BEHAVIOR = permission_mode plan + ExitPlanMode + plan-validate-execute-verify
- YAIWES_DESIGN = ExecutionMode + PlanContract + PlanGate + SET_MODE + Policy
- PROHIBIDO copiar codigo propietario o declarar equivalencia de implementacion.
- Test/evidence deben demostrar solo el comportamiento YAIWES especificado.

Trazabilidad:
este mecanismo NO se extrae de un agente externo; es diseño nativo YAIWES.
Las fuentes externas solo sirven como referencia de comportamiento.
Por tanto no se requiere SOURCE_SYMBOL externo para implementarlo.

## T-022 - AGENT SKILLS STANDARD

Status: PROVEN / OFFICIAL_SPEC / BUILD_INPUT

Official specification:
https://agentskills.io/specification

Anthropic reference repo:
https://github.com/anthropics/skills

Pinned commit:
34040c9c568585f6929bedeaad110ad08f079624

Source files:
- spec/agent-skills-spec.md
  blob: 772512097afe01955bd635c46b71cd351ce42e9a
- template/SKILL.md
  blob: 50a4f9b104357d96361e257adb70454604cd15c0

Verified standard used by YAIWES:
- skill directory contains SKILL.md;
- SKILL.md = YAML frontmatter + Markdown body;
- required frontmatter: name, description;
- optional: license, compatibility, metadata, allowed-tools;
- scripts/, references/, assets/ are optional;
- progressive disclosure is expected;
- validation can use the reference library documented by the standard.

YAIWES destination:
`➡️ 📂 shema skills agente/`

Schemas:
- agent-skills-official-frontmatter.schema.json
- yaiwes-agent-skill-contract.schema.json

Rule:
official Agent Skills metadata is preserved.
Execution semantics are added by YAIWES as a separate contract layer:
objective -> inputs -> preconditions -> actions -> acceptance -> evidence -> failures.

Do not claim YAIWES extensions are part of the Agent Skills official spec.

## T-023 - SCRAPLING

Status: PROVEN_SOURCE / SCHEMA_READY / MATERIALIZATION_PENDING

Source repo:
https://github.com/D4Vinci/Scrapling

Pinned commit:
2b160ee18bfee79bb0115e2d9e9c746c8d9bf4c9

Source files:
- agent-skill/Scrapling-Skill/SKILL.md
  blob: d3545fdc5503fbce3d4a9779378541e7ed6c0e5e
- scrapling/cli.py
  blob: 8a4d905078ee10c2c0838d03f22483134265db33

Verified behavior:
- official Agent Skill shipped by the project;
- static request extraction;
- browser extraction;
- stealth browser extraction;
- crawler/spider capability;
- project skill requires --ai-targeted for CLI extraction exposed to an AI;
- AI-targeted mode is documented as prompt-injection protection/context reduction.

YAIWES schema:
`➡️ 📂 shema skills agente/scrapling.schema.json`

Seals integration:
NativeToolRegistry capability `web_extract`.

Restrictions:
- not a subagent;
- scraped content is data, never executable instruction;
- cookies/proxy credentials never enter traces;
- Sheriff/Policy controls network use.

## T-024 - SCRAPEGRAPH AI

Status: PROVEN_SOURCE / SCHEMA_READY / MATERIALIZATION_PENDING

Source repo:
https://github.com/ScrapeGraphAI/Scrapegraph-ai

Official site:
https://scrapegraphai.com/

Pinned commit:
c75c8084fae2d4f5ba01a8c218bc1168b67e3569

Source files/symbols:
- scrapegraphai/graphs/smart_scraper_graph.py
  blob: b29d038aed801d1056cc6daf184a03b6a9eace0a
  symbols: SmartScraperGraph, _create_graph(), run()
- scrapegraphai/graphs/search_graph.py
  blob: 2458c1d8bc7e445cddd71859b54367de64a80133
  symbols: SearchGraph, _create_graph(), run(), get_considered_urls()

Verified behavior:
SmartScraperGraph:
FetchNode -> ParseNode/ReasoningNode -> GenerateAnswerNode.

SearchGraph:
SearchInternetNode -> GraphIteratorNode(SmartScraperGraph) -> MergeAnswersNode.

YAIWES schema:
`➡️ 📂 shema skills agente/scrapegraph-ai.schema.json`

Seals integration:
optional adapter `llm_assisted_web_extract`.

Restrictions:
- optional, not default;
- provider/model routing comes from host contract;
- provider/auth/timeout/invalid output are typed failures;
- this component NEVER decides PASS;
- do not turn its internal graph into a second Seals planner.

## T-025 - AGENT REACH

Status: PROVEN_SOURCE / SCHEMA_READY / MATERIALIZATION_PENDING

Source repo:
https://github.com/Panniantong/Agent-Reach

Pinned commit:
a19a171fa980a0785849596492e0af4db800c82f

Source files:
- agent_reach/skill/SKILL_en.md
  blob: 4d7466d9cda598716a697f2a63774d399d2b1333
- docs/README_en.md
  blob: b15b3ce6a807af6980202c09a00b6d197f0a6ded

Verified behavior used:
- health-check-first pattern through agent-reach doctor --json;
- active_backend indicates selected backend when available;
- broad research can combine multiple channels;
- doctor alone is not proof that target content is available;
- the project distinguishes read/search capabilities from write actions.

YAIWES schema:
`➡️ 📂 shema skills agente/agent-reach.schema.json`

Seals integration:
optional read-only adapter `multi_platform_research`.

Restrictions:
- read-only integration;
- no posting/commenting/liking;
- authenticated channels require user-controlled session/credentials;
- never expose cookies/tokens;
- do not import Agent Reach as a second router/orchestrator.

## T-026 - SOURCE MATERIALIZATION FOR AGENT SKILLS

Status: BUILD_TASK / MOTOR2_REQUIRED

Queue:
`➡️ 📂 shema skills agente/DOWNLOAD-EXTRACT-QUEUE.json`

Canonical motor:
`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`

Canonical engine:
`➡️📂motores de descarga extracción copiado movimiento archivos agentes/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`

Expected destination after Motor 2:
`➡️ 📂 shema skills agente/sources/<slug>/code/`

Required queue items:
- anthropics/skills @ 34040c9c568585f6929bedeaad110ad08f079624
- D4Vinci/Scrapling @ 2b160ee18bfee79bb0115e2d9e9c746c8d9bf4c9
- ScrapeGraphAI/Scrapegraph-ai @ c75c8084fae2d4f5ba01a8c218bc1168b67e3569
- Panniantong/Agent-Reach @ a19a171fa980a0785849596492e0af4db800c82f

PASS:
- Motor 2 returns VERIFIED_CLOSED for all 4;
- source_commit equals pinned commit;
- extraction_verified=true;
- read-back tree hash matches;
- schema source refs match materialized files.

Until then:
`SOURCE_MATERIALIZATION_PENDING`.

## COMPONENT BUDGET

Objetivo:
500-1000 LOC de codigo propio/adaptado para el micro-agente y adapters finos.

Si un mecanismo exige otro agente completo, otra cola, otro scheduler o un segundo kernel:
NO ENTRA.

## CIERRE DE TRAZABILIDAD

Antes de integrar:
1. leer commit fijado
2. abrir source file
3. fijar symbol
4. definir behavior exacto
5. definir destino
6. test rojo
7. adaptar
8. test verde
9. read-back
10. evidence SHA256

Sin los diez puntos: NO INTEGRADO.
