# README ÍNDICE COMPONENTES 15 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque: **YAIWES 71–75** · Inventario fresh: **245**.

Continuidad fresh: `readme índice componentes 14 .md` cerró en YAIWES 70 (`Helicone`). Siguientes físicos: `HelpSteer2`, `Hermes-Agent`, `HiRAS`, `Huey`, `Hugging-Face-Skills`. Todo detalle no demostrado: `NO VERIFICADO`.

## YAIWES 71 — HelpSteer2 ➡️ Dataset recuperado para preferencias/alineamiento
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/HelpSteer2/`.  
**Handoff:** inventario `74`; Crazy Wall nodo `69`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/HelpSteer2/SOURCE_POINTER_RECOVERY.json`: fuente `https://huggingface.co/datasets/nvidia/HelpSteer2`, commit `990b2711a36180dd19d9c94b8627844866f8982a`, `disagreements`, `preference`, `train`, `validation` recuperados, verdict `VERIFIED`. README funcional local: **NO VERIFICADO**.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No; lo demostrado es dataset/artefactos de datos.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel/core propio: **NO VERIFICADO**; una política de decisión no está demostrada.  
**Microflujo horizontal:** `fuente dataset → recuperación verificada → train/preference/disagreements/validation → consumidor externo`.  
**Contexto estructural:** dataset, preference, disagreements, train, validation, recuperación con SHA-256.  
**Nivel seleccionado:** data/alignment evidence layer.  
**Qué aporta a un agente:** datos verificables para procesos externos de preferencia/alineamiento; uso concreto: **NO VERIFICADO**.

## YAIWES 72 — Hermes-Agent ➡️ Agente IA auto-mejorable con herramientas, memoria, skills y subagentes
**URL raíz / ubicación:** `Core kernel Yaiwes/Hermes-Agent/` · código `Core kernel Yaiwes/Hermes-Agent/code/`.  
**Handoff:** inventario `75`; Crazy Wall nodo `169`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Hermes-Agent/code/README.md`: self-improving AI agent, learning loop, creación/mejora de skills, memoria/búsqueda de sesiones, múltiples proveedores, herramientas/RPC, subagentes paralelos y cron.  
**Determinista:** **No globalmente — % NO VERIFICADO**.  
**¿Es agente?:** Sí.  
**Cómo funciona el kernel/core para tomar decisiones:** usa modelo intercambiable, herramientas, memoria/skills y delegación; algoritmo exacto para cada siguiente acción: **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada → modelo → contexto/memoria/skills → herramienta o subagente → ejecución → resultado → aprendizaje/memoria`.  
**Contexto estructural:** model providers, tools, gateway, learning loop, skills, memory, cron, subagents, RPC, execution backends.  
**Nivel seleccionado:** autonomous-agent/orchestration + learning-memory layer.  
**Qué aporta a un agente:** patrón persistente con herramientas, aprendizaje por skills, memoria, automatización y paralelización.

## YAIWES 73 — HiRAS ➡️ Framework multiagente jerárquico para replicación automatizada de papers
**URL raíz / ubicación:** `Core kernel Yaiwes/HiRAS/` · código `Core kernel Yaiwes/HiRAS/code/`.  
**Handoff:** inventario `76`; Crazy Wall nodo `221`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/HiRAS/code/README.md`: Hierarchical Research Agent System, framework multi-agent para automated research paper replication; PaperBench/Paper2Code, API de modelo y entornos aislados.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** Sí, sistema multiagente.  
**Cómo funciona el kernel/core para tomar decisiones:** arquitectura jerárquica declarada; política exacta de coordinación/decisión: **NO VERIFICADO**.  
**Microflujo horizontal:** `paper/benchmark → HiRAS multi-agent → model API → experimento aislado → output`.  
**Contexto estructural:** hierarchical research agents, paper replication, benchmarks, model API, experiment environments.  
**Nivel seleccionado:** hierarchical multi-agent research/execution layer.  
**Qué aporta a un agente:** descomposición jerárquica y ejecución experimental aislada para investigación reproducible.

## YAIWES 74 — Huey ➡️ Cola ligera de tareas con scheduling, retries y pipelines
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Huey/`.  
**Handoff:** inventario `77`; Crazy Wall nodo `70`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Huey/README.rst`: task queue Python; Redis/Postgres/SQLite/filesystem/memory; process/thread/greenlet; scheduling, recurring tasks, retries, priorities, results, locks, rate limits, pipelines/chains, groups/chords.  
**Determinista:** Sí para reglas explícitas dadas condiciones equivalentes, **% NO VERIFICADO**; global: **NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no decide objetivos; aplica cola, prioridad, horario, retry, locking/rate-limit y entrega a consumers.  
**Microflujo horizontal:** `función → enqueue → broker/storage → consumer/worker → ejecución → retry/result → consumidor`.  
**Contexto estructural:** task queue, storage, workers, crontab, retry, priority, locking, pipelines, fan-out/map-reduce.  
**Nivel seleccionado:** task-queue/scheduler execution layer.  
**Qué aporta a un agente:** ejecución asíncrona/programada con retry, prioridad, límites y composición.

## YAIWES 75 — Hugging-Face-Skills ➡️ Skills estandarizadas para tareas AI/ML y operaciones del Hub
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Hugging-Face-Skills/`.  
**Handoff:** inventario `78`; Crazy Wall nodo `71`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Hugging-Face-Skills/README.md`: definiciones para datasets/training/evaluación; Agent Skills; carpetas con `SKILL.md`, YAML, instrucciones/scripts/resources; CLI/MCP; Claude Code, Codex, Gemini CLI y Cursor.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No; son skills consumibles por agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel propio; el agente descubre/carga `SKILL.md` al decidir usarla o por invocación explícita; criterio interno: **NO VERIFICADO**.  
**Microflujo horizontal:** `tarea AI/ML → agente → descubre/carga SKILL.md → instrucciones/scripts/resources → CLI/MCP/Hub → resultado`.  
**Contexto estructural:** Agent Skills, SKILL.md, YAML, hf-cli, CLI/MCP, datasets/models/Spaces/jobs.  
**Nivel seleccionado:** agent-skill/tooling integration layer.  
**Qué aporta a un agente:** capacidades AI/ML empaquetadas y descubribles sin incorporar un nuevo kernel.

---
**COMPONENTES_DOCUMENTADOS = 75**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 76–80**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO = Huginn, Hypothesis, Inngest, Instructor, Intercode**