# 📂 README ÍNDICE COMPONENTES 8 — YAIWES CORE KERNEL

Repositorio `maxbry123-commits/agentes` · rama `main` · **YAIWES 36–40** · inventario fresh **229**.

Regla: estado físico `main` > código/README/manifiesto + Crazy Wall/Handoff. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 36 — DR-WELL ➡️ Cooperación multiagente neurosimbólica con world model simbólico
**URL raíz / ubicación:** `Core kernel Yaiwes/DR-WELL/` (código: `DR-WELL/code/`).  
**Handoff:** nodo `214` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada:** `code/README.md`: ciclo explícito `joint negotiation → individual planning → execution → refinement`; símbolo interno único del ciclo: `NO VERIFICADO`.  
**Determinista:** **No — ≈35%** (estimación técnica): la estructura del ciclo/world model es programática, pero negociación y planificación dependen de LLMs y feedback parcial.  
**¿Es agente?:** **Sí, framework multiagente**; contiene agentes LLM cooperativos, no una sola instancia agente.  
**Cómo funciona el kernel/core:** cada timestep negocia asignación conjunta, cada agente planifica en espacios primitivo/simbólico, ejecuta en CUBE y el world model simbólico actualiza representación/refina estrategia a partir de outcomes conjuntos.  
**Microflujo horizontal:** `estado parcial → negociación conjunta → asignación → planificación individual → acción embodied → outcome → symbolic world model → refinement → siguiente timestep`  
**Contexto estructural:** negociación, planificación simbólica, CUBE, world model compartido y aprendizaje/refinamiento cooperativo.  
**Nivel seleccionado:** multi-agent neurosymbolic reasoning/planning framework.  
**Qué aporta a YAIWES:** patrón de cooperación descentralizada donde agentes coordinan sin intercambiar planes completos y refinan estrategia con modelo simbólico compartido.

## YAIWES 37 — Dramatiq ➡️ Procesamiento distribuido fiable de tareas mediante broker y workers
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Dramatiq/`.  
**Handoff:** nodo `55` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada:** clase `Worker`, `dramatiq/worker.py`; `Worker.start()` arranca middleware/worker threads y `Worker` consume colas declaradas y distribuye mensajes a threads.  
**Determinista:** **Sí — ≈94%** en dispatch/control (estimación técnica); timing, broker, concurrencia, retries y código de actores pueden variar.  
**¿Es agente?:** **No**; es librería de distributed task processing.  
**Cómo funciona el kernel/core:** broker recibe mensajes de actores; consumidores los cargan con prefetch, `Worker` los pone en `PriorityQueue`, worker threads ejecutan y middleware/broker gestionan lifecycle, errores y retries.  
**Microflujo horizontal:** `actor/message → broker queue → ConsumerThread/prefetch → PriorityQueue → WorkerThread → actor execution → middleware/result|retry → ack/requeue`  
**Contexto estructural:** Broker, Consumer, Worker, worker threads, middleware, retries, delay queues, prefetch y resultados.  
**Nivel seleccionado:** distributed task queue/worker runtime.  
**Qué aporta a YAIWES:** ejecución paralela desacoplada de subtrabajos con colas, workers, retry y backpressure/prefetch.

## YAIWES 38 — DSPy ➡️ Programación y optimización de pipelines/loops de modelos de lenguaje
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/dspy/dspy/`.  
**Handoff:** nodo `162` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md`: framework para programar modelos mediante módulos composables y algoritmos que optimizan prompts/pesos; símbolo interno único representativo: `NO VERIFICADO`.  
**Determinista:** **No — ≈45%** (estimación técnica): composición/compilación/optimización tienen control programático, pero inferencia LM y búsquedas de optimización pueden variar.  
**¿Es agente?:** **No** como framework; puede construir **agent loops** y otros sistemas AI.  
**Cómo funciona el kernel/core:** el desarrollador declara módulos/signatures y un programa composable; DSPy ejecuta el programa con LM y puede optimizar sus instrucciones/demostraciones/pesos según métricas/datos, en vez de mantener prompts manuales.  
**Microflujo horizontal:** `programa declarativo → módulos/signatures → LM calls → output → métrica/datos → optimizer/compiler → prompts/weights mejorados → programa`  
**Contexto estructural:** módulos, signatures, LM adapters, optimizers, métricas, RAG y agent loops.  
**Nivel seleccionado:** declarative LM programming + optimization framework.  
**Qué aporta a YAIWES:** capa para convertir comportamiento LLM en módulos programables y optimizables con evaluación, reduciendo dependencia de prompts artesanales.

## YAIWES 39 — durable_rules ➡️ Motor stateful de reglas/eventos para inferencia y coordinación en tiempo real
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/durable_rules/`.  
**Handoff:** nodo `163` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada:** `libpy/durable/engine.py`, clase `Closure`: `post()`, `assert_fact()`, `retract_fact()`, timers y acceso a facts/pending events; README lo define como micro-framework de coordinación consistente/escalable de eventos.  
**Determinista:** **Sí — ≈98%** para mismas reglas, facts, eventos y estado (estimación técnica); concurrencia/timers externos pueden alterar orden temporal.  
**¿Es agente?:** **No**; es rule/event engine stateful.  
**Cómo funciona el kernel/core:** ingiere eventos/facts asociados a estado/sid, el ruleset correlaciona condiciones, activa acciones y estas pueden publicar nuevos eventos/facts, retractarlos o gestionar timers, formando inferencia reactiva encadenada.  
**Microflujo horizontal:** `event|fact → ruleset/state → pattern/condition match → action Closure → post/assert/retract/timer → nuevo estado/evento → siguiente match`  
**Contexto estructural:** rulesets, facts, events, state sessions, actions/closures, timers y engine nativo.  
**Nivel seleccionado:** complex event processing + deterministic rules engine.  
**Qué aporta a YAIWES:** policy/decision layer reproducible para eventos, estado y reglas que no necesita delegar cada decisión a un LLM.

## YAIWES 40 — E2B ➡️ Sandbox cloud aislado para ejecutar código generado por agentes
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/E2B/`.  
**Handoff:** nodo `57` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md`: `Sandbox.create()`, `sandbox.commands.run(...)` y Code Interpreter `runCode()/run_code()`; infraestructura declarada para ejecutar código generado por IA en sandboxes aislados.  
**Determinista:** **Sí — ≈90%** en lifecycle/API del sandbox (estimación técnica); programa ejecutado, red, paquetes y entorno externo pueden variar.  
**¿Es agente?:** **No**; infraestructura/runtime sandbox para agentes.  
**Cómo funciona el kernel/core:** crea un entorno aislado mediante SDK/API, recibe comandos o código, ejecuta dentro del sandbox y devuelve stdout/resultado; también expone variantes Code Interpreter y Desktop. No decide objetivos semánticos.  
**Microflujo horizontal:** `agent tool-call → Sandbox.create → entorno aislado → commands.run|run_code → proceso → stdout/result/error → agente → cierre sandbox`  
**Contexto estructural:** SDK JS/Python, sandbox lifecycle, command execution, code interpreter y desktop/computer-use APIs.  
**Nivel seleccionado:** isolated code-execution sandbox infrastructure.  
**Qué aporta a YAIWES:** frontera de ejecución aislada para código/herramientas generadas por el agente, separando razonamiento de ejecución potencialmente riesgosa.

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 40` · `RANGO = 36-40` · `TOTAL_COMPONENTES_INVENTARIO_FRESH = 229` · `SIGUIENTE_BLOQUE = 41-45` · `ARCHIVO_SIGUIENTE = readme índice componentes 9 .md`
