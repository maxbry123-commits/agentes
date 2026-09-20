# ANEXO B - SEALS TEAM YAIWES: MAPA DE MECANISMOS
Anexo del PLAN-MAESTRO-4-OBJETIVOS.md. Version 1, 2026-09-19.

INSTRUCCION DEL DIRECTOR (verbatim, linea 475):
"Que integres los agentes de minimax y Kimi k y usas PARTES DE SUS COMPONENTES
y los 4 agente de glimer para crear el agente seals team YAIWES y lo conviertes
en determinetista lo mas que puedas"

PRINCIPIO: no se copia ningun agente entero. Se EXTRAE EL MECANISMO de cada uno
y se cablea dentro de Seals. Copiar un agente completo crearia un segundo kernel,
que es exactamente lo que el analisis prohibe.

REGLA MADRE: PROHIBIDO ESCRIBIR CODIGO DESDE CERO.
Todo sale del codigo YA DESCARGADO en `agent_sources/`.
Podar -> editar quirurgicamente -> refactorizar -> cablear.

---

## INVENTARIO DE FUENTES (todas ya en el repo)

META (4 agentes + cookbook), en `agent_sources/`:
  meta_muse_code_sdk    - carpeta local con codigo real
  muse_glimmer          - code/ + _archives/ + manifest
  metacua               - carpeta local
  cua_mcp               - carpeta local
  meta_agent_cookbook   - carpeta local

KIMI K (5), submodules gitlink reales:
  kimi_agent_sdk    -> MoonshotAI/kimi-agent-sdk
  kimi_agent_rs     -> MoonshotAI/kimi-agent-rs
  kimi_cli          -> MoonshotAI/kimi-cli
  kimi_code         -> MoonshotAI/kimi-code
  kimi_researcher   -> MoonshotAI/Kimi-Researcher

MINIMAX (8), submodules gitlink reales salvo mcode:
  minimax_mini_agent        -> MiniMax-AI/Mini-Agent
  minimax_openroom          -> MiniMax-AI/OpenRoom
  minimax_mmx_cli           -> MiniMax-AI/cli
  minimax_code_plugins      -> MiniMax-AI/MiniMax-Code-Plugins
  minimax_mcp               -> MiniMax-AI/MiniMax-MCP
  minimax_mcp_js            -> MiniMax-AI/MiniMax-MCP-JS
  minimax_coding_plan_mcp   -> MiniMax-AI/MiniMax-Coding-Plan-MCP
  mcode                     -> FALTA MONTAR (unico gap de descarga)

AVISO CRITICO: el gitlink NO trae el codigo fuente al repo. Para EXTRAER
mecanismo de los 13 submodules hace falta `git submodule update --init`
en CI con sparse-checkout. Esto es la Salida 2.3 del plan.

---

## MAPA MECANISMO -> GAP QUE TAPA

Cada linea: FUENTE -> MECANISMO -> GAP DE SEALS QUE RESUELVE -> DESTINO EN EL CODIGO

### De MUSE CODE SDK (Meta)
command_id + payload_fingerprint + replay -> tapa P0-11 (mission_id no es
  idempotencia) -> seals_core/idempotency.py
cola durable + reclaim (SUBMITTED/ACKED/QUEUED/STARTED/MATERIALIZED/TERMINAL)
  -> tapa P0-12 (la cola es un list Python en memoria) -> seals_core/queue.py
crash recovery + checkpoint durable -> tapa P1-27 -> integra con
  CrazyWallAdapter.checkpoint
session/event state (EVENT -> FOLD -> CURRENT STATE) -> tapa el estado volatil
worktree git aislado por subagente -> refuerza P1-25 (isolation.py ya existe)
completion audit -> tapa P0-05 (no cerrar por texto del agente)
approvals por etapas -> refuerza el Sheriff (P0-15)

### De MUSE GLIMMER (Meta)
ToolRegistry + JSON tool schemas -> tapa P0-16 (quedo parcial)
  -> extraer de agent_sources/muse_glimmer/code/agentic-fundamentals/
     archivos reales: agent_loop.py, response_parser.py, run_agent.py
parser ATEM (RAW OUTPUT -> channel parsing -> reasoning/tool_calls/final)
  -> tapa "texto libre interpretado como comando"
loop PLAN -> TOOL -> OBSERVE -> SELF-CORRECT -> NEXT -> el micro-loop del worker
tool errors como ToolResult tipado -> tapa P0-17 (errores que acababan en PASS)
REGLA: el tool loop va DENTRO del worker, NUNCA en el kernel.

### De META AGENT COOKBOOK
objective oracle -> tapa P0-04 (Claude no puede ser el oracle final)
acceptance-driven close -> tapa P0-05
stuck detection -> tapa P1-19
safe edit exact-match-before-patch -> mejora la edicion quirurgica
browser-verified web design -> es la base del gate frontend (P1-23)
GitHub Repo Agent -> patron de worker remoto disparado por evento
Multi-Agent Product Studio -> patron de equipo con estado compartido (Crazy Wall)

### De METACUA (Meta) - EL TRABAJO VISUAL, EN DETALLE
CAPACIDAD REAL: NO depende del DOM. OBSERVA PIXELES mediante screenshots
y actua mediante COORDENADAS.

Sistema de coordenadas:
  SCREENSHOT -> coordenadas normalizadas 0-1000 -> convertir a coordenadas
  del display -> mover cursor -> ejecutar accion

LOOP REAL:
  SCREENSHOT -> SEND IMAGE + TOOLS -> MODEL OBSERVES -> COMPUTER ACTION ->
  CLICK/TYPE/KEY -> SCREENSHOT NUEVO -> OBSERVE AGAIN -> REPEAT -> COMPUTER.STOP

REGLA FUNDAMENTAL: ACTION -> SCREENSHOT NUEVO -> VERIFY
  Nunca asumir que un CLICK funciono.

DETECTA VISUALMENTE lo que el codigo no delata:
  layout incorrecto
  botones fuera de posicion
  navegacion incorrecta
  elementos que no aparecen
  resultado distinto al esperado

TEST DE ESTADO: STATE A -> ACTION -> STATE B SCREENSHOT -> VERIFY STATE B

FALLO: CLICK INCORRECTO -> pagina/estado incorrecto -> screenshot ->
  detectar error -> corregir siguiente accion

CONVIERTE: "el codigo parece correcto" EN "resultado realmente observado
en pantalla"

Casos de test que cubre:
  BUTTON -> CLICK -> VERIFY
  FORM -> TYPE -> SUBMIT -> VERIFY
  MENU -> OPEN -> SELECT -> VERIFY
  DRAG -> MOVE -> VERIFY POSITION

RESTRICCION: MetaCua va SIEMPRE detras de Sheriff + sandbox + typed tool
contract + evidence. NUNCA tiene autoridad de PASS. (P1-24)

### De CUA + MCP + SANDBOX (Meta)
computadora Linux aislada -> el agente NO controla el host
LOOP: AGENT -> TOOL/MCP -> SANDBOX -> BROWSER -> ACTION -> OBSERVATION -> AGENT
Aporta el laboratorio frontend desechable: CODE -> SANDBOX -> BROWSER ->
  RENDER -> OBSERVE
REGLA: el agente decide, MCP transporta la accion, el sandbox limita donde
  ocurre el side effect.
Si el entorno queda inconsistente: se descarta y se reconstruye sin
  contaminar el host.
-> tapa P1-28 (installer sin sandbox/rollback)

### De KIMI-RESEARCHER (Kimi K)
investigacion real multi-fuente con cross-check
-> TAPA P1-18, QUE ES UNO DE LOS PEORES GAPS:
   hoy research_comunidad le pregunta 20 veces al MISMO Cerebras y llama a eso
   investigar. Ademas acepta la palabra "RESUELTO" del modelo como resolucion.
-> destino: seals_core/research_real.py (ya existe, se le cablea el mecanismo)
   ResearchResult estructurado: query, sources[], source_type, claims[],
   cross_check[], new_evidence, conclusion
   Regla: NO_NEW_EVIDENCE -> NO_RESEARCH

### De KIMI-AGENT-SDK (Kimi K)
contratos de sesion de agente -> refuerza el task_contract (P1-20, P1-21)
  y el WorkerBootstrap

### De KIMI-AGENT-RS (Kimi K)
implementacion en Rust -> para las partes que deben ser 100% DETERMINISTAS
  El Director pidio "lo conviertes en determinetista lo mas que puedas".
  Rust da determinismo real donde Python no alcanza.
  Candidatos: el verificador de hashes, el motor de idempotencia, el lease.

### De KIMI-CODE y KIMI-CLI (Kimi K)
worker de escritura alternativo + CLI programable
  -> entran en el AgentFleetAdapter como slots con capability declarada,
     nunca como orquestadores

### De MINIMAX-CODING-PLAN-MCP (MiniMax)
planificacion estructurada de codigo via MCP
  -> es el PLANNER del macro-loop. Hoy Seals no tiene planner real.
  -> alimenta el paso PLAN del loop antes de cualquier StructuredAction

### De MINIMAX-MCP y MINIMAX-MCP-JS (MiniMax)
servidores MCP reales, herramientas expuestas por MCP
  -> son la BASE del servidor MCP de contexto compartido del plan (Salida 10.3)
     3 recursos: crazy_wall_state, mission_context, enchufe_universal_tools
  -> REGLA: MCP comparte CONTEXTO, nunca AUTORIDAD

### De MINIMAX-CODE-PLUGINS (MiniMax)
sistema de plugins de codigo
  -> encaja DIRECTO con el Enchufe Universal Fables (el unico plugin
     autorizado para cablear, Grupo 1 punto 4)

### De OPENROOM (MiniMax)
entorno/sala multi-agente
  -> encaja con Multi-Agent Product Studio: estado compartido para que
     frontend y backend avancen en paralelo sin una sola conversacion

### De MINI-AGENT (MiniMax)
loop base minimo -> referencia de arquitectura minima, no se copia entero

### De MMX CLI (MiniMax)
CLI programable -> contrato de automatizacion externa (igual que el CLI de Orca)

### De MCODE (MiniMax) - FALTA MONTAR
agente de codigo de MiniMax -> worker de escritura. Salida 2.1

---

## ARQUITECTURA RESULTANTE DE SEALS (podado)

Seals NO es un orquestador. Su firma unica es:

  SealsExecutor.execute(NodeInput) -> ToolReceipt -> Evidence[] -> NodeResult

Pierde (porque los aporta Wordflow): su cola propia, su watchdog propio,
su decision de PASS.

Composicion interna por capas:

  CAPA CONTRATO      <- kimi_agent_sdk + task_contract + WorkerBootstrap
  CAPA PLAN          <- minimax_coding_plan_mcp
  CAPA DECISION      <- muse_glimmer (ToolRegistry + parser ATEM + micro-loop)
  CAPA AUTORIZACION  <- Sheriff/policy (ya existe: sheriff_policy.py)
  CAPA EJECUCION     <- tools registradas + minimax_code_plugins (Enchufe Universal)
  CAPA ENTORNO       <- cua_mcp (sandbox aislado)
  CAPA VISUAL        <- metacua (ojos: pixeles + coordenadas)
  CAPA INVESTIGACION <- kimi_researcher
  CAPA DURABILIDAD   <- meta_muse_code_sdk (idempotencia, cola, checkpoint, replay)
  CAPA DETERMINISTA  <- kimi_agent_rs (partes criticas en Rust)
  CAPA ORACLE        <- meta_agent_cookbook (objective oracle, acceptance close)
  CAPA EVIDENCIA     <- EvidenceRecord tipado + sha256 + screenshots

---

## LOOP COMPLETO DE SEALS (con todos los mecanismos cableados)

GOAL (del nodo autorizado por Wordflow)
  -> READ CRAZY WALL FRESH
  -> CLAIM + LEASE
  -> LOAD TASK CONTRACT (kimi_agent_sdk) -> schema validate -> READY
  -> DISCOVER REPO -> READ RELEVANT CODE -> BUILD DEPENDENCY CONTEXT
  -> RESEARCH si hace falta (kimi_researcher, con cross_check real)
  -> PLAN (minimax_coding_plan_mcp)
  -> DECIDE NEXT ACTION (muse_glimmer: reason -> structured tool call)
  -> PARSE (parser ATEM) -> StructuredAction
  -> SHERIFF autoriza
  -> IDEMPOTENCY CHECK (command_id + payload_fingerprint)
  -> EXECUTE en sandbox (cua_mcp) con el plugin Enchufe Universal
  -> TOOL RECEIPT
  -> si work_surface = FRONTEND:
       BUILD -> START APP -> OPEN REAL BROWSER
       -> SCREENSHOT (metacua, coords 0-1000)
       -> DOM + CONSOLE
       -> INTERACT (click/type/drag)
       -> SCREENSHOT NUEVO  <- obligatorio, nunca asumir
       -> COMPARE CON ACCEPTANCE
  -> si work_surface = BACKEND:
       RUN TESTS -> CAPTURE OUTPUT
  -> OBSERVATION (los errores vuelven como ToolResult, nunca como PASS)
  -> GAP? -> ROOT CAUSE -> NEW ACTION -> SHERIFF -> FIX -> RETEST
       STUCK detector: mismo tool + mismos args + mismo error x3 -> BLOCKED_STUCK
  -> OBJECTIVE ORACLE decide (test determinista, jamas un LLM)
  -> COMPLETION AUDIT (acceptance uno a uno)
  -> RECORD EVIDENCE (path + sha256 + receipt + screenshots)
  -> CHECKPOINT DURABLE
  -> RELEASE LEASE
  -> NodeResult a Wordflow

---

## ORDEN DE EXTRACCION (que se cablea primero)

1. submodule update --init en CI  <- sin esto no hay codigo que extraer (S2.3)
2. muse_glimmer: ToolRegistry + parser  <- completa P0-16, desbloquea todo lo demas
3. kimi_researcher -> research_real.py  <- tapa el peor gap (P1-18)
4. meta_muse_code_sdk: idempotencia + cola + checkpoint  <- tapa P0-11, P0-12, P1-27
5. cua_mcp: sandbox  <- tapa P1-28
6. metacua: capa visual  <- habilita el gate frontend (P1-23, P1-24)
7. minimax_coding_plan_mcp: planner
8. minimax_code_plugins -> Enchufe Universal
9. kimi_agent_rs: partes deterministas criticas
10. minimax_mcp -> servidor MCP de contexto compartido

PASS por mecanismo: test que falla ANTES de cablearlo y pasa DESPUES.
PARCHE: cada mecanismo es un commit independiente y revertible.
NUNCA declarar un mecanismo integrado por el hecho de que la carpeta exista.
Copiar las fuentes NO las convierte en integracion.
