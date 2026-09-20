# PLAN MAESTRO - 4 OBJETIVOS YAIWES
Version 2. Creado 2026-09-19 por Claude Opus 5.
v2 = verificacion cruzada 5 pasadas contra `instrucciones 1 a 1 director.md` (4540 lineas)
+ las 24 notas de `Claude notas/`. La v1 tenia 31 omisiones; todas incorporadas aqui.

NOTACION: `<E>` = prefijo emoji flecha+carpeta del Director.
URL-encoded: `%E2%9E%A1%EF%B8%8F%F0%9F%93%82`
No se escriben emojis literales (la API de escritura devuelve HTTP 500).

FORMATO DE REPORTE AL DIRECTOR (regla suya, linea 188):
NO usar cuadros/tablas - dificil de leer en smartphone.
Usar cascada + microflujo transversal horizontal + formato Glimmer resumido.

---

## JERARQUIA REAL (no confundir nunca)

Yaiwes (proyecto completo)
  -> NCT / Neuronas Code Turbo (repo nct-core)
      -> Wordflow Loop Code Yaiwes (motor de PROGRAMAR CODIGO, 95% de Fables)
          -> Seals Team (worker especializado dentro de ese motor)

Wordflow Loop Code Yaiwes NO ES Yaiwes. Es un motor de workflow para programar.

---

## ESTADO REAL VERIFICADO POR API 2026-09-19 (no de documentos)

Los documentos previos mentian. Esto es lo fisico:

12 submodules MiniMax/Kimi -> MONTADOS REALES (gitlinks a repos externos)
  en `<E> wordflow loop code Yaiwes/wordflow_loop/agent_sources/`
  incluidos kimi_code y kimi_cli que las notas daban por GAP
mcode (@minimax-ai/code) -> UNICO QUE FALTA de los 13
orca/ -> DESCARGADO COMPLETO (src/, skills/, skill-guides/, skill-stubs/,
  native/, mobile/, cloud/, orca.yaml, package.json, pnpm-lock 529KB)
  Las notas decian "adquisicion ausente" - ERA FALSO
muse_glimmer/ -> real (code/, _archives/, DOWNLOAD_EXTRACT_MANIFEST.json)
opencode/ -> real y completo (packages/, sdks/, specs/, infra/)
meta_muse_code_sdk, metacua, cua_mcp, meta_agent_cookbook -> presentes, verificar en S1
18 slots de agentes (aider, cline, codex, goose, hermes, openhands, qwen_code,
  smolagents, agent_zero, claude_code, mimo_code, mirothinker, openclaw,
  opendev, research_agent_lab) -> presentes, verificar en S1

CONCLUSION: el objetivo 1 es mucho mas pequeno de lo que decian las notas.
El trabajo real es VERIFICAR, PODAR, CABLEAR - no descargar.

---

## BLOQUEOS QUE DEPENDEN DEL DIRECTOR (no los puede resolver Claude)

FLAG-1 SEGURIDAD: las 5 API keys NVIDIA estan en texto plano en
  `Claude notas/instrucciones 1 a 1 director.md`, repo PUBLICO.
  Comprometidas. Regenerar en NVIDIA.
FLAG-2: GROQ_API_KEY_1 da HTTP 401 real (invalida o revocada). Keys 2-7 OK.
FLAG-3: MAXBRY_123_TOKENS no sirve para auth git (push de limpieza de historial falla).
FLAG-4: limpieza de historial NO CERRADA. yaiwes-nucleo-limpio sigue size:0.
  filter-repo funciona pero solo baja de 15.70 a 15.09 GiB - el peso esta DENTRO
  de las carpetas protegidas. Falta decidir si se podan blobs grandes
  (--strip-blobs-bigger-than) dentro de esas carpetas.
FLAG-5: Open Montage sin repo verificable (solo un video de YouTube).
  Confirmar nombre/link exacto o se descarta.
FLAG-6: renombrar la carpeta ajena `Wordflow loop code Yaiwes` (big-AGI) a
  `big-AGI-descargado/` - requiere OK explicito (es un proyecto de cientos de MB).
FLAG-7: quien ejecuto el commit c9c81072 (copia META4) y si respeta la regla
  "Sol GPT retirado de todo trabajo mecanico".

---

## REGLAS DURAS (no negociables)

1. PROHIBIDO ESCRIBIR CODIGO DESDE CERO. Todo sale del codigo ya descargado:
   podar -> editar quirurgicamente -> refactorizar -> cablear.
   REUSE > PATCH > ADAPT > GENERATE. COPY-FIRST.
2. Maximo 500 LOC por bloque. Si no cabe, mas salidas.
3. NUNCA BORRAR ARCHIVOS. Editar quirurgicamente o crear version nueva y comparar.
4. No PASS sin evidencia: CODE + TEST + EVIDENCE(sha256) + READ-BACK.
5. SPARSE-CHECKOUT OBLIGATORIO en todo Action (repo 16.4GB; checkout completo
   tarda 13min o muere - runs 35467245568 y 35468506302 murieron asi).
6. Cada paso se anota en `Claude notas/` + Crazy Wall bitacora stated JSON +
   handoff, ANTES de pasar al siguiente. Y cada HALLAZGO tambien.
7. Escritura via API. Sin emojis literales (HTTP 500). En Python usar
   escapes `➡️\U0001f4c2`.
8. Si algo se bloquea: FLAG + anotar + seguir. Nunca parar el ciclo.
9. Un paso/tarea por salida. Contrato de nodo: maximo 3 pasos.
10. Verificar 4 veces (no 1) que una regla nueva quede cableada en TODOS los
    lugares donde aplica, no solo documentada una vez.
11. Antes de escribir CUALQUIER schema o bloque: consultar biblioteca/GitHub
    primero. Nunca escribir de memoria del LLM.
12. Anotar las instrucciones del Director 1 a 1, input block VERBATIM.

### REGLA CENTRAL DE AUTORIDAD
LLM = PROPONE
POLICY/SHERIFF = AUTORIZA
TOOL = EJECUTA
RECEIPT = DEMUESTRA
ORACLE = DECIDE PASS

### INVARIANTES FORMALES (nunca violables)
NO PASS WITHOUT EVIDENCE
NO MUTATION WITHOUT AUTH
NO CLOSE WITHOUT ORACLE
NO REPLAY WITHOUT SAME INPUT HASH
NO TWO WRITERS SAME RESOURCE

### PLANTILLA EXACTA (Glimmer, 7 secciones) - obligatoria para agentes y componentes
Capacidad
Patron - microflujo transversal horizontal (texto, sin imagenes salvo peticion)
LOOP
Aporta
Usa
Reglas
Fallos
Test
El diseno debe ser EXACTO, nunca generico ni ambiguo.

### ARQUITECTURA DE ROLES (nucleo pequeno - NO usar los 18 agentes por tarea)
Orquestar DAG/FSM      -> Wordflow Kernel      (autoridad maxima)
Autorizar ejecucion    -> Runtime determinista (autoridad maxima)
Escritura de codigo    -> OpenCode             (WRITER, slot 1)
Reparacion/revision    -> OpenHands            (REPAIRER, separado del escritor)
Auditoria independiente-> Codex                (AUDITOR)
Arquitectura dificil   -> Claude Code / MiMo   (ASESOR, sin autoridad de ejecucion)
Ambiguedad             -> Council12            (SOLO asesor)
PASS final             -> Tests/oracle determinista (autoridad maxima)

### SEALS PODADO A
SealsExecutor.execute(NodeInput) -> ToolReceipt -> Evidence[] -> NodeResult
Pierde: su cola, su watchdog, su decision de PASS.
NUNCA un segundo orquestador (eso duplicaria DAG/STATE/QUEUE/RETRY/PASS/WATCHDOG
y REDUCE determinismo).

### SEMANTICA DE ESTADOS (Muse Code)
SUBMITTED -> ACKED -> QUEUED -> STARTED -> MATERIALIZED -> VALIDATING -> VERIFIED_CLOSED

### FSM DEL NODO
PENDING -> CLAIMED -> RESEARCHING -> READY -> EXECUTING -> OBSERVING ->
VALIDATING -> VERIFIED_CLOSED

---

## OBJETIVO 1 - COMPONENTES + SKILLS->SCHEMA + AGENTES FALTANTES

### SALIDA 1 - Inventario forense real de agent_sources/
Recorrer las ~35 entradas via `GET /git/trees/<sha>` (1 llamada por carpeta).
Clasificar: SUBMODULE REAL / CODIGO REAL / CARPETA VACIA / STUB.
Incluir tambien: `kimi_k/` (vieja, duplicada con kimi_researcher) y
`minimax_mcp/` suelta fuera de agent_sources - marcar para fusion futura, NO borrar.
Escribir `Claude notas/INVENTARIO-FORENSE-agent_sources.md`.
PASS: 35 entradas, ninguna marcada "supuesto", sha de cada arbol.
PARCHE: archivo parcial ya sirve; retomar desde la ultima fila.

### SALIDA 2 - mcode + keys NVIDIA + submodule checkout en CI
2.1 Montar `mcode` como gitlink (Git Data API: POST /git/trees mode=160000
    type=commit sha pineado -> POST /git/commits -> PATCH /git/refs/heads/main).
    Metodo ya probado en commit f13f8f9.
2.2 Subir 5 keys NVIDIA como secrets NVIDIA_API_KEY_1..5, sellado libsodium
    via ctypes sobre libsodium.so.23 (metodo probado con las 7 GROQ, memoria.md 11).
2.3 GAP CRITICO YA IDENTIFICADO: montar el gitlink NO trae el codigo fuente.
    Para que Seals pueda EJECUTAR el codigo de esos 12 submodules hace falta
    `git submodule update --init` real en tiempo de build/CI.
    Cablear ese paso en el workflow (con sparse-checkout).
PASS: GET agent_sources/mcode -> html_url externo;
      GET /actions/secrets -> 5 NVIDIA;
      un run de CI que materializa al menos 1 submodule y lista sus archivos.
PARCHE: si el mount falla, FLAG y seguir - mcode no bloquea nada mas.

### SALIDA 3 - Skills -> DSL DAG Schema (decision Fables, no negociable)
Regla del Director: los skills NO sirven de adorno. Se convierten en
contratos -> DSL DAG schema -> runtime Python.
Fuentes:
  - los 3 skills frontend (impeccable, frontend-design, skill-creator)
  - skills nativos en `agent_sources/orca/skills/` y `orca/skill-guides/`
  - skills Anthropic adicionales: docx, pdf, pptx, xlsx, artifact-design,
    artifact-capabilities
REUTILIZAR como plantilla (NO inventar formato):
  `Core kernel Yaiwes/control-layer/schemas/output_contract.yaml`
  `Seals team YAIWES/dag_schema.yaml`
Producir `skills_schema/<nombre>.dag.yaml` con:
  objective, acceptance[], tools[], evidence[], work_surface
PASS: cada schema valida contra el validador DAG existente; 1 test por schema.
PARCHE: schemas independientes - si uno falla, los demas siguen.

### SALIDA 3B - Notas de tareas pendientes en readme + Crazy Wall
Instruccion literal: "Coloca una nota dentro de la readme arquitectura y cada
Craxy wall segun el repo como tarea pendiente".
LISTA JEV + RSI -> destino repo `router-universal-router-inteligente-`:
  TypeSafe Agent Skills, Jev Router, Jev Agent Skill Router, Jev Review MCP,
  Jev Harness, Fast Jev Compaction, System One Lite, Open Jev, Awesome Jev,
  OpenRSI/OpenMLE, RSIAgent, Skill-RSI, ShinkaEvolve, OpenEvolve, SimpleTES,
  ThetaEvolve, CodeEvolve, Dream-RSI
  NUCLEO MINIMO: OpenRSI + RSIAgent + Skill-RSI + ShinkaEvolve + SimpleTES
  DECISION: NO instalar como skills decorativos. Extraer mecanismo ->
  DSL/DAG contract Python, patron de seals_core/.
LISTA FRONTEND -> destino wordflow + copia repo frontend + fabrica UI:
  Taste Skill, 21st MCP, Web Design Guidelines (vercel-labs), Image to Code,
  Awesome Design (VoltAgent), UI/UX Pro Max, Vercel React Best Practices,
  Design-to-Code, Frontend Design Codex, Emil Kowalski skills, Impeccable,
  HyperFrames (framework + 9 skills), Web Design Studio / cinematic-scroll
  Software adicional: Caret, Onlook, Plasmic, Webstudio, Playwright MCP
COMPONENTES COMAND CENTER (investigados, mecanismo extraible):
  Orca (worktree aislado + rotacion de keys) - el mas fuerte, YA DESCARGADO
  Munder Difflin (oficina de agentes con roles fijos)
  DeepSeek Harness (provider-plugin declarativo)
  Herdr (sesiones/paneles concurrentes, secundario)
  MatPocock Skills (biblioteca, no motor - fuera de scope de motores)
  Open Montage -> FLAG-5, sin repo verificable
DESTINOS YA CORREGIDOS (no repetir el error anterior):
  Omniroute -> `wordflow_loop/runtime/src/conn/`
  Orca -> NO se instala como carpeta de componente; se extrae su logica
  Omarchy -> NO APLICA como componente de repo (es infraestructura)
  Anydoc -> `Motores de descarga y extraccion/anydoc/`
  Skill Design Anthropic -> `Skills agente/skill-design-anthropic/`
PASS: nota escrita en el readme arquitectura de cada repo afectado + Crazy Wall.

---

## OBJETIVO 2 - CERRAR WORDFLOW LOOP CODE YAIWES

### SALIDA 4 - Doble raiz + reorganizacion de raiz
4.1 Carpeta 1 = `<E> wordflow loop code Yaiwes` (kernel Python real).
    Carpeta 2 = `Wordflow loop code Yaiwes` (SIN emoji, W mayuscula) =
    proyecto ajeno big-AGI (Electron+Next.js) con los 3 skills dentro de `skills/`.
4.2 Auditoria forense X-Ray: verificacion cruzada carpeta por carpeta entre
    ambas raices. Lista de lo que hay en cada una para decidir.
4.3 Mover SOLO los 3 skills a `Skills agente/` con el motor de copia existente
    (motor_3_copy_batches.py), sin borrar el origen.
4.4 Renombrar Carpeta 2 -> `big-AGI-descargado/` SOLO con OK del Director (FLAG-6).
4.5 Reorganizacion de raiz APROBADA hace turnos y NUNCA EJECUTADA:
    fusionar `Skills`/`skills`, `Conecciones router inteligente universal`/
    `conectividad con Router inteligente universal`, y los 3 duplicados de
    "wordflow loop code Yaiwes" en main -> UNA SOLA RAIZ UNIFICADA.
PASS: 3 skills en `Skills agente/` con contenido real; tabla de doble raiz;
      raices duplicadas resueltas o FLAG explicito.
PARCHE: nada se borra; el origen queda intacto.

### SALIDA 5 - Gaps del kernel Wordflow (orden del propio analisis)
5.1 CheckpointManager guarda en memoria (`self._checkpoints={}`) ->
    persistencia durable en disco/SQLite. PRIORIDAD NUMERO UNO.
5.2 Deprecar `runtime/src/agent/agent_router.py` (debil: si no hay match real
    puede seleccionar el primero del registro en vez de fallar cerrado) ->
    AUTORIDAD UNICA `AgentFleetAdapter` + `agent_fleet_registry.json`
    (fail-closed real, contrato tel.workflow/v4). Decision tomada, nunca ejecutada.
5.3 Recovery Engine generico (ESCALATE_TO_DIRECTOR) -> estados tipados:
    RETRYABLE / DEPENDENCY / AUTH / STUCK / CRASH / IRREVERSIBLE_FAILURE /
    NO_NODE_SOLUTION.
5.4 Stuck detector: mismo tool + mismos args + mismo error x3 -> BLOCKED_STUCK.
5.5 1 path = 1 writer + lease (resource locks).
5.6 Idempotencia persistente (hoy el cache del Kernel tambien es memoria de proceso).
5.7 `contracts/` y `evidence/` (wordflow_loop/wordflow_loop/) estan VACIAS - llenar.
5.8 Los 7 archivos de gobernanza (sheriff, sentinel, judge, guardian, supervisor,
    validator, verifier) miden 389-804 bytes. LEER su contenido real:
    si son stubs, cablearlos; si no, documentar por que son tan pequenos.
5.9 2 sistemas de Crazy Wall paralelos (raiz principal vs "Crazy Wall Orquestador/")
    - el prompt de comparacion ya esta escrito, nunca se ejecuto. Ejecutarlo.
5.10 Duplicado `source_truth_reconciler.py` vs `truth_reconciler.py` - resolver.
5.11 13 subcarpetas de templates/skills/plugins/prompts VACIAS = biblioteca RAG
     sin construir. Construirla (es requisito previo a generar cualquier schema).
5.12 AGENT_FLEET_READY_FOR_TEST.json: 18 agentes registrados, CERO pruebas de
     runtime real. Ejecutar al menos 1 prueba real por rol del nucleo pequeno
     (OpenCode, OpenHands, Codex).
PASS por item: test que falla ANTES del fix y pasa DESPUES.
PARCHE: cada item = commit independiente, revertible por separado.

### SALIDA 6 - Frontend visualizable
Peticion literal: "revisa en wordflow la parte de frontend para que visualice
el frontend".
REUTILIZAR el capability/adapter de navegador que Wordflow YA TIENE.
NO crear otro navegador-kernel dentro de Seals.
Cablear el gate: CODE PASS + BROWSER PASS + VISUAL PASS
  (spec en `arquitectura wordflow loop code Yaiwes/SCHEMA-frontend-browser-verified.md`)
Tool loop Meta/Glimmer DENTRO de cada worker (NO en el kernel).
Screenshot recurrente en CADA paso visual relevante, no solo al cierre.
LOOP FRONTEND completo:
GOAL UI -> READ CRAZY WALL FRESH -> CLAIM -> READ COMPONENT TREE ->
READ STATE/STYLES/ROUTES -> READ API CONTRACTS -> PLAN -> EDIT -> BUILD ->
START APP -> OPEN REAL BROWSER -> SCREENSHOT/DOM/CONSOLE -> INTERACT ->
COMPARE ACCEPTANCE -> GAP? -> FIX -> REBUILD -> RETEST -> MOBILE/TOUCH TEST ->
INTEGRATION TEST -> EVIDENCE -> PASS -> RELEASE/NEXT
PASS: un componente frontend real recorriendo el loop completo con evidencia.
PARCHE: si no hay navegador en CI, FLAG y dejar el gate cableado marcado
NO_VERIFICADO.

### SALIDA 6B - Los 4 archivos nunca abiertos (Frente 1)
Pendiente explicito desde 2026-09-16, nunca resuelto:
  execution_pipeline_dsl.py
  execution_pipeline_dsl_-_Copiar.md
  PIPELINE_MASTER.md
  INPUT_BLOCK.md
Y el "motor de investigacion y deterministico de codigo de opus" que el Director
menciono y que NO fue identificado ni integrado.
ACCION: localizarlos en el repo, leerlos, y decidir si el System Prompt DSL/DAG
del Frente 1 ya esta cubierto o falta cablearlo.
PASS: los 4 leidos + veredicto escrito sobre el motor de opus.

---

## OBJETIVO 3 - TERMINAR SEALS TEAM YAIWES

Ya cerrados (Salidas 1-7, memoria.md seccion 6):
P0-01..P0-15, P0-17, P1-18..P1-23, P1-25, P1-26, P1-29.

### SALIDA 7 - Gaps restantes
P1-27 crash/resume: integrar con CrazyWallAdapter.checkpoint (depende de S5.1).
P1-28 sandbox/rollback del instalador: workspace aislado -> acquisition ->
  inspect -> dependency policy -> install -> local test -> promote;
  FAIL -> descartar workspace/snapshot.
P0-16 completar ToolRegistry Glimmer (quedo parcial) - extraer de
  `agent_sources/muse_glimmer/code/agentic-fundamentals/`
  (agent_loop.py, response_parser.py, run_agent.py).
P1-24 MetaCua/CUA-MCP: LEER la implementacion real en `agent_sources/metacua/`
  y `agent_sources/cua_mcp/` ANTES de declarar nada.
  Detras de Sheriff + sandbox + typed tool contract + evidence.
  NUNCA autoridad de PASS.
P2-31 handoff drift: regenerar la seccion de estado desde el inventario runtime
  (dice 229 componentes; real 248; requirements.txt SI existe).
P1-30 tests faltantes: crash/recovery y wrong-source-commit.
P2-32 requirements reproducibles: lock/pinning.

### SALIDA 8 - Grupo 1 + Grupo 2
GRUPO 1 - 7 requisitos NATIVOS del agente (verbatim del Director):
1. Saber donde va cada cosa en el kernel (pool/rol del Wordflow) y como
   determinarlo, sin confundirse con un subagente (evitar 2 cerebros).
   YAIWES usa/replica su propio kernel; solo activa plugin/wordflow como extension.
2. Radiografia nativa de la raiz de YAIWES: donde va cada archivo y POR QUE,
   usando el motor de mover archivos.
3. Como convertir un skill en un schema: criterios + varios modelos de ejemplo.
4. Como usar UNICAMENTE el plugin universal Enchufe Universal Fables para cablear.
5. Como podar, que podar, como decapitar y convertir el wordflow.
6. Partes criticas del kernel: SOLO Claude las toca; otros preparan, Claude revisa.
7. Como descargar componentes con los motores: reciben URL + nombre de componente
   y realizan un estudio de su ubicacion, igual que todos los componentes de la
   raiz de Core kernel Yaiwes.

GRUPO 2 - pool de agentes (equipo 2):
1. Hacen CODIGO PURO - no integran. Ejemplo: el razonamiento de Mythos del
   diseno que hizo Fables.
2. Bajo consenso reciben un lote de codigo ya creado (Fables/Opus) y deciden
   donde debe ir en la arquitectura de la raiz.
3. Revisan lo realizado, refactorizan, revisan code y wordflows, y hacen
   auditoria forense X-Ray con verificacion cruzada contra el codigo fuente
   CARPETA POR CARPETA, usando la plantilla Glimmer de 7 secciones EXACTA.
   Nunca generico, nunca ambiguo.

### SALIDA 8B - 12 GOALS + Ask Council + refutaciones (exigido antes de cerrar)
Instruccion literal (linea 290): "Audita el plan refuta 3 veces y creas 12 goals
de entrada y salida y ask consil tambien 12 pasos antes de continuar".
Producir:
  12 GOALS de entrada/salida explicitos
  Ask Council de 12 puntos
  3 refutaciones independientes del plan
  4 simulaciones SIM-01..04 como regression tests obligatorios
Ampliar la suite con: IDEMPOTENT_REPLAY, IDEMPOTENCY_CONFLICT,
TASK_CONTRACT_INVALID, CLAIM_COLLISION, LEASE_EXPIRED, WORKER_CRASH,
CRASH_RESUME, WRONG_BASE_SHA, WRONG_SOURCE_COMMIT, SHERIFF_DENY, TOOL_TIMEOUT,
TOOL_ERROR_OBSERVATION, STUCK_DETECTION, NO_NEW_EVIDENCE, ACCEPTANCE_FAIL,
PASS_WITHOUT_EVIDENCE, BACKEND_TEST_FAIL, FRONTEND_BUILD_FAIL, BROWSER_FAIL,
VISUAL_FAIL, SCREENSHOT_MISSING, DOUBLE_WRITER_COLLISION, ROLLBACK_AFTER_FAILURE.

### SALIDA 8C - Cierre verificado + prueba real con 3 agentes
CONDICION DE CIERRE (completa, del Director):
DAG_REAL + TASK_CONTRACT_REAL + CLAIM/LEASE + WRITE_SCOPE + STRUCTURED_ACTIONS +
SHERIFF + IDEMPOTENCY + DURABLE_QUEUE/RECOVERY + OBJECTIVE+ACCEPTANCE +
OBJECTIVE_ORACLE + REAL_TESTS + EVIDENCE_SHA256 + WATCHDOG/REENQUEUE +
CRASH_RESUME + BACKEND_ROUTING + FRONTEND_ROUTING + BROWSER/SCREENSHOT_LOOP +
REGRESSION_TESTS + COMPLETION_AUDIT + INDEPENDENT_REFUTATION
= SEALS WORKER VERIFIED

PRUEBA REAL EXIGIDA ANTES DE PASAR AL COMAND CENTER:
  3 agentes iguales, 1 componente dificil a cada uno.
  Probar, corregir, perfeccionar su comportamiento.
  Lo mismo con el pool del Grupo B usando codigo de Mythos.
  Varias rondas, verificando que descargan el codigo y escriben el resultado
  completo. Pulir ANTES de continuar.

REQUISITO 50 MUNDOS (se verifica aqui, antes de declarar cerrado):
  Cada wordflow = un mundo independiente, sin compartir archivos:
  Readme memoria.md propio + Handoff propio + Crazy Wall propio +
  System prompt propio (del mismo template).
  Mismo code_sha256, distinto worker_id/task/workspace.
  Cerebras = SOLO PRUEBAS. En produccion todos se conectan al Router
  Inteligente Universal como proveedor de API keys.
  IMPLICACION: router_modelos.py y consultor_experto.py necesitan un adapter
  que apunte al Router Universal en vez de directo a Cerebras.

PARCHE: si un item no cierra -> GAP explicito. Nunca cierre fingido.

---

## OBJETIVO 4 - ORQUESTADOR COMAND CENTER

Arquitectura YA APROBADA por el Director (verbatim):
"Opcion 1 como capa de control y Opcion 2 como motor de ejecucion durable -
Omniroute/Orca gobiernan keys, mirrors y visibilidad; Dagu/DBOS aporta la
durabilidad que hoy falta. Lo unico que escribiria de cero son los adapters
entre ambos y el kernel Python. Cero componentes nuevos por descargar."

El Comand Center orquesta WORDFLOW (el kernel central), NO Seals.
Seals dejo de ser el orquestador principal.

### SALIDA 9 - Adapters (capa de control)
De `agent_sources/orca/` (YA DESCARGADO, codigo real) extraer:
  worktree git aislado por agente (coincide con isolation.py ya construido)
  rotacion/hot-swap de cuentas y API keys con usage tracking
    (aplica directo a router_modelos.py para las 50+ keys)
  CLI programable como contrato de automatizacion externa
De Omniroute extraer: gobierno de keys/mirrors.
De Munder Difflin: patron "oficina de agentes" con roles fijos.
De DeepSeek Harness: patron provider-plugin declarativo.
DESTINO: funciones Python dentro de `isolation.py` y `router_modelos.py`
YA EXISTENTES en seals_core. NO app Electron. NO carpeta nueva.
El Director nunca ve ni opera Orca directamente - es backend invisible.
ARTIFY (= Archify skills, confirmado por el Director):
  parte del osquestador del wordflow, para ir actualizando el progreso de
  todos los trabajos de wordflow de forma facil y simplificada.
  Artify + Orca = backend del orquestador.
PASS: test real de rotacion de keys + aislamiento de 2 workers sin colision.

### SALIDA 10 - Motor durable + 50 mundos + MCP
10.1 Dagu/DBOS como motor de ejecucion durable.
     VERIFICAR PRIMERO cual esta ya en el repo: `Core kernel Yaiwes/` tiene
     Dagster, Temporal, Prefect, APScheduler, Celery; existe
     TASK-GAPS/N21-DAGU-PASO1-XRAY.md. Si no esta ninguno -> FLAG al Director.
     No se descarga sin su OK (su regla: cero componentes nuevos).
10.2 Router que llama al Router Inteligente Universal (50+ API keys EN PARALELO)
     y manda senal al Comand Center + todos los mirrors de wordflow y sus
     agentes internos.
10.3 Servidor MCP - contexto compartido entre agentes. 3 recursos:
     crazy_wall_state (lectura)
     mission_context (lectura/escritura controlada - lo que un agente descubre
       lo comparten los demas)
     enchufe_universal_tools
     REGLA DE SEGURIDAD: MCP comparte CONTEXTO, nunca AUTORIDAD.
     El Kernel decide PASS.
10.4 Sistema de preguntas previas SIEMPRE activo, 3 lugares:
     UI interface, UI backend, Input Shark.
     (diseno completo en DISENO-preguntas-siempre-activo-input-shark.md)
10.5 Omnirouter como backend Y frontend del Router Inteligente Universal -
     esto va DESPUES de terminar Wordflow + Comand Center.
PASS: ciclo end-to-end: goal -> DAG -> worker -> evidencia -> completion audit,
sobreviviendo a un crash del worker sin duplicar side effect.

---

## PIPELINE CANONICO (del Director)

GOAL BUILDER
  -> REQUIREMENTS + COUNCIL
  -> DAG VISUAL
  -> NODE / CLAIM / LEASE
  -> AGENT FLEET
  -> CODE + TOOL EXECUTION
  -> BACKEND TEST / FRONTEND BROWSER
  -> GAP / FIX LOOP
  -> EVIDENCE LEDGER + RECOVERY
  -> COMPLETION AUDIT / GOAL OUTPUT

Campos por nodo: GOAL, ACCEPTANCE, STATE, WORKER, CLAIM, LEASE, INPUT SHA,
BASE SHA, FILES TOUCHED, COMMANDS, TOOLS, OBSERVATIONS, TESTS, SCREENSHOTS,
GAPS, FIXES, RETRIES, EVIDENCE, OUTPUT, WHY PASS / WHY BLOCKED.

---

## WATCHDOG

Tarea programada cada 1 hora. Nombre: "Motor de descarga".
Sesion nueva por disparo.
Prompt: leer este archivo -> primera salida no cerrada -> ejecutarla ->
anotar en Claude notas + Crazy Wall + handoff -> siguiente.
AVISO: puede requerir que el Director active "aprobacion automatica" en los
ajustes de la tarea, o cada disparo se quedara esperando permiso.

---

## VERIFICACION END-TO-END

GET /actions/secrets -> 5 NVIDIA presentes
Test real NVIDIA (https://integrate.api.nvidia.com/v1, modelo
  minimaxai/minimax-m2.7) DESDE GITHUB ACTIONS con sparse-checkout
  (el sandbox de Claude tiene la red bloqueada hacia NVIDIA: CONNECT tunnel 403)
SIM-01..04 en verde + la suite ampliada
Un componente frontend real pasando CODE+BROWSER+VISUAL
Crash de worker -> lease expira -> mision recuperada sin duplicar side effect
Read-back por API de cada archivo escrito
Auditoria 4 pasadas de todos los archivos creados/actualizados por Claude

---

## ORDEN DE EJECUCION

S1 -> S2 -> S3 -> S3B -> S4 -> S5 -> S6 -> S6B -> S7 -> S8 -> S8B -> S8C -> S9 -> S10

Dependencias reales:
  S7 depende de S5.1 (checkpoint durable)
  S9 depende de S1 (saber exactamente que hay dentro de orca)
  S3 depende de S5.11 (biblioteca RAG antes de generar schemas)
  S8C depende de S8 y S8B
Si una se bloquea: FLAG y saltar a la siguiente.

---

## ESTADO DE LAS SALIDAS

S1  obj1  PENDIENTE
S2  obj1  PENDIENTE
S3  obj1  PENDIENTE
S3B obj1  PENDIENTE
S4  obj2  PENDIENTE
S5  obj2  PENDIENTE
S6  obj2  PENDIENTE
S6B obj2  PENDIENTE
S7  obj3  PENDIENTE
S8  obj3  PENDIENTE
S8B obj3  PENDIENTE
S8C obj3  PENDIENTE
S9  obj4  PENDIENTE
S10 obj4  PENDIENTE
