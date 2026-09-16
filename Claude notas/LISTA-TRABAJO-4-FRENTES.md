LISTA DE TRABAJO - 4 FRENTES (organizada por Claude, 2026-09-16)
Basada en documentos VERBATIM-01 a 06B. Solo organizacion, NO diseno nuevo
(modo recepcion activo, pendiente autorizacion del Director para ejecutar).

===================================================================
FRENTE 1 - SYSTEM PROMPT DSL/DAG (el que da el Director, 1 a 1, sin sintetizar)
===================================================================
Fuente: VERBATIM-01 a 03 (yaiwes.node-executor/xray-v2, component-ops/v1,
critica 12 puntos + node/v2)
Pendiente de Claude: falta revisar 4 archivos adjuntos nuevos aun sin abrir
(execution_pipeline_dsl.py, execution_pipeline_dsl_-_Copiar.md,
PIPELINE_MASTER.md, INPUT_BLOCK.md) - el Director menciona "un motor de
investigacion y deterministico de codigo de opus" que aun no fue integrado
al agente team, y confirma que "no esta, asi como otras cosas no existen".
ACCION PENDIENTE: Claude debe leer esos 4 archivos antes de dar por cerrado
este frente.

===================================================================
FRENTE 2 - MEJORAR AGENTE TEAM (Seals) PARA TAREAS ESPECIALIZADAS
===================================================================
Fuente: VERBATIM-04A/04B (50 mejoras) + VERBATIM-06A/06B (decision final)
DECISION YA TOMADA por el Director+Sol: Seals NO es el agente principal.
Se poda hasta: SealsExecutor.execute(NodeInput) -> ToolReceipt ->
Evidence[] -> NodeResult. Pierde: su propia cola, su propio watchdog, su
propia decision de PASS. Pasa a ser worker/plugin de Wordflow, no un
segundo orquestador.
CONFIRMADO POR EL DIRECTOR: "no hiciste nada de lo que te dije de los
agentes de Meta, esta super incompleto" - los mecanismos de Muse Code SDK
(idempotencia real, command states, crash recovery), Muse Glimmer (tool
registry, plan-act-observe-correct) y Meta Cookbook (read-act-observe-
evaluate-oracle, safe edit exact-match) NO estan implementados en el
Seals actual (ejecutor.py, instalador_deterministico.py, consultor_experto.py,
verificador.py, watchdog.py, router_modelos.py).

===================================================================
FRENTE 3 - WORDFLOW LOOP CODE YAIWES = PIEZA CENTRAL (la "colmena")
===================================================================
Fuente: VERBATIM-05A/05B + VERBATIM-06A/06B
DECISION YA TOMADA: Wordflow = KERNEL/ORCHESTRATOR unico. Seals Team y
otros agentes van DENTRO, como workers.
Ya tiene (confirmado real, no diseno): DAGEngine con deteccion de ciclos,
FSM (PENDING->RUNNING->DONE/FAILED/BLOCKED/CANCELLED), Scheduler con
idempotency_key+dedup+dependency+priority+bounded parallelism, EventBus
(InMemory/Redis/NATS), frontera LLM/deterministico ya codificada,
AgentFleetAdapter con 18 slots de agentes registrados (OpenCode, OpenHands,
Claude Code, MiMo, Codex, SmolAgents, Hermes, OpenClaw, Aider, Muse/Glimmer,
Kimi, Qwen Code, Cline, Goose, Agent-Zero, OpenDev, Research Agent Lab,
MiroThinker), Council12.
GAPS CONFIRMADOS A CORREGIR (prioridad indicada por el analisis):
1. CheckpointManager guarda en memoria (self._checkpoints={}), no sobrevive
   crash - PRIORIDAD NUMERO UNO
2. Existen 2 routers duplicados: runtime/src/agent/agent_router.py (debil,
   puede fallar sin cerrar) vs AgentFleetAdapter (bueno, fail-closed real).
   DECISION: eliminar/deprecar el primero, unica autoridad el segundo.
3. Recovery Engine generico (ESCALATE_TO_DIRECTOR) - mejorar a clasificacion
   especifica (RETRYABLE/DEPENDENCY/AUTH/STUCK/CRASH/IRREVERSIBLE/NO_SOLUTION)
4. Falta Tool loop Meta/Glimmer DENTRO de cada worker (no en el kernel)
5. Falta stuck detector (mismo tool+args+error x3 -> BLOCKED_STUCK)
6. Falta 1 path = 1 writer + lease

===================================================================
FRENTE 4 - CREAR OSQUESTADOR Y COMAND CENTER
===================================================================
Estado: pendiente de que el Director prepare y pase la informacion
("lo que te voy a preparar de el osquestador que vamos a crear Comand
Center"). Comand Center ya tiene un inicio (Handoff + placeholders) dentro
de Seals team YAIWES/, pero dado que Seals deja de ser el orquestador
principal, ESTE FRENTE REQUIERE DECISION DEL DIRECTOR: el Comand Center
debe reubicarse para orquestar Wordflow (el nuevo kernel central), no Seals.
PENDIENTE: el Director aclarara esto cuando prepare la informacion.

===================================================================
VALIDACION - nada omitido, confirmado por revision de los 6 documentos guardados
===================================================================
- Los 4 documentos originales (node-executor, component-ops, critica+v2,
  50 mejoras) - guardados y reflejados en Frente 1 y 2.
- El analisis Wordflow vs Seals vs Meta - guardado y reflejado en Frente 3.
- La recomendacion final (Wordflow=kernel, Seals=worker podado,
  AgentFleetAdapter unico router) - guardada y reflejada en Frentes 2 y 3.
- Los 4 archivos recien adjuntos (execution_pipeline_dsl.py, -Copiar.md,
  PIPELINE_MASTER.md, INPUT_BLOCK.md) - AUN NO LEIDOS por Claude, marcados
  como pendiente explicito en Frente 1.
- El "motor de investigacion y deterministico de codigo de opus" mencionado
  por el Director - AUN NO IDENTIFICADO/INTEGRADO, marcado pendiente en Frente 1.
