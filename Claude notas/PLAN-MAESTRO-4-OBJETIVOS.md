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

13 submodules MiniMax/Kimi -> MONTADOS REALES (gitlinks a repos externos)
  en `<E> wordflow loop code Yaiwes/wordflow_loop/agent_sources/`
  incluidos kimi_code, kimi_cli y mcode.
mcode (@minimax-ai/code) -> MONTADO como gitlink al commit
  73a2581c6c7525628342f33b53907d4f7bdc146e.
  NO volver a montarlo; solo verificar/materializar con submodule update --init.
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

### ROLES DE CONSTRUCCION/VALIDACION - NO SON SUBAGENTES DE SEALS
Orquestar DAG/FSM      -> Wordflow Kernel      (autoridad maxima)
Autorizar ejecucion    -> Runtime determinista (autoridad maxima)
Escritura de codigo    -> OpenCode             (herramienta/agente EXTERNO de construccion)
Reparacion/revision    -> OpenHands            (EXTERNO, separado del escritor)
Auditoria independiente-> Codex                (EXTERNO)
Arquitectura dificil   -> Claude Code / MiMo   (ASESOR EXTERNO)
Ambiguedad             -> Council12            (ASESOR EXTERNO)
PASS final             -> Tests/oracle determinista

REGLA: OpenCode/OpenHands/Codex/Kimi/MiniMax completos NO viven dentro de Seals.
Solo se estudian para extraer mecanismos trazados o se usan fuera del runtime para
construir/reparar/auditar.

### SEALS PODADO A - ARQUITECTURA CONGELADA
Firma objetivo:
SealsWorker.execute(TaskContract) -> NodeResult

Seals = UN SOLO micro-agente/worker especializado.
Objetivo: 500-1000 LOC de codigo propio/adaptado para core + adapters finos.

CORE permitido:
TaskContract -> Bootstrap -> FSM -> StructuredAction -> Sheriff/Policy adapter ->
Tool/Adapter -> ToolResult -> Observation -> GAP/FIX -> Objective Oracle ->
Evidence -> Completion Audit -> NodeResult.

HOST_CONTRACT (Wordflow lo posee; Seals solo consume/respeta):
DAG, global claim/lease, durable queue/recovery scheduling, watchdog/reenqueue,
global write-scope arbitration, provider/key routing.

PROHIBIDO dentro de Seals:
subagentes, scheduler, segundo DAG, segunda cola global, segundo watchdog,
fleet manager, provider pool, Command Center.

Trazabilidad obligatoria:
`Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md`
Handoff operativo:
`Claude notas/HANDOFF-SEALS-TEAM-YAIWES.md`

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
2.1 mcode YA ESTA MONTADO como gitlink real.
    Commit fijado: 73a2581c6c7525628342f33b53907d4f7bdc146e.
    Accion: verificar gitlink + materializar con `git submodule update --init`.
    PROHIBIDO remontar/reemplazar sin nueva evidencia.
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

FUENTES AUTORITATIVAS PARA ESTE OBJETIVO:
1. `Claude notas/PLAN-ANEXO-B-SEALS-MECANISMOS.md`
2. `Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md`
3. `Claude notas/HANDOFF-SEALS-TEAM-YAIWES.md`
4. codigo real fijado por SHA
5. tests/run fresh

No confiar en etiquetas historicas de "cerrado" sin revalidacion.
El primer paso es X-Ray del runtime Seals actual contra esta arquitectura aprobada.

### PRINCIPIO DE DISENO - NO NEGOCIABLE

Seals Team YAIWES es UN SOLO micro-agente/worker de ejecucion e integracion.
NO es orquestador general.
NO contiene subagentes.
NO duplica Wordflow.

Firma:
`SealsWorker.execute(TaskContract) -> NodeResult`

Microflujo:

TASK CONTRACT
-> BOOTSTRAP/VALIDATE
-> FSM
-> RESEARCH si aplica
-> STRUCTURED ACTION
-> SHERIFF/POLICY
-> APPROVED TOOL/ADAPTER
-> TOOL RESULT
-> OBSERVATION
-> GAP/FIX/RETEST
-> OBJECTIVE ORACLE
-> EVIDENCE
-> COMPLETION AUDIT
-> NODE RESULT

Regla de autoridad:
LLM PROPONE -> POLICY AUTORIZA -> TOOL EJECUTA -> RECEIPT DEMUESTRA ->
ORACLE DECIDE PASS.

### CLASIFICACION OBLIGATORIA

CORE:
vive dentro del micro-Seals.

HOST_CONTRACT:
Wordflow lo posee; Seals lo recibe, valida y respeta.

VALIDATION:
prueba Seals; no forma parte del runtime interno.

GAP:
requisito real cuya fuente/implementacion aun no esta demostrada.

### HOST_CONTRACT - WORDFLOW

Wordflow conserva:
DAG
global claim/lease
durable queue/recovery scheduling
watchdog/reenqueue
global write-scope arbitration
provider/key routing
autoridad global de estado.

TaskContract entregado a Seals debe declarar como minimo:
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
command_id.

Seals puede:
validate
heartbeat/checkpoint
execute
record_gap
record_evidence
release/report
return NodeResult.

Seals NO crea motores globales equivalentes.

### SALIDA 7 - BASELINE + GAPS REALES

7.1 X-Ray del Seals actual:
- contar LOC y modulos reales
- leer ejecutor/verificador/watchdog/tests
- identificar cualquier cola/scheduler/watchdog/PASS oracle duplicado
- marcar que se conserva, poda, decapita o migra al host
- NO borrar antes de test comparativo.

7.2 Revalidar gaps historicos contra codigo:
P0-16 ToolRegistry/Glimmer
P1-27 crash/resume
P1-28 sandbox/rollback
P1-24 MetaCua/CUA-MCP
P1-30 crash/recovery + wrong-source-commit tests
P2-31 handoff drift
P2-32 lock/pinning.

7.3 Materializar submodules antes de extraer mecanismo:
`git submodule update --init`
No declarar mecanismo integrado porque exista gitlink/directorio.

PASS S7:
X-Ray escrito + mapa KEEP/PRUNE/DECAPITATE/HOST/GAP + tests baseline.
Sin eso no se modifica el core.

### SALIDA 8 - CONSTRUIR EL MICRO-SEALS

Seguir el handoff nodo por nodo.

S-01 baseline/X-Ray.
S-02 contracts/bootstrap.
S-03 loop minimo + structured actions.
S-04 policy/execution/safe edit.
S-05 idempotency/replay.
S-06 oracle/evidence/completion audit.
S-07 acquisition/integration.
S-08 research solo cuando exista motor real trazado.
S-09 frontend/visual solo cuando MetaCua/CUA tengan SOURCE_SYMBOL trazado.
S-10 recovery/regression contra host contract.
S-11 validacion con 3 instancias DESDE Wordflow.
S-12 completion audit.

Objetivo de tamano:
500-1000 LOC para micro-agent + adapters finos.

Si un mecanismo exige otro agente completo, segunda cola, scheduler,
segundo kernel o segundo orquestador -> NO ENTRA.

### MECANISMOS APROBADOS Y ESTADO

PROVEN:
- smolagents @ 30bb116... -> loop minimo, max_steps, ToolOutput, final checks.
- Muse Glimmer -> parser ATEM + reason/action/result/observation/correction.
- Muse Code SDK -> command_id/replay/idempotency pattern, NO cola global Seals.
- OpenCode @ d7b115f... -> exact safe edit + per-path lock + diff/permission.
- Codex @ be6e8eac... -> sandbox/policy/approval execution.
- kimi-agent-sdk @ ed4be6... -> lifecycle/resume contract.
- kimi-agent-rs @ f9186cd... -> typed request/state validation.

REFERENCE hasta cerrar SOURCE_SYMBOL:
- OpenHands action/observation.
- MiniMax Code Plugins capability manifest.
- MetaCua implementation.
- CUA-MCP bridge.
- Meta Agent Cookbook mechanisms.

GAP:
- Kimi-Researcher: commit 9406d8... no demostro codigo ejecutable del
  motor multi-source/cross-check.
- MiniMax-Coding-Plan-MCP: server.py demostro web_search/understand_image,
  NO un planner estructurado. Prohibido llamarlo planner sin simbolo.

EXCLUDED como agentes internos:
kimi_code, kimi_cli, OpenRoom, mmx CLI, mcode, OpenCode, OpenHands, Codex.
Pueden aportar patrones o servir al equipo externo de construccion; no viven dentro de Seals.

Detalle completo y SHAs:
`Claude notas/SEALS-TRAZABILIDAD-COMPONENTES.md`

### CAPACIDAD NATIVA - ACQUISITION + INTEGRATION

Entrada:
URL + COMPONENT + TaskContract.

RECEIVE
-> motor existente descarga/extraccion
-> verify source URL
-> resolve exact commit
-> checkout exact commit
-> SOURCE_COMMIT == CHECKED_OUT_COMMIT
-> inspect
-> classify
-> determine destination
-> prune
-> decapitate external brain/orchestrator
-> extract capability
-> integrate via adapter/plugin aprobado
-> test
-> read-back
-> evidence.

Directorio existente != instalacion valida.
Empty/stale/wrong repo -> FAIL/GAP.
1 path = 1 writer.

Antes de implementar esta capa:
trazar SOURCE_FILE + SOURCE_SYMBOL de los motores existentes.
No crear otro downloader/mover.

### SKILL -> SCHEMA

SKILL
-> objective/inputs/preconditions/actions/acceptance/evidence/failures
-> typed schema
-> validate
-> executable contract.

Los schemas no son prompts decorativos.
Usar templates/validators existentes despues de X-Ray.
No inventar formato desde memoria.

### RESEARCH

Research es capability, NO subagente interno.

ResearchResult:
query
sources[]
source_type
claims[]
cross_check[]
new_evidence
conclusion.

NO_NEW_EVIDENCE -> cambiar estrategia.
Repeticion improductiva -> STUCK/BLOCKED_WITH_TRACE.

Motor concreto:
GAP hasta demostrar codigo fuente trazado.

### FRONTEND / VISUAL

Solo cuando work_surface = FRONTEND o MIXED:

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
-> CODE PASS + BROWSER PASS + VISUAL PASS.

MetaCua/CUA:
detras de Sheriff + sandbox + typed contract + evidence.
Nunca autoridad de PASS.

Regla:
ACTION -> SCREENSHOT NUEVO -> VERIFY.

### ORACLE / EVIDENCE

LLM_OPINION != OBJECTIVE_ORACLE.

TEST
-> ACCEPTANCE
-> EVIDENCE
-> COMPLETION AUDIT
-> PASS.

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
acceptance_id.

Existe=false -> GAP/FAILED.
Provider/auth/timeout/invalid_output -> typed failure.
Tool error -> observation, nunca PASS.
No cierre por cantidad de iteraciones.

### SALIDA 8B - TRAZABILIDAD + REGRESSION SUITE

Cada mecanismo debe tener:
SOURCE_REPO
SOURCE_COMMIT/BLOB
SOURCE_FILE
SOURCE_SYMBOL
BEHAVIOR_EXTRACTED
SEALS_DESTINATION
TEST
EVIDENCE.

Sin SOURCE_SYMBOL:
REFERENCE/GAP, nunca INTEGRATED.

Tests obligatorios:
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
ROLLBACK_AFTER_FAILURE.

Mantener tambien:
12 GOALS de entrada/salida
Ask Council 12 puntos
3 refutaciones independientes
SIM-01..04.

Estos son VALIDATION, no motores internos.

### SALIDA 8C - PRUEBA REAL + CIERRE

Prueba desde Wordflow/host:
3 instancias identicas de Seals
-> 3 nodos/claims/workspaces separados
-> 1 componente dificil distinto por instancia
-> verificar descarga real
-> verificar escritura/materializacion real
-> test/read-back/evidence
-> corregir comportamiento
-> repetir.

NO crear una flota dentro de Seals para hacer esta prueba.

Los "50 mundos" son HOST/INTEGRATION VALIDATION:
cada mundo mantiene su estado/archivos/worker identity.
Seals recibe su TaskContract; no administra los 50 mundos ni las keys.

Cerebras/Router/provider routing:
pertenece al host.
Seals recibe referencias/capabilities; no un pool de API keys interno.

### CONDICION DE CIERRE

CORE demostrado:
TASK_CONTRACT
STRUCTURED_ACTION
SHERIFF/POLICY ADAPTER
IDEMPOTENCY
TOOL_RESULT/OBSERVATION
OBJECTIVE+ACCEPTANCE
OBJECTIVE_ORACLE
REAL_TESTS
EVIDENCE_SHA256
COMPLETION_AUDIT.

HOST INTEGRATION demostrada:
DAG real
CLAIM/LEASE
WRITE_SCOPE
DURABLE_QUEUE/RECOVERY
WATCHDOG/REENQUEUE
CRASH_RESUME
BACKEND/FRONTEND routing
browser/screenshot loop cuando aplique.

VALIDATION demostrada:
regression suite
3 isolated Seals instances
wrong-source-commit
provider/tool failures
no-pass-without-evidence
independent refutation.

Solo entonces:
SEALS WORKER VERIFIED.

PARCHE:
si algo no cierra -> GAP explicito.
Nunca cierre fingido.

---

## OBJETIVO 4 - ORQUESTADOR COMAND CENTER
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
DESTINO: CAPA COMMAND CENTER/WORDFLOW, FUERA DEL CORE DE SEALS.
PROHIBIDO introducir control-plane, key rotation, mirrors o fleet management
dentro de seals_core.
Antes de escribir, hacer X-Ray y fijar la ruta real existente del Command Center;
si aun no existe un destino autorizado -> GAP_DESTINO, no inventar carpeta.
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
