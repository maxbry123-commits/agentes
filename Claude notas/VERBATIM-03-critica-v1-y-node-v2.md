VERBATIM DOCUMENTO 3/4 - Critica v1 (12 puntos) + yaiwes.node/v2 (Director+Sol, 2026-09-16)

12 MEJORAS CRITICAS SENALADAS:
1. DATA_ONLY/DO_NOT_EXECUTE necesita fase explicita CAPTURE -> BIND_TASK
2. max_steps:3 = 3 MACROFASES, los retries NO incrementan ese contador
3. continue_on_failure:false y "tomar otro nodo" no son contradictorios:
   el nodo falla y queda BLOCKED; la COLA sigue con otro nodo independiente
4. investigar_max:20 es demasiado abierto -> max_research_cycles pequeno +
   NO_NEW_EVIDENCE -> BLOCKED (20 busquedas iguales no anaden evidencia)
5. RESEARCH no significa "preguntarle a Cerebras" - debe usar herramientas
   reales de GitHub/HF/web. Cerebras puede sintetizar o proponer, NUNCA ser
   la evidencia en si misma.
6. EXECUTE llm_allowed:false es correcto para las mutaciones, pero se
   permite que un LLM produzca un ExecutionPlan/Delta tipado; Python decide
   si es valido y ejecuta.
7. Anadir FSM explicita: PENDING->RESEARCHING->READY->EXECUTING->
   VALIDATING->CLOSED/BLOCKED
8. Anadir authorization, preconditions, postconditions, idempotency_key
9. Anadir evidence obligatoria: path + sha256 + tool receipt + test result
10. No permitir DONE directo desde VALIDATE; mejor VALIDATE.PASS -> VERIFIED_CLOSED
11. Anadir FINAL_VERIFY independiente del propio resultado del agente
12. La salida debe tener JSON Schema real, no solo mode:JSON_SCHEMA

VERSION CORREGIDA yaiwes.node/v2 (schema completo dado por el Director):

schema: yaiwes.node/v2
execution_model: DAG+FSM
execution_policy: FAIL_CLOSED

input:
  capture: [VERBATIM, RAW_INPUT, OPAQUE_PAYLOAD, IMMUTABLE, READ_ONLY]
  preserve: [characters, whitespace, line_breaks, order]
  deny: [rewrite, normalize, interpolate, reinterpret]
  bind: CAPTURE_AS_DATA -> BIND_AS_TASK

node: { id: NODE-[N], repo: [repo], origen: [url], destino: [ruta] }
locks: { objective: true, scope: true, default_deny: true }
macro_steps: 3
dag: RESEARCH -> EXECUTE -> VALIDATE -> VERIFIED_CLOSED
all_other_transitions: FORBIDDEN
fsm: PENDING -> RESEARCHING -> READY -> EXECUTING -> VALIDATING -> VERIFIED_CLOSED | BLOCKED
constraints: { skip_steps: false, reorder_steps: false, invent_steps: false,
  reinterpret_input: false, scope_expansion: false }

RESEARCH:
  llm_role: SYNTHESIZE_AND_PLAN
  evidence_sources: [GitHub, HuggingFace, Library, StackOverflow, DEV, Reddit/programming]
  flow: TASK -> SEARCH_REAL_SOURCES -> DEDUPE -> CROSS_CHECK -> ResearchEvidence -> ExecutionPlan -> PASS
  gate: { require: [evidence_found, provenance_complete, plan_defined] }

EXECUTE:
  requires: RESEARCH.PASS
  llm_mutation_authority: false
  flow: ExecutionPlan -> AUTHZ_CHECK -> PRECONDITIONS -> IDEMPOTENCY_CHECK ->
    EXECUTE_REAL_TOOL -> OBSERVE_RESULT -> HASH_CHANGED_ARTIFACTS -> PASS
  require: [real_state_change, tool_receipt, path_sha256]

VALIDATE:
  requires: EXECUTE.PASS
  flow: ExecutionEvidence -> REAL_TEST -> CHECK_POSTCONDITIONS ->
    CHECK_ACCEPTANCE -> CHECK_OBJECTIVE -> FINAL_VERIFY -> PASS|GAP
  gate: { require: [tests_pass, acceptance_pass, objective_pass,
    evidence_complete, independent_verify_pass] }

on_gap:
  flow: GAP -> FIX -> RETEST -> VALIDATE
  max_fix_retries: 2
  research_again: NEW_BLOCKING_EVIDENCE_ONLY
  no_new_evidence: BLOCKED
  same_failure_without_delta: BLOCKED
  blocked: { record_gap: true, preserve_trace: true, next_independent_node: true }

gates: { NO_AUTHORIZATION: BLOCKED, NO_RESEARCH_PASS: NO_EXECUTE,
  NO_EXECUTION: NO_PASS, NO_REAL_TEST: NO_CLOSE, NO_EVIDENCE: NO_CLOSE,
  OBJECTIVE_DRIFT: FAIL, SCOPE_DRIFT: FAIL }

idempotency:
  key: sha256(mission_id + node_id + step_id + canonical_input)
  same_key_same_input: REPLAY_PREVIOUS_RESULT
  same_key_different_input: FAIL_CLOSED

evidence: { required: [path, sha256, operation, tool_receipt, test_result] }

NodeOutput: { type: object, additionalProperties: false,
  required: [node_id, research, execute, validate, evidence, status],
  status: { enum: [VERIFIED_CLOSED, BLOCKED] } }

MICROFLUJO TRANSVERSAL v2:
VERBATIM -> BIND TASK -> OBJECTIVE+SCOPE LOCK -> REAL RESEARCH -> CROSS-CHECK
-> TYPED PLAN -> AUTHZ+IDEMPOTENCY -> EXECUTE TOOL -> OBSERVE -> PATH+SHA256
-> REAL TEST -> FINAL VERIFY -> VERIFIED_CLOSED
   (rama) GAP -> FIX -> RETEST<=2 -> BLOCKED

REGLA CENTRAL DE ESTA VERSION:
LLM propone/investiga -> JSON/YAML restringen -> PYTHON autoriza y ejecuta
-> TEST externo decide PASS
"Eso si empieza a ser un system contract respaldado por un runtime
determinista, en vez de un prompt que simplemente le pide al modelo
comportarse de forma determinista." (cita textual del analisis)
