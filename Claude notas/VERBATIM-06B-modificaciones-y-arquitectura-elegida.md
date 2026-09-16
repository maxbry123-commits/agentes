VERBATIM DOCUMENTO 6 PARTE B - Lista de 15 modificaciones + arquitectura
final elegida (Director+Sol, 2026-09-16)

QUE MODIFICARIA PARA MAXIMA DETERMINACION (15 puntos):
1. Wordflow = unica autoridad. DAG, FSM, queue, retry, estado y PASS viven ahi.
2. Un unico router: AgentFleetAdapter; quitar el router reducido de 4 agentes.
3. No seleccionar agentes por "inteligencia". Seleccionar por capability/
   role explicito y allowlist.
4. OpenCode como escritor por defecto (ya slot 1, writer/executor).
5. OpenHands separado del escritor - reparacion y revision, no autoaprobacion.
6. Codex como auditor tecnico independiente para cambios importantes.
7. Claude/MiMo/Council sin autoridad de ejecucion - solo arquitectura,
   diagnostico, refutacion o plan.
8. Seals como worker opcional, NUNCA segundo orquestador.
9. PASS solo por oracle: "worker says PASS = NO valido. pytest/build/hash/
   postcondition says PASS = SI valido" (cita textual)
10. Checkpoint durable en disco/SQLite (hoy es diccionario en memoria).
11. Idempotencia persistente (hoy el cache interno del Kernel tambien es
    memoria de proceso).
12. Agregar semantica Muse Code: SUBMITTED->ACKED->QUEUED->STARTED->
    MATERIALIZED->VALIDATING->VERIFIED_CLOSED
13. Tool loop Meta/Glimmer DENTRO de los workers, NO en el kernel:
    PLAN->TOOL->OBSERVE->CORRECT
14. Stuck detector: same tool + same args + same error x3 -> BLOCKED_STUCK
15. 1 path = 1 writer + lease para evitar dos agentes editando el mismo archivo.

ARQUITECTURA FINAL ELEGIDA:
YAIWES
  WORDFLOW LOOP KERNEL
    - deterministic tools (rama directa)
    - AgentFleetAdapter -> capabilities -> OpenCode(WRITER) / OpenHands
      (REPAIRER) / Codex(AUDITOR)
  -> TEST ORACLE -> EVIDENCE -> VERIFIED_CLOSED

"Y Seals Team lo dejaria fuera de ese camino principal salvo que lo
conviertas en un executor especializado que ofrezca alguna capacidad que
estos workers no tengan." (cita textual, conclusion final)

"Eso te deja un sistema bastante mas deterministico: un solo cerebro de
control (Wordflow), varios workers intercambiables, y ningun worker puede
decidir por si mismo que su trabajo esta aprobado." (cita textual de cierre)
