# ANEXO B - SEALS TEAM YAIWES: ARQUITECTURA Y MECANISMOS
Version 2. Reparacion quirurgica aprobada.
Scope exclusivo: Seals Team YAIWES.

## DECISION CONGELADA

Seals Team YAIWES es UN SOLO micro-agente/worker especializado.

No se copian agentes completos.
No se ejecutan subagentes dentro de Seals.
No se crea un segundo Wordflow, scheduler, DAG, cola global, watchdog ni provider router.

Objetivo de tamano:
500-1000 LOC de codigo propio/adaptado para el core y adapters finos.

Firma objetivo:

SealsWorker.execute(TaskContract) -> NodeResult

Microflujo:

TASK CONTRACT
-> BOOTSTRAP/VALIDATE
-> FSM
-> RESEARCH si aplica
-> STRUCTURED ACTION
-> SHERIFF/POLICY
-> TOOL/ADAPTER
-> TOOL RESULT
-> OBSERVATION
-> GAP/FIX/RETEST
-> OBJECTIVE ORACLE
-> EVIDENCE
-> COMPLETION AUDIT
-> NODE RESULT

Regla central:
LLM = PROPONE
POLICY/SHERIFF = AUTORIZA
TOOL = EJECUTA
RECEIPT = DEMUESTRA
ORACLE = DECIDE PASS

## CLASIFICACION OBLIGATORIA

CORE:
vive dentro del micro-Seals.

HOST_CONTRACT:
lo posee Wordflow; Seals lo recibe, valida y respeta.

VALIDATION:
sirve para probar Seals; no forma parte del runtime interno.

GAP:
requisito real cuya implementacion/fuente todavia no esta demostrada.

La trazabilidad exacta vive en:
Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md

## CORE APROBADO

El core puede contener solamente:

- TaskContract y contratos tipados.
- WorkerBootstrap/validacion fail-closed.
- FSM/loop del worker.
- StructuredAction/parser.
- ToolRegistry fino.
- policy adapter hacia Sheriff.
- command_id + payload_fingerprint + replay/conflict.
- safe edit + read-back.
- ToolResult/Observation.
- failure classification.
- stuck detection.
- objective oracle determinista.
- EvidenceRecord + completion audit.
- adapters finos para acquisition/research/visual.

No puede contener:

- managed_agents/subagents.
- OpenCode/OpenHands/Codex como agentes internos.
- Kimi/MiniMax agents completos.
- durable queue global.
- DAG global.
- scheduler.
- watchdog/reenqueue global.
- claim/lease manager global.
- provider/key pool.
- Command Center.

## HOST CONTRACT - WORDFLOW

Wordflow conserva:

DAG
-> node assignment
-> global claim/lease
-> durable queue/recovery scheduling
-> watchdog/reenqueue
-> global write-scope arbitration
-> provider/key routing
-> autoridad global de estado.

Seals recibe:

node_id
mission_id
claim_id
lease_id
write_scope
base_sha
acceptance[]
work_surface
capability
secret_refs
command_id

Seals hace:

validate
-> heartbeat/checkpoint
-> execute
-> record gap/evidence
-> release/report
-> NodeResult

Las pruebas de claim collision, lease expiry, reenqueue, 3 workers y 50 mundos son VALIDATION/INTEGRATION con Wordflow.
NO justifican meter esos motores dentro de Seals.

## MECANISMOS FUENTE APROBADOS

### smolagents

Base elegida para el loop minimo.

Commit:
30bb1161095dbae2271e6bc3cc4c219cc3897a57

Extraer:
MultiStepAgent step loop
max_steps
ToolOutput
patron de final_answer_checks

Eliminar/NO usar:
managed_agents
delegacion/subagentes

### Muse Glimmer

Fuentes locales verificadas:

agent_loop.py
blob f3087c13214e97b97d2a871f378cffaf1a393bf5

response_parser.py
blob 82bb70b0d3b539d1740bc7bdab3646054622aeb9

Extraer:

raw -> typed tool call
reason -> action -> result -> observation -> correction
tool errors -> observation

No ejecutar texto libre como comando.

### Muse Code SDK

Fuente:

pending-command-set.ts
blob d250ffd284ca0fb4ff42839b43155c7487d92494

Extraer:

command identity
replay/resubmit seguro
idempotency conflict
estado suficiente para evitar doble side effect

NO extraer una cola/scheduler global dentro de Seals.
La durabilidad global pertenece a Wordflow.

### OpenCode

Commit:
d7b115f623760e68a4749d16508a9eca350f246f

Fuente:
packages/opencode/src/tool/edit.ts

Simbolos:
EditTool
lock()
replace()

Extraer:
exact-match-before-patch
single writer local por path
diff
permission-before-write
read-back

OpenCode no queda ejecutandose como agente interno.

### OpenHands

Commit fijado:
f7fb0c4b21f5ed726edbba8a6309634ef434b004

Uso aprobado:
patron Action -> Observation
success/error/timeout

Estado:
REFERENCE hasta fijar SOURCE_FILE/SOURCE_SYMBOL exactos del commit.

OpenHands no queda ejecutandose dentro de Seals.

### Codex

Commit:
be6e8eac029b183056b7e4402879f15d2c85f61b

Fuentes:

codex-rs/core/src/exec.rs
-> process_exec_tool_call

codex-rs/core/src/tools/sandboxing.rs
-> ApprovalStore
-> ExecApprovalRequirement
-> SandboxOverride
-> ToolRuntime

codex-rs/core/src/apply_patch.rs
-> prepare_apply_patch

Extraer:
policy
sandbox
approval
fail-closed execution

Codex no queda ejecutandose como agente interno.

### Kimi Agent SDK

Commit:
ed4be6be5280d02191da88bbafb3f828dcd33d72

Fuente:
python/src/kimi_agent_sdk/_session.py

Simbolo:
Session

Extraer:
session lifecycle/resume contract

No extraer el agente Kimi.

### Kimi Agent RS

Commit:
f9186cd20b28c02d33721c05fd248e65d56e3e53

Fuente:
kimi-agent/src/wire/server.rs

Simbolos:
PendingRequest
WireServer

Extraer:
typed request/state validation

No crear un segundo wire/orchestrator dentro de Seals.

### MiniMax Code Plugins

Commit:
d592f422893846c2aac48f8b407a92bd0293c6b1

Uso:
referencia para manifest declarativo de capability/plugin
adaptado al Enchufe Universal Fables.

Estado:
REFERENCE hasta fijar schema/validator ejecutable exacto.

### MetaCua

Fuente local:
wordflow_loop/agent_sources/metacua/

README blob:
7b69c111150041b52a7bf32076dd914ff4fa34e8

Patron aprobado:

SCREENSHOT
-> ACTION
-> SCREENSHOT NUEVO
-> VERIFY

Coordenadas normalizadas 0-1000.

Estado:
REFERENCE hasta fijar SOURCE_FILE/SOURCE_SYMBOL de implementacion.

Nunca autoridad de PASS.

### CUA-MCP

Fuente local:
wordflow_loop/agent_sources/cua_mcp/

README blob:
e56ec0c9a8a48d4f2b52e9e22708a2ad46c34b8f

Patron:

Seals
-> approved MCP tool
-> isolated CUA sandbox
-> observation

Estado:
REFERENCE hasta fijar bridge/source symbol.

Nunca autoridad de PASS.

## COMPONENTES EN GAP O DESCARTADOS COMO CORE

### Kimi-Researcher

Commit:
9406d821348471bceb6d5fa0b7eba05411106f93

Estado:
GAP.

Hallazgo:
la fuente fijada auditada expone project page; no se demostro codigo ejecutable del motor multi-source/cross-check.

Decision:
NO declarar P1-18 cerrado con Kimi-Researcher hasta localizar codigo real.

El requisito permanece:

ResearchResult(
query,
sources,
source_type,
claims,
cross_check,
new_evidence,
conclusion
)

NO_NEW_EVIDENCE
-> cambiar estrategia
o
-> BLOCKED_WITH_TRACE

### MiniMax-Coding-Plan-MCP

Commit:
5dbf3494d7dac35d154958e0c1dab03910b89bbd

Archivo auditado:
minimax_mcp/server.py

Simbolos comprobados:
web_search
understand_image

Estado para "planner":
GAP.

No llamarlo planner de Seals sin localizar un simbolo que implemente planificacion estructurada.

### Meta Agent Cookbook

Estado:
REFERENCE.

Antes de extraer objective oracle/stuck/safe-edit:
fijar file + symbol exactos.

No declarar mecanismo integrado por descripcion del cookbook.

### Mini-Agent

Commit:
d76a4f6389688cabda39c224a6cdfa274215d47c

Uso:
segunda referencia de agente minimo.

No copiar Agent entero.
smolagents es la base escogida.

### No entran como agentes internos

kimi_code
@ 1fddc16e3ea2de4c26a18acd764380adf9e2ed64

kimi_cli
@ 86f136422a0aae6b217ea49e7ea1d2e8a1defcd2

OpenRoom
@ 02468154c4d99f8925916425bf444d672454fb3d

mmx CLI
@ bfbb4cb75ec343149eaccfd668c5011aa27bcf2b

mcode
@ 73a2581c6c7525628342f33b53907d4f7bdc146e

Pueden estudiarse como fuente.
No quedan vivos dentro de Seals.

### MCP generico MiniMax

MiniMax-MCP
@ 0856b9aef8a9d676bb63bdd6b6426d7b640a3b7a

MiniMax-MCP-JS
@ 8032f830203a1c61e56760b1680db923654bcb1b

Clasificacion:
HOST_ONLY / REFERENCE.

El servidor de contexto compartido pertenece al host/Command Center, no al cerebro de Seals.

## NATIVE TOOLSET - MOTORES INTEGRADOS EN SEALS

Decision aprobada:

Los motores son capacidades NATIVAS del agente Seals Team YAIWES.

Arquitectura:

SEALS CORE
-> NativeToolRegistry
-> schema tipado
-> Sheriff/Policy
-> adapter fisico Wordflow
-> motor canonico exacto
-> ToolResult
-> receipt/evidence

La implementacion fisica NO se pega dentro de `seals_core`.
Se mantiene separada para preservar el limite de 500-1000 LOC, pero el runtime
de Seals los registra como tools nativas disponibles directamente por nombre.

Codigo fisico:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/adapters/seals_motors/`

Contratos:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/contracts/seals_motors/`

Tools nativas obligatorias:
- `download_extract`
- `extract_only`
- `copy_batches`
- `move_batches`
- `zip_root`

Regla:
Seals NO llama scripts por nombre libre.
Solo puede invocar un motor mediante una StructuredAction que resuelva a un
tool_name registrado + schema valido + Policy PASS.

Los motores 1-4 se copian 1:1 desde la fuente canonica y deben conservar blob SHA.
Motor 5 `motor_5_zip_root.py` tambien queda bloqueado por blob SHA:
`2516d85d81f691f86c32a70b90c2599639eb83c6`.

No integrar un motor significa que Seals queda INCOMPLETO para acquisition/integration.

## PLAN_MODE AVANZADO - NATIVO DEL CORE

Referencia de comportamiento:
Claude Code Plan Mode se usa como modo de exploracion/planificacion sin mutaciones.
El atajo de UI no forma parte del kernel Seals.

Seals implementa su propia version nativa mediante FSM + Policy.

Estados:

BOOTSTRAP
-> PLAN_MODE
-> PLAN_READY
-> EXECUTE_MODE
-> OBSERVE
-> GAP?
   -> REPLAN
   -> PLAN_MODE
   o
   -> VERIFY
-> COMPLETION

Contrato nativo:

`ExecutionMode = PLAN | EXECUTE`

`PlanContract` debe contener como minimo:
- plan_id
- mission_id
- node_id
- goal_id
- base_sha
- write_scope
- objective
- acceptance[]
- evidence_refs[]
- findings[]
- actions[]
- dependencies[]
- expected_outputs[]
- rollback[]
- unknowns[]
- created_from_state_hash
- plan_sha256

Cada `actions[]`:
- action_id
- tool_name
- typed_inputs
- side_effect
- target_paths[]
- depends_on[]
- expected_result
- acceptance_ids[]

PLAN_MODE:
- puede READ/LIST/SEARCH/INSPECT/HASH/RESEARCH;
- puede producir/actualizar PlanContract;
- NO puede escribir, mover, copiar, descargar, instalar, ejecutar deployment ni
  cualquier otra mutacion;
- StructuredAction mutante en PLAN_MODE -> `PLAN_MODE_SIDE_EFFECT_DENIED`.

PLAN_GATE antes de ejecutar:
- schema PlanContract valido;
- base_sha sigue vigente;
- write_scope cubre todos los target_paths;
- todos los tool_name existen en NativeToolRegistry;
- cada mutacion apunta a action_id del plan;
- acceptance tiene cobertura por acciones/pruebas;
- unknown critico no resuelto -> PLAN_BLOCKED;
- plan_sha256 fijado.

Transicion:
`SET_MODE(EXECUTE)` solo puede ocurrir despues de PLAN_GATE PASS y autorizacion
del host/usuario segun TaskContract.

En EXECUTE_MODE:
- toda StructuredAction mutante debe referenciar `plan_id + action_id`;
- accion fuera del plan -> `UNPLANNED_MUTATION_DENIED`;
- drift de base_sha/write_scope/inputs -> `PLAN_STALE` y regreso a PLAN_MODE;
- un GAP puede generar `REPLAN_REQUIRED` sin perder evidence previa.

UI opcional:
`Shift+Tab` puede mapearse a `SET_MODE`, pero nunca es la autoridad.
La autoridad es el estado FSM + Sheriff/Policy.

Evidence adicional:
- plan_id
- plan_sha256
- action_id
- mode_at_execution
- base_sha_at_plan
- base_sha_at_execution

Tests obligatorios:
- PLAN_MODE_MUTATION_DENIED
- EXECUTE_WITHOUT_PLAN_DENIED
- UNPLANNED_MUTATION_DENIED
- STALE_PLAN_DENIED
- PLAN_ACTION_SCHEMA_INVALID
- PLAN_WRITE_SCOPE_ESCAPE
- PLAN_ACCEPTANCE_UNCOVERED
- VALID_PLAN_EXECUTES
- GAP_REPLAN_PRESERVES_EVIDENCE

Objetivo:
hacer que Seals inspeccione y acuerde exactamente QUE va a hacer antes de tocar
estado, sin convertir Plan Mode en otro agente ni en otro orquestador.

## CAPACIDAD NATIVA: ACQUISITION + INTEGRATION

Entrada:

URL + COMPONENT + TaskContract

Flujo:

RECEIVE
-> usar motor existente de descarga/extraccion
-> verify source URL
-> resolve exact commit
-> checkout exact commit
-> SOURCE_COMMIT == CHECKED_OUT_COMMIT
-> inspect
-> classify
-> map destination
-> prune
-> decapitate external brain/orchestrator
-> extract capability
-> integrate through approved adapter/plugin
-> test
-> read-back
-> evidence

Reglas:

directorio existente != instalacion valida

stale/empty/wrong repo
-> FAIL/GAP

no crear downloader/mover nuevo antes de auditar el autorizado

1 path = 1 writer

Los SOURCE_FILE/SOURCE_SYMBOL de los motores existentes deben añadirse a la trazabilidad antes de implementar esta capa.

## SKILL -> SCHEMA

Seals convierte una skill en contrato/schema.
No ejecuta skills como prompts decorativos.

Flujo:

SKILL
-> extract objective/inputs/preconditions/actions/acceptance/evidence/failures
-> typed schema
-> validate
-> executable contract

Debe haber varios templates segun capability.
Todos deben ser validables.

No inventar schema de memoria.
Reutilizar schemas/validators existentes despues de X-Ray.

## RESEARCH

Research es una capability.
No otro agente interno.

Contrato minimo:

ResearchResult
- query
- sources[]
- source_type
- claims[]
- cross_check[]
- new_evidence
- conclusion

Regla:

NO_NEW_EVIDENCE
-> cambiar estrategia

repeticion improductiva
-> STUCK/BLOCKED_WITH_TRACE

Motor concreto:
GAP hasta cerrar trazabilidad real.

## FRONTEND / VISUAL

Solo si work_surface = FRONTEND o MIXED.

CODE
-> BUILD
-> START APP
-> REAL BROWSER
-> SCREENSHOT
-> DOM/CONSOLE
-> ACTION
-> SCREENSHOT NUEVO
-> VERIFY
-> GAP/FIX/REBUILD/RETEST
-> CODE PASS + BROWSER PASS + VISUAL PASS

CUA/MetaCua:
observan/actuan detras de Sheriff+sandbox.

No deciden PASS.

## ORACLE / COMPLETION

LLM_OPINION != OBJECTIVE_ORACLE.

Cadena:

TEST
-> ACCEPTANCE
-> EVIDENCE
-> COMPLETION AUDIT
-> PASS

EvidenceRecord minimo:

path
sha256
receipt
test
exit_code
artifact
source_commit
timestamp
mission_id/node_id
acceptance_id

Existe=false
-> GAP/FAILED

Provider/auth/timeout/invalid_output
-> typed failure

Tool error
-> observation
-> nunca PASS

No cierre por numero de iteraciones.

## RECOVERY

Seals no posee el scheduler de recovery.

Wordflow posee:
claim/lease/durable queue/watchdog/reenqueue.

Seals debe ser reanudable e idempotente:

CRASH
-> host reasigna/reanuda
-> Seals load contract/checkpoint
-> verify base/evidence hashes
-> same command_id replay/join
-> continue without duplicate side effect

## CONSTRUCCION Y VALIDACION

El equipo de construccion externo puede usar OpenCode/OpenHands/Codex u otros agentes para crear, reparar o auditar codigo.

Ese equipo NO forma parte de Seals runtime.

Las 3 instancias iguales en paralelo son una PRUEBA desde Wordflow/host:

3 Seals iguales
-> 3 nodos/claims/workspaces separados
-> 1 componente dificil por instancia
-> verify real download/write/test/evidence

No convertir esta prueba en una flota interna de Seals.

## ORDEN DE IMPLEMENTACION

1. X-Ray baseline del Seals actual.
2. contracts/bootstrap.
3. loop minimo + structured actions.
4. policy/execution/safe edit.
5. idempotency/replay.
6. oracle/evidence/completion audit.
7. acquisition/integration usando motores existentes trazados.
8. research cuando exista motor real trazado.
9. visual adapter cuando MetaCua/CUA symbols esten trazados.
10. recovery/regression contra host contract.
11. prueba 3 instancias desde Wordflow.
12. completion audit final.

Cada mecanismo:

test rojo
-> adapt
-> test verde
-> read-back
-> evidence SHA256

## CONDICION FINAL

SEALS WORKER VERIFIED significa:

CORE:
TASK_CONTRACT
STRUCTURED_ACTION
SHERIFF/POLICY ADAPTER
IDEMPOTENCY
TOOL_RESULT/OBSERVATION
OBJECTIVE+ACCEPTANCE
OBJECTIVE_ORACLE
REAL_TESTS
EVIDENCE_SHA256
COMPLETION_AUDIT

HOST INTEGRATION:
DAG real
CLAIM/LEASE
WRITE_SCOPE
DURABLE_QUEUE/RECOVERY
WATCHDOG/REENQUEUE
CRASH_RESUME
BACKEND/FRONTEND routing
browser/screenshot loop cuando aplique

VALIDATION:
regression suite
3 isolated Seals instances
wrong-source-commit
provider/tool failures
no-pass-without-evidence

Ningun item HOST obliga a duplicar su motor dentro de Seals.
