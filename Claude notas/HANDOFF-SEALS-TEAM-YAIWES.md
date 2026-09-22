# HANDOFF - SEALS TEAM YAIWES
Version 1. Scope exclusivo: construccion y cierre del micro-agente Seals Team YAIWES.

## MISION

Construir Seals Team YAIWES como UN SOLO worker especializado de ejecucion e integracion.

No es:
- Command Center
- Wordflow Kernel
- scheduler
- fleet manager
- segundo DAG
- segundo watchdog
- segundo provider router
- conjunto de subagentes internos

Firma objetivo:

SealsWorker.execute(TaskContract) -> NodeResult

## FUENTES AUTORITATIVAS

Leer fresh, en este orden:

1. Claude notas/PLAN-MAESTRO-4-OBJETIVOS.md - OBJETIVO 3
2. Claude notas/PLAN-ANEXO-B-SEALS-MECANISMOS.md
3. Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md
4. codigo real del componente fijado por SHA
5. runtime/tests reales de Seals

Si documento y codigo discrepan:
CODE + TEST + RUN FRESH > documento.

## ARQUITECTURA CONGELADA

TaskContract
-> WorkerBootstrap
-> FSM/loop
-> optional Research
-> StructuredAction
-> Sheriff/Policy
-> approved Tool/Adapter
-> ToolResult
-> Observation
-> GAP/FIX/RETEST
-> Objective Oracle
-> Evidence
-> Completion Audit
-> NodeResult

Regla central:
LLM propone.
Policy autoriza.
Tool ejecuta.
Receipt demuestra.
Oracle decide PASS.

## LIMITES DEL CORE

Objetivo: 500-1000 LOC para el micro-agente + adapters finos.

Permitido dentro de Seals:
- contracts tipados
- bootstrap/validation
- FSM del worker
- structured actions
- tool registry fino
- policy adapter
- command_id/payload fingerprint/replay
- safe edit
- ToolResult/Observation
- stuck detector
- oracle/evidence/completion audit
- adapters finos acquisition/research/visual

Prohibido dentro de Seals:
- subagentes
- OpenCode/OpenHands/Codex ejecutandose como workers internos
- Kimi/MiniMax agents enteros
- durable queue global
- DAG global
- scheduler
- watchdog/reenqueue global
- global lease manager
- multi-worker orchestrator
- provider/key pool

## HOST CONTRACT - WORDFLOW

Wordflow entrega como minimo:
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

Seals:
- valida el contrato
- ejecuta solo el nodo asignado
- respeta claim/lease/write_scope
- reporta heartbeat/checkpoint/gap/evidence
- devuelve NodeResult
- solicita/reporta release

Wordflow conserva autoridad global.

## REGLA DE COMPONENTES

NO copiar agentes completos.

Cada fuente se usa asi:
SOURCE -> MECHANISM -> ADAPT -> TEST -> EVIDENCE.

Antes de tocar codigo, consultar:
Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md

Si el item esta REFERENCE:
cerrar SOURCE_FILE/SOURCE_SYMBOL antes de integrar.

Si esta GAP:
no inventar el mecanismo.

Si esta EXCLUDED/HOST_ONLY:
no meterlo en el core.

## ORDEN DE CONSTRUCCION

NODO S-01 - baseline
- leer Seals actual
- contar LOC
- inventariar modulos/tests
- marcar codigo que duplica Wordflow
Salida: X-Ray baseline + tests actuales.

NODO S-02 - contracts/bootstrap
- TaskContract
- StructuredAction
- ToolResult
- EvidenceRecord
- NodeResult
- ExecutionMode = PLAN | EXECUTE
- PlanContract
- typed provider/failure states
- validate before execution

NODO S-03 - loop + PLAN_MODE nativo
- adaptar loop minimo smolagents + Muse Glimmer
- eliminar managed_agents/subdelegacion
- result -> observation -> correction
- max_steps + stuck detector
- FSM: BOOTSTRAP -> PLAN_MODE -> PLAN_READY -> EXECUTE_MODE -> OBSERVE/VERIFY
- PLAN_MODE solo READ/LIST/SEARCH/INSPECT/HASH/RESEARCH
- mutacion en PLAN_MODE -> PLAN_MODE_SIDE_EFFECT_DENIED
- PlanGate valida base_sha, write_scope, tools, acceptance y plan_sha256
- EXECUTE exige plan_id + action_id
- drift -> PLAN_STALE -> REPLAN

NODO S-04 - policy/execution
- Sheriff/policy antes de mutation
- write_scope
- sandbox/tool adapter
- safe edit
- read-back

NODO S-05 - idempotency
- command_id + payload_fingerprint
- replay/join
- conflict
- receipt

NODO S-06 - oracle/evidence
- TEST -> ACCEPTANCE -> EVIDENCE -> COMPLETION AUDIT
- ningun LLM decide PASS

NODO S-07 - acquisition/integration
URL + COMPONENT
-> motor existente de descarga/extraccion
-> verify URL/commit
-> inspect
-> classify
-> prune
-> decapitate
-> map destination
-> integrate
-> test
-> read-back
-> evidence

NODO S-07A - motores canonicos como tools de Seals
Objetivo:
copiar fielmente los motores canónicos dentro de Wordflow SIN modificar su codigo
y exponerlos a Seals mediante schemas.

Codigo destino:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/adapters/seals_motors/`

Schemas destino:
`➡️📂 wordflow loop code Yaiwes/wordflow_loop/contracts/seals_motors/`

Copiar EXACTO:
- motor_1_extract_only.py
- motor_2_queue_download_extract.py
- hf_download_extract_engine.py
- motor_3_copy_batches.py
- motor_4_move_batches.py
- motor_5_zip_root.py

Regla:
fetch source canonical -> verify blob SHA -> exact copy -> read-back -> same blob SHA.

NO:
- refactorizar motores
- adaptar motores
- reescribir motores
- meter motores en seals_core
- crear motor alternativo

Schemas requeridos:
- extract_only.schema.json
- download_extract.schema.json
- copy_batches.schema.json
- move_batches.schema.json
- zip_root.schema.json

Cada schema debe declarar:
tool_name
input_schema
required
write_scope
side_effect
timeout
result_schema
failure_types
evidence_required
source_blob_sha
adapter_path

Flujo:
StructuredAction
-> schema validate
-> Sheriff/Policy
-> motor exacto
-> ToolResult
-> receipt/evidence.

Motor 5:
empaqueta una raiz completa a ZIP excluyendo `.git/`;
produce manifest + tree_sha256 + zip_sha256 + read-back.
Blob canonico:
`2516d85d81f691f86c32a70b90c2599639eb83c6`
Estado:
`CODE_CREATED / RUNTIME_TEST_PENDING`.

PASS S-07A:
- 6 motores copiados con blob SHA identico;
- 5 schemas validos;
- registrados en NativeToolRegistry como tools nativas de Seals;
- 1 test real por tool;
- invalid schema no ejecuta;
- tool failure nunca PASS;
- evidence source/destination SHA + exit_code + read-back.

NODO S-08 - research
- primero resolver motor real trazado
- ResearchResult estructurado
- NO_NEW_EVIDENCE cambia estrategia
- no integrar Kimi-Researcher mientras T-013 siga GAP

NODO S-09 - frontend/visual
- solo si work_surface=FRONTEND/MIXED
- CUA/MetaCua detras de Sheriff+sandbox
- ACTION -> SCREENSHOT NUEVO -> VERIFY
- CODE PASS + BROWSER PASS + VISUAL PASS

NODO S-10 - recovery/regression
- crash/resume via host checkpoint/lease contract
- idempotency evita doble side effect
- suite completa de regresion

NODO S-11 - real validation
- lanzar 3 instancias iguales DESDE EL HOST, no dentro de Seals
- 1 componente dificil por instancia
- comprobar descarga/materializacion/evidence
- corregir comportamiento

NODO S-12 - completion
- audit de requirements
- trazabilidad completa
- LOC budget
- docs/runtime sync
- SEALS WORKER VERIFIED solo con evidencia

## TESTS MINIMOS OBLIGATORIOS

PLAN_MODE_MUTATION_DENIED
EXECUTE_WITHOUT_PLAN_DENIED
UNPLANNED_MUTATION_DENIED
STALE_PLAN_DENIED
PLAN_WRITE_SCOPE_ESCAPE
VALID_PLAN_EXECUTES
PATH_NOT_FOUND_NO_PASS
PROVIDER_ERROR_NO_PASS
INVALID_PREEXISTING_DIR_NO_PASS
WRONG_SOURCE_COMMIT
TASK_CONTRACT_INVALID
IDEMPOTENT_REPLAY
IDEMPOTENCY_CONFLICT
ACCEPTANCE_FAIL
PASS_WITHOUT_EVIDENCE
EVIDENCE_HASH
TOOL_ERROR_OBSERVATION
STUCK_DETECTION
NO_NEW_EVIDENCE
WRONG_BASE_SHA
SHERIFF_DENY
TOOL_TIMEOUT
CRASH_RESUME
BACKEND_TEST_FAIL
FRONTEND_BUILD_FAIL
BROWSER_FAIL
VISUAL_FAIL
SCREENSHOT_MISSING
ROLLBACK_AFTER_FAILURE

## DISCIPLINA DE TRABAJO PARA AGENTES CONSTRUCTORES

1 node = 1 active task.
1 path = 1 writer.
Leer HEAD fresh antes de escribir.
No declarar mecanismo por README si se exige codigo.
No cambiar arquitectura congelada.
No crear otro agente interno.
No cerrar por iteraciones.
No PASS sin test + evidence + read-back.
Cada commit debe ser pequeno y revertible.
Si aparece contradiccion: GAP, no interpretacion creativa.

## ESTADO INICIAL

Arquitectura: APROBADA.
Traceabilidad: creada; algunos items siguen REFERENCE/GAP a proposito.
Implementacion del nuevo micro-Seals: PENDIENTE.
Primer nodo valido: S-01 baseline/X-Ray del Seals actual.
