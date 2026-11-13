# 📂 README ÍNDICE COMPONENTES 4 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque: **YAIWES 16–20**  
Inventario fresh: **229 componentes**.  
Regla: estado físico `main` > read-back/hash/tree/test > Crazy Wall/state > Handoff/README > histórico > inferencia. Lo no demostrado se marca `NO VERIFICADO`.

---

## YAIWES 16 — Cadence ➡️ Orquestación durable y fault-tolerant de workflows de larga duración

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Cadence/`  
**Handoff:** nodo `154`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** core orchestration engine de Cadence; README físico confirma backend multi-servicio + DB y workers con implementación de workflow. **Función única representativa: NO VERIFICADA** en esta pasada.  
**Determinista:** **Sí — ≈97% en replay/orquestación** (estimación técnica); Activities/sistemas externos pueden variar.  
**¿Es agente?:** **No**; plataforma/orquestador durable de workflows.  
**Cómo funciona el kernel/core para tomar decisiones:** persiste historial del workflow, entrega trabajo a workers y usa historial/eventos para continuar/reintentar ejecuciones largas tolerando reinicios; la lógica de negocio vive en workflow/worker, no en un LLM.  
**Microflujo horizontal:** `start workflow → persistir historial/estado → task list → worker → workflow decision → activity/task → registrar evento → retry/timer/signal → replay/continuación → completed|failed|cancelled`  
**Contexto estructural:** servicios backend, Cassandra/MySQL/PostgreSQL, workers SDK, historial/trazas, CLI, schema tools, canary/benchmark y Kafka+Elasticsearch opcional.  
**Nivel seleccionado:** durable workflow orchestration engine.  
**Qué aporta a un agente:** continuidad durable de planes largos, retries y recuperación tras fallos sin mantener todo el estado en memoria del agente.

---

## YAIWES 17 — CAMEL ➡️ Runtime multiagente con memoria stateful, tools y ciclos de ChatAgent

**URL raíz / ubicación:** `Core kernel Yaiwes/CAMEL/`  
**Handoff:** nodo `44`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `ChatAgent`, `code/camel/agents/chat_agent.py`; primitivas verificadas `_get_context_with_summarization()`, `_calculate_next_summary_threshold()` y `_update_memory_with_summary()`.  
**Determinista:** **No — ≈35%** del camino agentic completo; memoria/thresholds/tools son programáticos, selección semántica depende del modelo.  
**¿Es agente?:** **Sí**, `ChatAgent` es una implementación concreta dentro de CAMEL.  
**Cómo funciona el kernel/core para tomar decisiones:** combina system message + memoria/contexto, modelo(s), tools y respuesta; conserva estado y comprime memoria por umbrales. El modelo propone la decisión semántica y el runtime administra contexto/tools/continuidad.  
**Microflujo horizontal:** `input → memoria/contexto → threshold → resumir si aplica → modelo → respuesta|tool call → ejecutar tool → registrar resultado/memoria → siguiente paso → respuesta final`  
**Contexto estructural:** `AgentMemory`, `ChatHistoryMemory`, `ScoreBasedContextCreator`, `ModelManager`, `FunctionTool`, tool-call records, summarización progresiva y workforce multiagente.  
**Nivel seleccionado:** multi-agent framework + stateful agent runtime.  
**Qué aporta a un agente:** memoria stateful, tools y patrones multiagente con control explícito del crecimiento del contexto.

---

## YAIWES 18 — Celery ➡️ Dispatch distribuido de tareas mediante broker, workers y estrategias por tipo

**URL raíz / ubicación:** `Core kernel Yaiwes/Celery/`  
**Handoff:** nodo `13`, `IN_PROGRESS_STEP2_PROVENANCE`, paso `2`, target `Agente Yaiwes principal/execution-engine-pool/parallel-dispatch/celery/`.  
**Fuente seleccionada:** `Consumer.create_task_handler()` + `Consumer.update_strategies()`, `celery/worker/consumer/consumer.py`.  
**Determinista:** **Sí — ≈97% en routing/dispatch**; protocolo/lookup/ack-reject son reglas explícitas, timing distribuido puede variar.  
**¿Es agente?:** **No**; distributed task queue/worker runtime.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe mensaje, extrae tipo de task, rechaza formatos/tareas inválidas o desconocidas, resuelve `strategies[type_]` y entrega request a ejecución; ETA y QoS controlan admisión.  
**Microflujo horizontal:** `producer → broker/queue → Consumer → decode headers → task type → strategy lookup → valid? → reserve/QoS/ETA → worker pool → task result → ack|reject/backend`  
**Contexto estructural:** broker, queues, routing, task strategies, worker pool, QoS/prefetch, ETA/timers, acknowledgements, result backend y signals.  
**Nivel seleccionado:** distributed task queue + worker execution pool.  
**Qué aporta a un agente:** paralelismo distribuido y desacoplamiento entre planificación agentic y ejecución real en workers.

---

## YAIWES 19 — Claude-Code ➡️ Agente de programación repo-aware para terminal, IDE y GitHub

**URL raíz / ubicación:** `Core kernel Yaiwes/Claude-Code/`  
**Handoff:** nodo `45`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `code/README.md` + manifiesto: snapshot `anthropics/claude-code` commit `18be13be81538c38efa5cb157fb2fc8da7469855`, 1027 archivos, extracción/reconstrucción verificadas. **Función interna única del loop decisor: NO VERIFICADA**.  
**Determinista:** **No — ≈30%**; workflows/tools tienen control programático, pero razonamiento y selección de acciones dependen del modelo.  
**¿Es agente?:** **Sí**; README lo define como herramienta agentic de coding que entiende el codebase y ejecuta tareas y workflows git por lenguaje natural.  
**Cómo funciona el kernel/core para tomar decisiones:** verificablemente recibe instrucciones naturales en contexto de proyecto y ejecuta tareas, explica código y opera Git; símbolo interno exacto que arbitra tool calls queda `NO VERIFICADO`.  
**Microflujo horizontal:** `instrucción natural → contexto codebase → modelo/agente → proponer acción → tool/edición/git → observar resultado → continuar → respuesta/cambio final`  
**Contexto estructural:** terminal/IDE/GitHub, plugins con comandos/agentes, codebase context y workflows Git; procedencia validada por manifiesto.  
**Nivel seleccionado:** agentic coding tool.  
**Qué aporta a un agente:** patrón de coding-agent que trabaja sobre repositorios y combina conversación, edición y Git.

---

## YAIWES 20 — Click ➡️ Parsing y dispatch determinista de comandos CLI componibles

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Click/`  
**Handoff:** nodo `155`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `click.core.Command.main()` / `Command.invoke()` como API central; inventario/README identifica Click como Command Line Interface Creation Kit.  
**Determinista:** **Sí — ≈99%** en parsing/dispatch para mismos argv, entorno y callbacks; side-effects del callback pueden variar.  
**¿Es agente?:** **No**; framework/librería CLI.  
**Cómo funciona el kernel/core para tomar decisiones:** transforma argv en contexto/parámetros tipados, valida opciones/argumentos, selecciona command/subcommand y llama callback; errores siguen rutas explícitas.  
**Microflujo horizontal:** `argv → Command.main → Context → parse args/options → validar/convertir → resolver command/subcommand → invoke callback → resultado|UsageError`  
**Contexto estructural:** commands/groups, contextos, options/arguments, type conversion, decorators, prompts, help y exception handling.  
**Nivel seleccionado:** deterministic CLI command router.  
**Qué aporta a un agente:** interfaz CLI estable para tools, comandos administrativos y entrypoints sin mezclar parsing con razonamiento LLM.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 20`  
`RANGO = 16-20`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 229`  
`SIGUIENTE_BLOQUE = 21-25`  
`ARCHIVO_SIGUIENTE = readme índice componentes 5 .md`
