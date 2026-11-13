# README ÍNDICE COMPONENTES 14 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque: **YAIWES 66–70** · Inventario fresh: **245**.

Continuidad fresh: `readme índice componentes 13 .md` cerró en YAIWES 65 (`Guidance`). Siguientes físicos: `gVisor`, `Gymnasium`, `Hatchet`, `Haystack`, `Helicone`. Todo detalle no demostrado: `NO VERIFICADO`.

## YAIWES 66 — gVisor ➡️ Kernel de aplicación en userspace para aislamiento de contenedores
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/gVisor/`.  
**Handoff:** inventario componente `69`; Crazy Wall nodo `26`, paso `2`, `IN_PROGRESS_STEP2_PROVENANCE`, destino `Agente Yaiwes principal/execution-orchestration/container-pod-isolation/gvisor/`; `HOLD_KERNEL_MATERIAL`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/gVisor/README.md`: application kernel en Go/userspace, interfaz Linux-like, OCI runtime `runsc`, Docker/Kubernetes.  
**Determinista:** Sí para semántica/configuración dada — **% NO VERIFICADO**; global: **NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no decide metas; intermedia llamadas mediante su interfaz Linux-like en userspace y limita superficie del kernel host.  
**Microflujo horizontal:** `contenedor → runsc → interfaz gVisor → kernel userspace → host kernel permitido → resultado aislado`  
**Contexto estructural:** application kernel, userspace, Linux-like interface, `runsc`, OCI, sandboxing.  
**Nivel seleccionado:** execution isolation/application-kernel layer.  
**Qué aporta a un agente:** aislamiento fuerte para ejecutar workloads/código no confiable.

## YAIWES 67 — Gymnasium ➡️ API estándar de entornos para reinforcement learning
**URL raíz / ubicación:** `Core kernel Yaiwes/Gymnasium/` · código `Core kernel Yaiwes/Gymnasium/code/`.  
**Handoff:** inventario componente `70`; Crazy Wall nodo `220`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Gymnasium/code/README.md`: API estándar algoritmo↔entorno; `reset(seed)`, `step(action)`, observation/reward/terminated/truncated/info y versionado por reproducibilidad.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; seed/versionado ayudan reproducibilidad, pero no prueban determinismo global.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe la acción elegida externamente, avanza el entorno y devuelve observación/reward/terminación; política autónoma: **NO VERIFICADO**.  
**Microflujo horizontal:** `agente → acción → env.step → transición → observation + reward + termination + info → agente`  
**Contexto estructural:** environment, action space, observation, reward, reset/seed, step, versioning.  
**Nivel seleccionado:** reinforcement-learning environment/interface layer.  
**Qué aporta a un agente:** entorno estándar para entrenamiento/evaluación de políticas.

## YAIWES 68 — Hatchet ➡️ Orquestación durable de tareas, agentes IA y workflows
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Hatchet/Hatchet/`.  
**Handoff:** inventario componente `71`; Crazy Wall nodo `22`, paso `2`, `IN_PROGRESS_STEP2_PROVENANCE`, destino `Agente Yaiwes principal/execution-orchestration/state-machine-executor/hatchet/`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/Hatchet/Hatchet/README.md`: background tasks, AI agents, durable workflows, queues, retries, schedules, routing, DAGs, durable waits, priority/rate limits/concurrency y Postgres durability.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; weighted scheduling/concurrencia/eventos impiden afirmar determinismo global.  
**¿Es agente?:** No; orquesta agentes/tareas.  
**Cómo funciona el kernel/core para tomar decisiones:** evalúa triggers/definiciones, enruta por reglas/afinidad, aplica políticas y persiste estado para retry/resume. Decisión semántica de objetivos: **NO VERIFICADO**.  
**Microflujo horizontal:** `trigger → workflow/task → scheduler/routing → worker → ejecución durable → Postgres → retry/resume → resultado`  
**Contexto estructural:** tasks, workers, queues, retries, schedules, events, DAGs, priorities, concurrency, durability.  
**Nivel seleccionado:** durable workflow/state-machine execution layer.  
**Qué aporta a un agente:** ejecución persistente, recuperable, distribuida y observable.

## YAIWES 69 — Haystack ➡️ Framework de orquestación IA para RAG y workflows de agentes
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Haystack/`.  
**Handoff:** inventario componente `72`; Crazy Wall nodo `68`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Haystack/README.md`: pipelines y agent workflows con retrieval, routing, memory, generation; lifecycle hooks, tool calls concurrentes, `SkillToolset`, loops, branches y condicionales.  
**Determinista:** No para generación LLM — **% NO VERIFICADO**; global: **NO VERIFICADO**.  
**¿Es agente?:** No como framework completo; incluye `Agent`.  
**Cómo funciona el kernel/core para tomar decisiones:** componentes explícitos preparan/enrutan contexto; `Agent` invoca LLM/tools; hooks y branches/loops controlan transiciones. Política autónoma completa: **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada → pipeline/contexto → retrieval/routing/memory → Agent/LLM → tools/hooks → branch/loop → resultado`  
**Contexto estructural:** Pipeline, Agent, components, retrieval, routing, memory, generation, tools, hooks, skills.  
**Nivel seleccionado:** AI orchestration/agent-workflow layer.  
**Qué aporta a un agente:** composición transparente de RAG, memoria, herramientas, routing y control de flujo.

## YAIWES 70 — Helicone ➡️ AI Gateway, routing y observabilidad LLM/agentes
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Helicone/Helicone/`.  
**Handoff:** inventario componente `73`; Crazy Wall nodo `168`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/Helicone/Helicone/README.md`: AI Gateway 100+ modelos, intelligent routing, automatic fallbacks, agent tracing, sesiones/traces, coste/latencia/calidad y prompt management.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; routing/fallback depende de configuración/disponibilidad.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe llamadas, enruta proveedor/modelo, aplica fallback si corresponde y registra trazas/métricas; metas/planes autónomos: **NO VERIFICADO**.  
**Microflujo horizontal:** `agente → gateway → routing → modelo → fallback si aplica → respuesta → trace/métricas`  
**Contexto estructural:** gateway, models/providers, routing, fallbacks, traces/sessions, metrics, prompts.  
**Nivel seleccionado:** LLM gateway/routing/observability layer.  
**Qué aporta a un agente:** acceso centralizado a modelos, fallback y trazabilidad operacional.

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 70`  
`RANGO_DOCUMENTAL = 66-70`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 245`  
`PRIMEROS_PENDIENTES_CONSUMIDOS = gVisor | Gymnasium | Hatchet | Haystack | Helicone`  
`SIGUIENTE_ARCHIVO = readme índice componentes 15 .md`  
`SIGUIENTE_SECUENCIA_DOCUMENTAL = 71-75`