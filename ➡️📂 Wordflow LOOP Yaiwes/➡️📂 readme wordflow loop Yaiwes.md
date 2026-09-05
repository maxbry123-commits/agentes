# ➡️📂 readme wordflow loop Yaiwes

## RECUPERACIÓN

El ledger literal completo y válido anterior se conserva íntegro en Git en el commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc` y blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`. Ese blob contiene los INPUT BLOCKS literales anteriores, incluida Parte 1, y sigue siendo ancla de recuperación. Este README continúa la bitácora sin invalidar ese origen.

## ANCLAS DE ESTADO / CHECKPOINT / RECOVERY / CRAZY WALL

- README canónico: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- STATE JSON: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- RECOVERY PATCH: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/RECOVERY-PATCH.md`
- CRAZY WALL bitácora: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- Regla: README = contrato y guía humana; STATE = estado estructurado; CHECKPOINT = punto recuperable; RECOVERY PATCH = restauración; CRAZY WALL = bitácora humana. Si divergen, el estado efectivo es GAP.

---

## INPUT BLOCK 014 — DIRECTOR — LITERAL

Ok te mandé auditar todo hasta el code integralo   
Envía copias el lote de archivo que necesitas y solo reescribe la parte del plugins y cableas lo metes en una capa o donde corresponda revisa la arquitectura del documento md si falta algo agun code lo resuelves   resuelves es  

Y lo llevas directo al destino de la estructura raíz de el wordflow lo puedes mover todo

---

## PARTE 3 — CAPA DE PROGRAMACIÓN — APROBADA/ANOTADA

### Contrato funcional acordado

1. Antes de programar, clasificar determinísticamente qué es la pieza requerida y dónde pertenece: `WORKFLOW | CORE/KERNEL | RAZONAMIENTO | CONTROL/GOBERNANZA | MEMORIA | EJECUCIÓN | VERIFICACIÓN/TEST | PERSISTENCIA | OPTIMIZACIÓN`.
2. El WORKFLOW no programa directamente: controla qué debe hacerse, en qué orden, con qué contexto, qué capacidad/agente ejecutor puede hacerlo, cómo se valida, cómo se recupera y cuándo se publica.
3. El arquitecto/Council analiza y prepara el contrato; no implementa la tarea del ejecutor. OpenClaw y Hermes se conservan por ahora para auditoría/documentos; los agentes de programación serán definidos posteriormente por el Director.
4. REUSE antes de generar: código existente del proyecto/repos autorizados → catálogo de 105 capacidades deterministas → librería madura/PyPI → repositorio de referencia GitHub/Papers With Code → código nuevo solo si no existe una opción madura que satisfaga el contrato.
5. Los 105 algoritmos son capacidades Python reales, no prompts para LLM. Candidatos a `reasoning_kernel/decision_on_demand/reasoning_modules/`; el router puede seleccionarlos y `decision_on_demand` debe poder invocar directamente la función sin consumo de LLM cuando corresponda.
6. Enchufe Universal/Ficha: capacidades deterministas usan `ejecucion.kind: code`; razonamiento que realmente requiera modelo usa `ejecucion.kind: llm`. Se conserva el mismo flujo de calificación, registro, contrato, sandbox, cableado, tests, trazabilidad y evidencia.
7. Kernel y control determinista permanecen 0% LLM. El LLM solo entra donde la decisión/razonamiento no pueda resolverse de forma determinista.
8. Skill obligatorio de esta capa: `SKILL-CLASIFICAR-UBICAR-RECICLAR-CODE`: identificar tipo de componente → determinar ruta arquitectónica → localizar/reutilizar código → validar procedencia/licencia/contrato → preparar Ficha → cablear por plugin → probar → generar evidencia.
9. Cada tarea de esta capa hereda Parte 1: 12 goals de entrada + 12 de salida, 12 Ask Consil, planificación antes de ejecución, cola 1×1, Sheriff/Validator/Verifier/Sentinel/Supervisor/Judge/Guardian, verificación cruzada y `evidence_hash` obligatorio.
10. Si una verificación falla: refutar → investigar 20 alternativas distintas → seleccionar resolución trazable → reejecutar → no avanzar hasta PASS; cierre global vuelve al LOOP ante cualquier gap.
11. Código modular/no monolítico: archivos separados, contratos/schemas/DAG/YAML, Ficha y plugin. No se permite rediseñar silenciosamente arquitectura global durante una task.
12. Estado de Parte 3: diseño aprobado y registrado; su implementación/cableado físico queda sujeto a la construcción de las capas correspondientes y a evidencia real.

---

## PARTE 4 — APROBADA — MAPA FUNCIONAL COMPLETO

### Flujo A — documento/arquitectura
`fuentes → índice maestro verificado → 12/12 goals → extracción → clasificación → fusión → auditoría1 → auditoría2 → FACTS/fichas → aprobación → arquitectura por fases pequeñas → raíz anterior/siguiente → DEBE/NO DEBE → DAG/contratos`

### Flujo B — Arquitecto Chat A → Ejecutor Chat B
`10 auditorías → INPUT_BLOCK/Sentinel → MissionContract+GoalLock → 12 Council → análisis→arquitectura→DAG→ROOT_MAP→dependencias→estimación LOC→tasks ≤2000 LOC→CHAT-B individual → código ≤500/bloque → tests+contratos+calidad+trace+EvidencePacket → A verifica/refuta e integra`

### Flujo C — UOOS
Parte 1: `B1 Manifest→B2 State→B3 nodos DSL→B4 DAG→B5 loops L01–L11→B6 Tribunal→B7 plan→B8 Recovery`.
Parte 2: `RT00 versión→RT01 integridad→RT02 preflight→RT03 skills→RT04 resume→RT10 select→RT11 idempotencia→RT12 capability→RT13 memoria→RT14 input→RT20 ejecutar→RT30 Tribunal→RT31 goal-check→RT40 artefactos→RT41 consistencia→RT42 auditoría→RT43 memoria→RT44 optimiza→RT45 entrega`; fallo→`RT80 recovery`; todo DONE→`RT90 cierre`.

### Flujo D — programación / Enchufe
`task_classifier → complexity/profile → ProgrammingInstance(mission/tenant/API/engine/idempotency) → InstancePool(concurrency+estado) → capability registry → executor real → usage ledger`.
Cada artefacto: `documento→Ficha→36 invariantes→contrato I/O→seguridad/sandbox→Tribunal→adapter/plugin→registry→telemetría/evidencia→health/failover`.
El PluginBus candidato que use ejecución dinámica no se declara seguro hasta eliminar o aislar esa ejecución y pasar verificación de seguridad.

### Flujo E — despliegue determinista
Destino definido por Director: `agentes/➡️➡️📂 Agente Yaiwes principal/`.
`deploy_config.yaml reglas+destino+protecciones → organizador --dry-run → plan.json → SIN_REGLA=FAIL / secreto=BLOQUEO → aprobación/validación → copiar/sincronizar según manifest → git add/commit → semver por hashes + CHANGELOG → push → verificar.py: HEAD remoto==local + archivos==plan + tag/version → evidence.json`.
Regla: despliegue = 0% LLM; agente no decide el destino ni rediseña. Sin `evidence.json` no está desplegado.

---

## INPUT BLOCK 015 — DIRECTOR — LITERAL — APROBACIÓN PARTE 4 / PLAN SIGUIENTE

Ok anotalo aprobado parte 4 anotalo 1 a 1 ✅

Ya tenemos más o menos la arquitectura para que inicies 
Revisemos que falta de el tú metodo de trabajo revisa y compara con tus notas que el ➡️📂 readme wordflow loop Yaiwes 

No inicia solo me dices si entiendes 
Siguiente Inicia el LOOP 
Ok tienes 
Por hacer pendiente 
parte 1 ⏳
Parte 2 listo✅
Parte 3 ⏳
Parte 4 ⏳

Cual es tu guía de trabajo 
El readme wordflow loop Yaiwes 

Siguiente paso para ir armando 

Tarea 1 salida 1 📌
1 revisar el plan en cada capa hacer un plan de trabajo y Menlo presentas en capas ejemplo 
Convierte parte 1 y parte 2 y parte 3 y parte 4 en una arquitectura en capas separadas para el wordflow loop Yaiwes 
Como me la vas a presentar un plan de arquitectura ejemplo 
➡️📂 Capa 1 
Micro flujo en español 
➡️📂 Capa 2 
Micro flujo en español 
➡️📂 Capa 3
Micro flujo en español 

➡️ Tarea 2 📌 salida 2 
Yo apruebo y repetimos una verificación cruzada con los documentos hasta que no te falte nada en ningunas de las capas de lo que está en los archivos 



Tarea 3 📌➡️ salida modo LOOP y bucle hasta terminar la tarea 
1. Paso 1 Creas un LOOP bucle de trabajo en programación pendiente de tares del chat gpt sol cada 1 hora 
2. Paso 1 empiezas la investigación Buscar y aclarar todo el  code fuente necesario para crear el wordflow LOOP Yaiwes ➡️ donde en todos los componentes existentes en los repos  ➡️ 📂 agente ➡️📂 agente motores wordflow YAIWES ➡️ osquestador auditor memoria ➡️ router inteligente universal
3. Paso 3 
Copiar y pegar en el destino de el wordflow LOOP Yaiwes el código que falta 
Paso 4. 
Cablear con los plugins 
Paso 5.
Verificación cruzada con los archivos 5 pasada por documentos 
Paso 5 
Análisis de que falta + integración de otras tareas dentro del wordflow 
Paso 6 
Lista de tareas de Claude para hacer que hay que darle dentro del wordflow a los agentes 
Paso 7 
Integración con los agentes cablear hacer espejo de los agentes de programación 
Paso 8
Cablear todos los repositorios de la cuenta Maxbry 123 commint con huggueface para usar los 3 procesadores 
Paso 9 
Integrar el sistema de almacenamiento para el wordflow y los agentes con graphiti y grapify y SQL y el alacenamiento de huggueface 
Paso 10
Integrar las api key de los modelo al wordflow 
Paso 11 
Auditoría y test 

Dime si lo entiendes y si falta algo a los pasos ?

---

## INPUT BLOCK 016 — DIRECTOR — LITERAL — CHECKPOINT / STATE / CRAZY WALL / PLAN COMPLETO

Va a integra en el loop. Y en la planificación de tares del chat gpt sol un checkpoin y parche de recuperación anclado al archivo ➡️📂 readme wordflow loop Yaiwes/ recuerda que debe existir una bitácora stated JSON Craxy wall bitácora cableado con el archivos 

Revisas 

Anota todo en le readme ➡️📂 wordflow loop Yaiwes y confirma. 

Si integralo todo las 
Y prepara el plan completo guía de trabajo detallado no puede ser algo resumido debe estár 1 a 1 toda la información que te di 

Lo montas muy detallado ➡️ readme wordflow loop Yaiwes ✅ 

Y confirmas me presentas en el chat 
1. El enlace del archivo ➡️📂 readme wordflow loop Yaiwes ➡️ con el plan detallado 1 a 1 no resumido 

2. Me presentas todas las capas del wordflow loop Yaiwes separadas con su micro flujo 

3. Verifica 4 veces el plan refuta 3 veces y haces ask consil de 12 pasos y 12 goals de entrada y salida antes de presentarme el plan final si existe un gaps no escalas modo Loops y bucle hasta terminar el plan bien detallado y bien estructurado sin resumir sin elimanar información 

4. El plan detallado debe ser en el readme wordflow loop ➡️ 1. Un DSL Dag shema sheriff validador verificación sentinela supervisor juez guardián y verificación cruzada de cada capa 
➡️ 2. Todo el plan es un shema y cada nodo es una capa 
➡️ Caía nodo debe tener trazabilidad con documentos y con información si la información está en el chat la debes poner 1 a 1
➡️ Cada nodo debe tener el enlace del checkpoin+ y de el stated JSON Craxy wall bitácora donde la ai va anotar el progreso todo cableado 


Dieme si entiendes como vas hacer el plan y que me vas a entregar?

---

# PLAN MAESTRO DETALLADO — WORDFLOW LOOP YAIWES

## 0. CONTRATO GLOBAL DEL PLAN

Todo el plan es un schema de nodos. Cada nodo = una capa independiente. Cada capa debe conservar archivos separados, contrato/Ficha, DSL, DAG, schema, Skill específico si hay razonamiento, system prompt solo donde exista LLM, Sheriff, Validator, Verifier, Sentinel, Supervisor, Judge, Guardian, verificación cruzada, checkpoint, state, recuperación y evidence_hash.

### Regla de determinismo
- Kernel/control: 0% LLM.
- Código general: determinista por defecto.
- LLM: solo decisión/razonamiento donde no exista resolución determinista suficiente.
- Reproducibilidad: mismo input + mismo estado + mismas dependencias versionadas → mismo output determinista.

### Microflujo obligatorio de TODO nodo
`12 GOALS INPUT → analiza literal → prioridades → planifica → cola 1×1 → ejecuta un paso → Sheriff → Validator → Verifier → Sentinel/Supervisor → Judge/Guardian → verificación cruzada → PASS? → NO: refuta + 20 alternativas + recovery + reinyección → SÍ: checkpoint + evidence_hash → siguiente → verificación global → checklist/salida`.

### 12 GOALS DE ENTRADA obligatorios de TODO nodo
1. Identidad literal del nodo/capa.
2. Objetivo primario único y bloqueado.
3. Criterios exactos de éxito.
4. Criterios exactos de fallo.
5. Input/schema esperado.
6. Fuentes/chat/documentos con ruta/URL/SHA.
7. Dependencias previas obligatorias.
8. Destino arquitectónico exacto.
9. Política determinista/LLM permitida.
10. Riesgos/permisos/secretos/side-effects.
11. Checkpoint y recovery disponibles antes de mutar.
12. Evidence esperado para poder cerrar.

### 12 GOALS DE SALIDA obligatorios de TODO nodo
1. Output conforme al schema.
2. Objetivo primario satisfecho/refutado explícitamente.
3. Dependencias verificadas.
4. Ruta destino confirmada.
5. Contrato/Ficha validado.
6. Plugin/cableado declarado y comprobado cuando aplique.
7. Tests/checks reales registrados.
8. Cambios con SHA/diff/ruta trazable.
9. `evidence_hash` calculado/registrado cuando exista evidencia real.
10. STATE actualizado.
11. CHECKPOINT actualizado y rollback posible.
12. Estado final literal: PASS | GAP | INCONCLUSIVE; solo cierre global con evidencia suficiente.

### 12 ASK CONSIL obligatorios antes de cerrar un nodo
1. ¿El objetivo literal fue preservado sin reinterpretación?
2. ¿La ruta destino es la aprobada por el Director?
3. ¿Existe ya una pieza reutilizable que evita reescribir?
4. ¿Las fuentes fueron leídas o solo referenciadas?
5. ¿El contrato I/O es suficiente y cerrado?
6. ¿Hay alguna acción que un LLM esté intentando ejecutar y deba ser determinista?
7. ¿Sheriff/deny-list permite la operación?
8. ¿Validator y Verifier comprobaron cosas distintas e independientes?
9. ¿Maker y Checker están separados donde importa?
10. ¿Existe recovery real por SHA/checkpoint antes de la mutación?
11. ¿La evidencia prueba funcionalidad o solo presencia de archivo?
12. ¿Queda algún GAP documental, de código, cableado, test, despliegue, secreto, infraestructura o destino?

### Estado y recuperación cableados en cada nodo
- `[README](../➡️📂 readme wordflow loop Yaiwes.md)` como guía/contrato.
- `[STATE](Crazy Wall Orquestador/STATE.json)` como estado estructurado.
- `[CHECKPOINT](Crazy Wall Orquestador/CHECKPOINT.json)` como punto recuperable.
- `[RECOVERY PATCH](Crazy Wall Orquestador/RECOVERY-PATCH.md)` como procedimiento de rollback/reinyección.
- `[CRAZY WALL](Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md)` como bitácora humana.

---

# ARQUITECTURA POR CAPAS / NODOS

## ➡️📂 CAPA 0 — Gobierno, ledger, state, checkpoint y recovery
**Objetivo:** ninguna capa puede trabajar sin mission_id, trace_id, nodo literal, estado y punto recuperable.
**Microflujo:** `input literal → hash/ID → STATE → checkpoint pre-mutation → ledger/Crazy Wall → Sheriff → permitir/bloquear → ejecutar nodo → evidence → checkpoint post-step`.
**DSL/DAG:** define estados `PENDING→RUNNING→PASS|GAP|FAILED→RECOVERY→RUNNING` y prohíbe saltos sin evidencia.
**Schema:** mission_id, trace_id, node_id, source_refs, destination, expected_evidence, current_state, previous_sha, recovery_ref.
**Gobierno:** Sheriff bloquea mutación sin checkpoint; Sentinel vigila deadline/heartbeat; Supervisor coordina; Judge valida cierre; Guardian protege integridad/secretos.
**Trazabilidad:** README + STATE + CHECKPOINT + Recovery + Crazy Wall.

## ➡️📂 CAPA 1 — Intake, InputBlockReader, objetivo y GOAL_LOCK
**Objetivo:** leer instrucción literalmente, extraer verbo/meta/criterios y fijar un objetivo primario.
**Microflujo:** `input → InputBlockReader/hash-chain → extracción literal → goal-dual-driver → GOAL_LOCK → 12/12 goals → contrato de misión → PASS/GAP`.
**No debe:** fusionar instrucciones distintas ni inventar metas.
**Salida:** MissionContract + objetivo primario + secundarios + criterios éxito/fallo + fuente literal.

## ➡️📂 CAPA 2 — Investigación
**Objetivo:** aclarar qué información/código necesita el nodo antes de escribir.
**Microflujo:** `consulta literal → chat/historial → repo/código interno → repos Maxbry autorizados → OSS/docs oficiales/PyPI/Papers With Code cuando aplique → comunidad secundaria → filtrar → deduplicar → rankear → registrar URL/ruta/SHA/licencia/fecha`.
**Fuentes prioritarias:** `agentes/Core kernel Yaiwes`, `NCT core/wordflow code`, `Agentes-motores-Wordflow-YAIWES`, especialmente orquestador/auditor/memoria/router inteligente universal.
**Salida:** lista de candidatos reutilizables y GAPs reales; sin fuente real no se inventa.

## ➡️📂 CAPA 3 — Auditoría forense X-Ray de documentos
**Objetivo:** convertir documentos en requisitos verificables de arquitectura y código.
**Microflujo:** `índice maestro → lectura real → 12 goals → extracción → clasificación → fusión → AUDIT_1 consistencia → AUDIT_2 cobertura → 12 Ask Consil → conclusión de qué código debe existir → buscar ruta real → existe? PASS; no existe? nuevo objetivo/tarea`.
**Cada item:** ID, tipo, contenido, evidencia textual, origen, estado, confianza, fuentes, dependencias, trace.
**Reglas:** duplicado=merge; contradicción=CONFLICTIVO; variante=coexistencia; fuente solo referenciada no prueba completitud.

## ➡️📂 CAPA 4 — Auditoría forense X-Ray de código
**Objetivo:** comprobar si el código exigido por documentos existe, funciona y está cableado.
**Microflujo:** `requisito documental → ruta esperada → búsqueda global → leer código → imports/símbolos/contratos/tests → comparar documento↔código → status WIRED|PARTIAL|STUB|GAP → tarea pendiente con ID`.
**Verificación:** presencia de nombre no cuenta como implementación; import no cuenta como integración; archivo sin test/evidencia no cierra.

## ➡️📂 CAPA 5 — Reuse / copiar / mover
**Objetivo:** reutilizar sin reescribir.
**Microflujo:** `candidato → SHA origen → licencia/procedencia → compatibilidad → copy exacto → SHA destino → comparar origen==destino → registrar`.
**Regla:** `REUSE > COPY/MOVE > PATCH PEQUEÑO > ADAPTER > GENERATE DELTA`.
**Solo puede reescribirse:** adapter/plugin/cableado o delta faltante expresamente necesario y autorizado.

## ➡️📂 CAPA 6 — Adquisición GitHub Action / descarga y extracción
**Objetivo:** traer código externo/repo fuente de forma reproducible y trazable.
**Microflujo:** `source list → GitHub Action → descarga/clonado → validar LFS/SHA/archive → extracción → manifest/provenance → scan → staging → evidence → entregar a X-Ray/copy`.
**Skill fuente:** `skills Github acción`; política `DO_NOT_REWRITE_CODE / COPY_THEN_SURGICAL_EDIT`.
**No integra por sí sola:** descarga ≠ integración.

## ➡️📂 CAPA 7 — Evolución de capacidades
**Objetivo:** decidir si una capacidad faltante debe reutilizarse, adaptarse, adquirirse o crearse.
**Microflujo:** `trigger → classify target → 12 INPUT goals → reuse research → 12 Consil → classify → proposal → Director gate → acquire → sandbox → mount → verify`.
**No debe:** importar externamente directo al kernel sin contrato/sandbox.

## ➡️📂 CAPA 8 — Clasificador arquitectónico de programación
**Objetivo:** saber qué es el código y dónde pertenece antes de programar.
**Tipos:** `WORKFLOW | CORE/KERNEL | RAZONAMIENTO | CONTROL | MEMORIA | EJECUCIÓN | TEST | PERSISTENCIA | OPTIMIZACIÓN`.
**Microflujo:** `task → type → destination → blast radius/criticality → complexity → profile → existing capability? → instance request`.
**Skill:** `SKILL-CLASIFICAR-UBICAR-RECICLAR-CODE`.

## ➡️📂 CAPA 9 — Reasoning modules deterministas / catálogo 105
**Objetivo:** usar algoritmos reales como capacidades `ejecucion.kind: code`, no como prompts.
**Microflujo:** `problema → expert_panel_router → capability match → deterministic function → output → verify`; solo si no existe opción suficiente → `ejecucion.kind: llm`.
**Familias:** Prelude, investigación, análisis, lógica formal, conclusiones, decisiones difíciles, descubrimiento, Coda, persistencia, verificación, optimización.
**Regla:** buscar implementación madura antes de escribir: proyecto → PyPI → GitHub/Papers With Code → implementación nueva solo como último recurso.

## ➡️📂 CAPA 10 — Arquitecto Chat A / Council
**Objetivo:** preparar trabajo para ejecutores sin programar directamente.
**Microflujo:** `10 auditorías → INPUT_BLOCK/Sentinel → MissionContract/GoalLock → 12 Council → análisis → arquitectura → DAG → ROOT_MAP → dependencias → LOC estimado → dividir tareas ≤2000 LOC → contrato individual por tarea`.
**Parte 1 añadida:** 12 goals input/output + 12 Ask Consil + plan previo + próximo paso único + evidencia esperada.
**OpenClaw/Hermes:** se mantienen para auditoría/documentos mientras el Director no designe programadores definitivos.

## ➡️📂 CAPA 11 — Ejecutor Chat B / motor de programación
**Objetivo:** ejecutar UNA tarea cerrada, sin rediseñar.
**Microflujo:** `TaskContract → classifier → ProgrammingInstance → engine_binding → sandbox/worktree → reuse/code delta → tests → EvidencePacket → return a Chat A`.
**ProgrammingInstance:** tenant_id, mission_id, api_slot, engine_binding, parent_workflow_id, profile, handle, status, budget, idempotency_key.
**Pool:** aislamiento por tenant, concurrency cap, dedup, transiciones válidas, fallback/queue si motor ocupado.
**Límites:** ≤500 líneas por bloque; funciones pequeñas; sin secretos en logs.

## ➡️📂 CAPA 12 — Espejo y registro de agentes de programación
**Objetivo:** desacoplar el workflow de proveedores/agentes concretos.
**Microflujo:** `capability registry → engine_binding → adapter gateway → agente elegido → result contract → EvidencePacket`.
**Regla:** el motor es compartido; se multiplican instancias, no copias del motor.
**Pendiente Director:** nombres definitivos de agentes programadores.

## ➡️📂 CAPA 13 — Enchufe Universal + Ficha/Contrato
**Objetivo:** toda pieza conectable declara qué consume, produce, ejecuta, permisos y recuperación.
**Microflujo:** `candidate → static analysis → Ficha → invariantes → I/O compatibility → security/sandbox → Tribunal → adapter → registry → health → telemetry → evidence → mount`.
**Kinds:** code, llm, db, api, tool, agent; para 105 algoritmos: `code`.
**Seguridad:** cualquier ejecución dinámica del código candidato queda bloqueada/aislada hasta revisión y pruebas de seguridad.

## ➡️📂 CAPA 14 — Orquestación / Scheduler / Time-Wheel / cola 1×1
**Objetivo:** ordenar dependencias y mantener el LOOP vivo sin monolito.
**Microflujo:** `DAG → topological sort → scheduler → deadline/timeout → queue → dispatch → heartbeat → watchdog → completion/failure event`.
**Puede evaluar Dagu/Prefect u otro solo si mejora el contrato; no se introduce por decoración.

## ➡️📂 CAPA 15 — Persistencia OpenMythos adaptada al workflow
**Objetivo:** reinyección persistente del contrato/objetivo original hasta obtener evidencia.
**Microflujo:** `Prelude(anchor original) → intento → verify/refute → FAIL? investigación 20 alternativas distintas → resolución determinista → reinyección mismo anchor → repetir → PASS → Coda`.
**Profundidad:** mecanismo de insistencia 20/20, no afirmación de benchmark 20×.
**Recovery:** checkpoint + rollback + replan antes de nuevo delta.

## ➡️📂 CAPA 16 — Heartbeat, memoria y mecanismos
**Objetivo:** que el kernel detecte pausa, cuelgue, cambio de estado y necesidad de snapshot.
**Inventario a validar:**
LEVEL 1 reasoningBank, hierarchicalMemory, learningBridge, hybridSearch, tieredCache.
LEVEL 2 memoryGraph, agentMemoryScope, vectorBackend, mutationGuard, gnnService.
LEVEL 3 skills, explainableRecall, reflexion, attestationLog, batchOperations, memoryConsolidation.
LEVEL 4 causalGraph, nightlyLearner, learningSystem, semanticRouter.
LEVEL 5 graphTransformer, sonaTrajectory, contextSynthesizer, rvfOptimizer, mmrDiversityRanker, guardedVectorBackend.
**Microflujo:** `heartbeat → snapshot → stale/deadline check → Sentinel/watchdog → retry/circuit-breaker → recovery/checkpoint → resume`.

## ➡️📂 CAPA 17 — Auditoría adversarial + cruzada + Maker-Checker + Tribunal
**Objetivo:** demostrar que documento, código, cableado y resultado son equivalentes.
**Microflujo:** `maker result → adversarial audit → cross-document/code audit → checker independiente → Judge → Guardian → PASS? evidence_hash : return task to LOOP`.
**Recovery chain:** `RETRY → ROLLBACK → CHECKPOINT → REPLAN → ESCALATE solo si el contrato exige decisión humana`.

## ➡️📂 CAPA 18 — UOOS Parte 1 / diseño ejecutable
**Objetivo:** convertir arquitectura aprobada en documentos/nodos ejecutables.
**Microflujo:** `B1 Manifest → B2 State → B3 Nodes DSL → B4 DAG → B5 Loops L01–L11 → B6 Tribunal → B7 Plan → B8 Recovery`.
**Mapeo:** cada fase/nodo del Pipeline se vuelve nodo UOOS; raíz estructural → I/O; sello de gobierno → validaciones.

## ➡️📂 CAPA 19 — UOOS Parte 2 / runtime
**Objetivo:** ejecutar los documentos de Parte 1 de forma controlada.
**Microflujo:** `RT00 version → RT01 integrity → RT02 preflight → RT03 skills → RT04 resume → RT10 select → RT11 idempotency → RT12 capability → RT13 memory → RT14 input → RT20 execute → RT30 Tribunal → RT31 goal-check → RT40 artifacts → RT41 consistency → RT42 audit → RT43 memory → RT44 optimize → RT45 deliver`.
**Fallo:** `RT80 recovery`; cierre total: `RT90`.

## ➡️📂 CAPA 20 — Despliegue determinista
**Objetivo:** publicar solo artefactos aprobados, sin decisiones de LLM.
**Destino:** repo `agentes` → `➡️➡️📂 Agente Yaiwes principal/`.
**Microflujo:** `deploy_config.yaml → manifest/destination rules → dry-run organizador → plan.json → SIN_REGLA=FAIL → secret scan/BLOCK → verify approved artifact/evidence → copy/sync → git add → commit → semver/hash + changelog → push → remote HEAD verification → compare files vs plan → tag/version verification → evidence.json`.
**Rollback:** conservar commit anterior y punto de retorno antes de push; si verificación remota falla, estado GAP y recovery.
**Regla:** el agente recibe comandos/plan exactos; no decide despliegue.

## ➡️📂 CAPA 21 — Integración repos Maxbry ↔ Hugging Face compute
**Objetivo:** conectar repos/capacidades a los 3 procesadores solo después de verificar infraestructura real.
**Microflujo:** `inventario repos → capability map → credential refs → compute endpoint/runtime check → resource broker/leases → adapter → test pequeño → telemetry → evidence`.
**No asumir:** disponibilidad, RAM, endpoints o permisos hasta verificar runtime.

## ➡️📂 CAPA 22 — Almacenamiento y memoria externa
**Objetivo:** integrar Graphiti, Grapify, SQL y almacenamiento Hugging Face con contratos separados.
**Microflujo:** `data class → retention/schema → connector capability → secret ref → sandbox/test → write/read consistency → backup/checkpoint → evidence`.
**Separación:** memoria de agente, grafo, SQL transaccional y blobs/storage no se mezclan como una sola base.

## ➡️📂 CAPA 23 — APIs/modelos y secretos
**Objetivo:** conectar modelos sin incrustar API keys en repo/chat/README/STATE.
**Microflujo:** `provider capability → secret reference → adapter/gateway → allowed models/actions → timeout/budget → healthcheck → test → telemetry → evidence`.
**Regla:** las API keys se guardan en secret store/variables protegidas; el plan solo conserva referencias y nombres lógicos.

## ➡️📂 CAPA 24 — Auditoría final, test E2E, SBOM y cierre
**Objetivo:** demostrar el sistema de punta a punta.
**Microflujo:** `unit → contract → integration → E2E reception→mission→decision→execution→evidence→closure → secret scan → SBOM → placeholder/stub audit → 4 verification passes → 3 refutations → 5 document cross-checks → final gap registry → verdict`.
**Cierre:** solo `VERIFIED_CLOSED` cuando no quedan gaps críticos y cada nodo tiene evidencia real.

---

# PLAN DE TRABAJO DE LAS TAREAS DEL DIRECTOR

## TAREA 1 — SALIDA 1 — arquitectura en capas
1. Leer README + STATE + Crazy Wall.
2. Reconciliar Parte 1/2/3/4 contra sus documentos fuente.
3. Instanciar las capas 0–24 anteriores como plan aprobado/no aprobado.
4. Mostrar al Director cada capa con microflujo en español.
5. No mover arquitectura física adicional hasta aprobación del mapa.

## TAREA 2 — SALIDA 2 — aprobación + verificación cruzada
Después de aprobación del Director:
1. Pasada 1: cobertura literal chat/README.
2. Pasada 2: documentos MD/HTML del intake y arquitectura.
3. Pasada 3: código existente y rutas reales.
4. Pasada 4: contratos/plugins/tests/evidencia.
5. Pasada 5: contradicciones, duplicados, versiones mejores y gaps.
6. Cualquier gap vuelve a la capa origen; no se elimina para cerrar artificialmente.

## TAREA 3 — SALIDA LOOP DE CONSTRUCCIÓN
### Paso 1 — LOOP horario ChatGPT Sol
Se prepara un trabajo recurrente cada 1 hora con checkpoint/STATE/Crazy Wall y recovery. La automatización se crea cuando se active la fase de ejecución del LOOP; cada iteración retoma el siguiente nodo pendiente, verifica evidencia y no repite ciegamente el mismo delta fallido.
### Paso 2 — investigación de código
Buscar/aclarar code fuente en `agentes`, `Agentes-motores-Wordflow-YAIWES`, orquestador, auditor, memoria, router inteligente universal, otros repos Maxbry y fuentes OSS cuando haga falta.
### Paso 3 — copiar código faltante
Copy/reuse por SHA hacia la capa destino; no reescribir lógica existente.
### Paso 4 — cablear plugins
Ficha/contrato → adapter/plugin → registry → health/evidence.
### Paso 5A — verificación documental 5 pasadas
Aplicar las cinco pasadas definidas en Tarea 2.
### Paso 5B — análisis de gaps e integración de tareas
Actualizar gap registry; convertir cada ausencia probada en nodo/tarea.
### Paso 6 — lista de tareas para agentes
Cada tarea: ID, objetivo, contexto mínimo, rutas, dependencias, LOC estimado, prohibiciones, tests y evidence esperado.
### Paso 7 — integración/espejo de agentes
Registrar engine bindings/adapters; separar arquitecto/auditor de programadores; los programadores concretos quedan a elección del Director.
### Paso 8 — repos ↔ Hugging Face / 3 procesadores
Auditar infraestructura, montar resource broker/leases/adapters y probar sin asumir disponibilidad.
### Paso 9 — almacenamiento
Graphiti + Grapify + SQL + HF storage por conectores y contratos separados.
### Paso 10 — APIs de modelos
Solo referencias de secretos; gateway/adapters; budgets/timeouts/health; ninguna key en repo.
### Paso 11 — auditoría y tests
Unit/contract/integration/E2E, security, SBOM, secret scan, evidence, cierre.

---

# VERIFICACIÓN DEL PLAN — 4 PASADAS

## PASS V1 — cobertura de instrucciones
Se comprobó que el plan contiene: arquitectura por capas, Parte 1–4, microflujos, 12/12 goals, 12 Ask Consil, DSL/DAG/schema/gobierno, research/reuse, GitHub Action, evolución, programación, 105 capacidades, Chat A/B, UOOS 1/2, Enchufe, despliegue, heartbeat/persistencia, agentes, Hugging Face, storage, API/modelos, auditoría/test, checkpoint/state/recovery/Crazy Wall.

## PASS V2 — separación no monolítica
Se comprobó que cada función mayor está en nodo/capa distinta y que estado, recuperación, ejecución, programación, despliegue, storage y APIs no están fusionados en un archivo/rol único.

## PASS V3 — fail-closed y evidencia
Se comprobó que ningún nodo puede declararse DONE solo por presencia de archivo; todos exigen contrato, verificación y evidence_hash; los secretos no se guardan en repo.

## PASS V4 — continuidad LOOP
Se comprobó que cada fallo retorna por refutación→20 alternativas→recovery→reinyección del objetivo y que STATE/CHECKPOINT/Crazy Wall permiten retomar sin perder el objetivo.

# REFUTACIÓN DEL PLAN — 3 PASADAS

## REFUTE R1 — ¿Puede el plan cerrar falsamente porque un archivo exista?
Refutado: capa X-Ray + Maker-Checker + evidence_hash separan presencia, wiring, test y cierre.

## REFUTE R2 — ¿Puede un LLM mutar kernel, secretos o despliegue por decisión propia?
Refutado: kernel/control 0% LLM; despliegue determinista; secret references; Sheriff/Guardian bloquean acciones fuera de contrato.

## REFUTE R3 — ¿Puede perderse el trabajo o repetirse un delta fallido?
Refutado por diseño: checkpoint pre/post, state, Crazy Wall, SHA previo, recovery patch e investigación de 20 alternativas distintas antes de reintentar.

# RESULTADO ASK CONSIL 12/12 DEL PLAN
1. Objetivo literal preservado: PASS.
2. Destinos identificados: PASS para Wordflow root y despliegue Yaiwes principal; otros destinos se validan por nodo.
3. Reuse-first explícito: PASS.
4. Fuentes leídas vs referenciadas diferenciadas: PASS.
5. Contratos I/O exigidos: PASS.
6. Determinismo/LLM separados: PASS.
7. Sheriff/deny-list previstos: PASS.
8. Validator/Verifier separados: PASS.
9. Maker/Checker separados: PASS.
10. Recovery previo a mutación: PASS.
11. Evidencia funcional distinta de presencia: PASS.
12. GAPs actuales declarados: ejecución física de Partes 1/3/4, elección final de programadores, runtime HF/storage/API y pruebas E2E quedan PENDING hasta ejecución verificable.

# ESTADO DEL PLAN
`PLAN_MASTER = PASS_DOCUMENTAL / AWAITING_DIRECTOR_PLAN_APPROVAL`.
No equivale a sistema implementado ni `VERIFIED_CLOSED`; las capas de construcción se ejecutarán después de aprobación del mapa y producirán su propia evidencia.
