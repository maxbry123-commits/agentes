VERBATIM DOCUMENTO 5 PARTE A - Wordflow vs Seals vs Meta patterns (analisis
del Director+Sol, 2026-09-16)

CONCLUSION PRINCIPAL: Wordflow Loops code Yaiwes YA es un runtime/orquestador
serio, mas cerca de la arquitectura buscada que Seals. Separa Kernel+DAGEngine+
StateMachine+EventBus, implementa idempotencia, scheduling con dependencias y
paralelismo limitado, mantiene frontera explicita LLM/deterministico.

MICROCOMPARACION DE FLUJOS:
Seals actual: TASK -> IF/ELIF ROUTER -> deterministic/LLM -> PASS/GAP -> JSONL -> NEXT
Wordflow YAIWES: INTAKE -> AUDIT -> DAG -> PLACEMENT -> REUSE/PATCH/ADAPT/
  GENERATE -> SCHEDULER -> EXECUTE -> EVIDENCE -> STATE/CHECKPOINT
Muse Glimmer: PLAN -> TOOL CALL -> RESULT -> SELF-CORRECT -> TOOL... -> FINAL
Meta Cookbook: READ -> THINK -> ACT -> OBSERVE -> EVALUATE -> TEST ORACLE -> LOOP/DONE
Muse Code SDK: COMMAND -> COMMAND_ID -> ACK -> QUEUE/START -> MATERIALIZE ->
  TERMINAL -> REPLAY/RESUME

WORDFLOW TIENE DAG REAL: DAGEngine valida dependencias, detecta ciclos, genera
orden topologico deterministico con desempate estable.

FSM REAL DE WORDFLOW:
PENDING -> RUNNING -> DONE
RUNNING -> FAILED -> RUNNING
RUNNING -> BLOCKED -> RUNNING
RUNNING -> CANCELLED

SCHEDULER YA TIENE LO QUE FALTABA A SEALS:
TASK -> IDEMPOTENCY_KEY -> DEDUP -> DEPENDENCY CHECK -> PRIORITY ->
BOUNDED PARALLELISM -> EXECUTE -> REPLAY IF COMPLETED
Rechaza idempotency_key reutilizada con firma diferente: IDEMPOTENCY_KEY_CONFLICT

CONCLUSION ARQUITECTONICA: SEALS = worker/router sencillo. WORDFLOW =
orchestration kernel. "No convertiria Seals en Wordflow. WORDFLOW = KERNEL/
ORCHESTRATOR, SEALS = WORKER/EXECUTION PROFILE/PLUGIN" (cita textual)

FRONTERA LLM/DETERMINISMO EN WORDFLOW:
LLM puede: analyze_file, classify_semantics, generate_candidate, draft_code,
council_opinion, research_summary, synthesize_requirements
Runtime EXCLUSIVO: authorize_execution, evaluate_gate, persist_checkpoint,
persist_evidence, rollback_deployment, route_task, select_target_path,
schedule_dag, state_transition, sandbox_policy, promote_deployment,
hash_verify, validate_contract, validate_schema
Regla: LLM PROPONE -> RUNTIME AUTORIZA -> TOOL EJECUTA -> TEST DEMUESTRA

ARQUITECTURA MODULAR: CORE, RECOVERY, GOVERNANCE, INTAKE, ACQUISITION,
EXECUTION. Kernel entrypoint, fail_closed true. Event Bus: InMemory/Redis/NATS.

GAP MAS IMPORTANTE ENCONTRADO: CheckpointManager guarda en self._checkpoints={}
(memoria del proceso, se pierde si muere). Falta CRASH->NEW PROCESS->LOAD
CHECKPOINT->VERIFY HASH->RESUME NODE. "Prioridad numero uno" (cita textual)

RECOVERY ENGINE actual: FAILURE->classify->checkpoint->RETRY<=3->
ESCALATE_TO_DIRECTOR. Mejora propuesta: clasificar en RETRYABLE/DEPENDENCY/
AUTH/STUCK/CRASH/IRREVERSIBLE_FAILURE/NO_NODE_SOLUTION.

DISENO MADURO: no convierte gaps en PASS automatico. G-022 permanece
BLOCKED_PHYSICAL_ISOLATION hasta aislamiento real. "Preferible BLOCKED
HONESTO a PASS SIMULADO" (cita textual)
