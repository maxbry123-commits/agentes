VERBATIM DOCUMENTO 6 PARTE A - Recomendacion arquitectura final (Director+Sol, 2026-09-16)

"Para hacerlo lo mas deterministico posible, yo no usaria Seals Team como
agente principal. Usaria Wordflow LOOP YAIWES como kernel/orquestador, y
pondria a Seals -si decides conservarlo- unicamente como un worker
especializado detras del Wordflow." (cita textual, decision central)

WORDFLOW YA TIENE UNA FLOTA REAL: 18 slots de agentes registrados: OpenCode,
OpenHands, Claude Code, MiMo Code, Codex, SmolAgents, Hermes, OpenClaw,
Aider, Muse/Glimmer, Kimi, Qwen Code, Cline, Goose, Agent-Zero, OpenDev,
Research Agent Lab, MiroThinker. Define un Council12.

DISTINCION CRITICA: REGISTRADO/WIRED != RUNTIME REAL YA PROBADO. El manifest
dice READY_FOR_REAL_AGENT_TEST, tests_executed_by_this_closure: false.
Hermes, Muse/Glimmer y Goose son runtimes externos no vendorizados. "Esto
esta bien disenado porque no inventa un PASS" (cita textual)

ARQUITECTURA RECOMENDADA - nucleo pequeno, NO usar los 18 agentes para
cada tarea (aumentaria costo/latencia/divergencia):
Orquestar DAG/FSM -> Wordflow Kernel (autoridad Maxima)
Autorizar ejecucion -> Runtime deterministico (Maxima)
Programacion/escritura -> OpenCode (Worker)
Reparacion/revision -> OpenHands (Worker)
Auditoria/debug independiente -> Codex (Reviewer)
Arquitectura dificil -> Claude Code o MiMo (Asesor)
Council cuando haya ambiguedad -> Muse/Kimi/Qwen/etc (Solo asesor)
PASS final -> Tests/oracle deterministico (Maxima)

Coincide con roles ya registrados en el Fleet: OpenCode=writer/executor,
OpenHands=review/repair, Codex=auditor/debug/code_review, Claude/MiMo=
flow_review/wiring_review/auditor.

DONDE PONDRIA SEALS TEAM: solo para tareas muy concretas, como worker
detras de un NODE especializado que ejecuta operacion acotada y devuelve
ToolReceipt/Evidence, NUNCA como su propio orquestador con su propia cola/
watchdog/decision de PASS, porque eso crearia DOS orquestadores duplicando
DAG/STATE/QUEUE/RETRY/PASS-GAP/WATCHDOG. "Eso reduce determinismo en lugar
de aumentarlo" (cita textual). Podaria Seals hasta:
SealsExecutor.execute(NodeInput) -> ToolReceipt -> Evidence[] -> NodeResult
Wordflow mantiene TODA la autoridad.

PROBLEMA CONCRETO A CORREGIR YA: existen DOS sistemas de routing.
runtime/src/agent/agent_router.py (pequeno) solo conoce OpenCode/Claude
Code/OpenHands/Aider, selecciona por coincidencia de skills, y si no hay
match real puede terminar seleccionando el primero del registro en vez de
fallar cerrado (riesgo real).
AgentFleetAdapter (el bueno) ya existe: agent_id exacto -> si no, role
exacto -> slot deterministico -> si no existe, FAIL_CLOSED. Comprueba
contrato tel.workflow/v4, IDs duplicados, runtime configurado, transporte permitido.

DECISION: ELIMINAR/DEPRECAR runtime/src/agent/agent_router.py.
AUTORIDAD UNICA: AgentFleetAdapter + agent_fleet_registry.json.
