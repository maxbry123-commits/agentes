VERBATIM DOCUMENTO 4/4 PARTE A - Analisis 50 mejoras vs Muse Code SDK/Glimmer/
Meta Agent Cookbook (Director+Sol, 2026-09-16)

HALLAZGO CRITICO CONFIRMADO EN MI CODE REAL (cita textual):
"evaluar_componente devuelve PASS simplemente despues de obtener una
respuesta de Cerebras, y verificar_existencia devuelve PASS aunque existe
sea False. Eso deberia desaparecer."

FALTA ABSORBER DE MUSE CODE SDK (Seals solo tiene mission_id UUID):
commandId estable -> idempotencia real
Exactly-once (no tiene) -> no ejecutar dos veces el mismo comando
Replay seguro (no tiene) -> recuperar resultado anterior
Payload identity (no tiene) -> misma ID + payload diferente = DENY
Pending commands (no tiene) -> estado persistente del comando
ACK separado de ejecucion (no tiene) -> SUBMITTED->ACKED->EXECUTING
Queue durable (Seals: muy basica)
Materialized (no tiene) -> distinguir aceptado vs realmente ejecutado
Rejected tipado (Seals: GAP generico)
Session state durable (no tiene)
Host-death recovery (no tiene)
Resume session (no tiene)
Protocol fingerprint (no tiene)
Conformance fixtures (no tiene)
Events/streaming (no tiene)
Cancel/interrupt (no tiene)

FORMULA IDEMPOTENCIA MUSE:
mission_id + node_id + step_id + canonical_input -> SHA256 -> IDEMPOTENCY_KEY
MISMA KEY + MISMO INPUT -> REPLAY RESULTADO
MISMA KEY + INPUT DISTINTO -> FAIL_CLOSED

PATRON ANTE MUERTE DE PROCESO:
HOST RUNNING -> HOST CRASH -> CLASSIFY DEATH -> PRESERVE DURABLE STATE ->
NEW HOST -> RESUME SAME SESSION

FALTA ABSORBER DE MUSE GLIMMER AGENT:
Loop real: PLAN -> TOOL CALL -> EXECUTE TOOL -> FEED RESULT BACK ->
SELF-CORRECT -> ... -> FINAL
Tiene: ToolRegistry, JSON Schema por tool, ToolCall tipado, ToolResult
tipado, ResponseParser, max_steps, errores como observaciones, temp 0.0
Seals actual: TASK -> IF/ELIF -> FUNCION -> RESULTADO -> PASS/GAP
(sin OBSERVE -> REPLAN -> NEXT TOOL)
Regla YAIWES mas estricta que Glimmer: LLM dice FINAL no significa PASS
-> pasa por TEST ORACLE -> PASS/FAIL

FALTA ABSORBER DE META AGENT COOKBOOK:
Loop: RECEIVE -> READ -> THINK -> ACT -> OBSERVE -> EVALUATE ->
(DONE | READ...) con guards: max iteraciones, presupuesto, stuck
detection, interrupcion, test objetivo (pytest) como oraculo de finalizacion.

PATRON "VALIDATED IN-PLACE EDIT" (debe entrar directo a YAIWES):
READ FRESH -> OLD_STRING -> EXACT_MATCH==1? ->
  0 -> DENY
  >1 -> DENY / DISAMBIGUATE
  1 -> PATCH -> DIFF -> TEST
"cero coincidencias significa que el modelo invento el original y varias
coincidencias significan que la edicion es ambigua" (cita textual)

QUE TIENE SEALS HOY (microflujo real actual, confirmado):
TASK -> TYPE ROUTER -> DETERMINISTIC / CEREBRAS / CLAUDE -> RESULT ->
PASS/GAP -> evidencia_local.jsonl -> NEXT TASK -> WATCHDOG
