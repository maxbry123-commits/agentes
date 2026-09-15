# 📂 README ÍNDICE COMPONENTES 5 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque: **YAIWES 21–25**  
Inventario fresh: **229 componentes**.  
Regla: estado físico `main` > read-back/hash/tree/test > Crazy Wall/state > Handoff/README > histórico > inferencia. Lo no demostrado se marca `NO VERIFICADO`.

---

## YAIWES 21 — Cognee ➡️ Memoria persistente para agentes mediante grafo de conocimiento + búsqueda vectorial

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Cognee/`  
**Handoff:** nodo `50`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md` físico; confirma plataforma de memoria AI, ingestión, knowledge graph, embeddings vectoriales, graph reasoning y memoria persistente cross-session. **Función interna única representativa: NO VERIFICADA** en esta pasada.  
**Determinista:** **No — ≈70%** (estimación técnica): persistencia/indexado/recuperación tienen control programático; embeddings, generación de ontología y razonamiento pueden depender de modelos.  
**¿Es agente?:** **No**; plataforma/subsistema de memoria para agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** no es un kernel decisor de objetivos. Ingiere información, la estructura en representaciones vectoriales y de grafo y recupera contexto relacionado para que el agente decida con memoria de largo plazo.  
**Microflujo horizontal:** `datos → ingestión → extracción/embeddings → knowledge graph + vector store → persistencia → consulta/recall → búsqueda semántica + relaciones → contexto → agente`  
**Contexto estructural:** memoria cross-session, knowledge graph self-hosted, vector embeddings, ontology generation, búsqueda, aislamiento user/tenant, trazabilidad e integraciones agentic.  
**Nivel seleccionado:** long-term agent memory / knowledge infrastructure.  
**Qué aporta a un agente:** continuidad de conocimiento entre sesiones y recuperación contextual conectando similitud semántica con relaciones explícitas.

---

## YAIWES 22 — Cognithor ➡️ Agent OS local con PGE-Trinity: Planner → Gatekeeper → Executor

**URL raíz / ubicación:** `Core kernel Yaiwes/Cognithor/`  
**Handoff:** nodo `46`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `code/ARCHITECTURE.md`, sección PGE-Trinity; Planner `core/planner.py`, Gatekeeper `core/gatekeeper.py`, Executor como tercer subsistema.  
**Determinista:** **No — ≈55%** del camino completo (estimación técnica): Planner es LLM-based; Gatekeeper es explícitamente determinista/no-LLM; Executor aplica acciones aprobadas.  
**¿Es agente?:** **Sí**; el proyecto se define como Agent OS autónomo local y contiene un core agentic operativo.  
**Cómo funciona el kernel/core para tomar decisiones:** Planner recibe mensaje + memoria/contexto y produce `ActionPlan`; Gatekeeper aplica ToolEnforcer, credential scan, policy rules, path validation, command safety y risk classification; Executor ejecuta sólo pasos aprobados y devuelve `ToolResult` al Planner para replanificación.  
**Microflujo horizontal:** `mensaje → contexto/memoria → Planner.plan → ActionPlan → Gatekeeper → ALLOW|INFORM|CONFIRM|DENY → Executor → ToolResult → Planner.replan → respuesta`  
**Contexto estructural:** PGE-Trinity, 6-tier memory, model router, context pipeline, HITL, auditoría, sandbox, MCP/tools, canales, evolución y workflows resilientes.  
**Nivel seleccionado:** autonomous agent operating system / guarded agent kernel.  
**Qué aporta a un agente:** separación fuerte entre razonamiento probabilístico, política determinista y ejecución, reduciendo que el LLM tenga acceso directo a filesystem/red.

---

## YAIWES 23 — CognitiveKernel-Pro ➡️ Deep-research agent multi-step con subagentes web/file y selección por ensemble

**URL raíz / ubicación:** `Core kernel Yaiwes/CognitiveKernel-Pro/`  
**Handoff:** nodo `47`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `CKAgent(MultiStepAgent)` y `CKAgent.step_action()`, `code/ck_pro/ck_main/agent.py`.  
**Determinista:** **No — ≈25%**; planificación/acciones/agregación dependen del LLM y puede variar seed; límites, tools y selección/fallback están codificados.  
**¿Es agente?:** **Sí**; README lo describe como agente open-source de deep research y el código implementa `CKAgent`.  
**Cómo funciona el kernel/core para tomar decisiones:** `CKAgent` habilita `web_agent`, `file_agent`, `ask_llm`, búsqueda y stop dentro de un `MultiStepAgent`; cuando una acción puede beneficiarse de múltiples ejecuciones, `step_action()` ejecuta candidatos con seeds/configuración multimodal diferentes, pide al modelo una agregación y selecciona un resultado, con fallback al candidato 0 si falla la selección.  
**Microflujo horizontal:** `query → plan/multi-step loop → action code → web_agent|file_agent|ask_llm|search → ejecución única o N candidatos → agregación LLM → seleccionar candidato → observación → siguiente step → stop`  
**Contexto estructural:** subagentes web/file, tools, prompts plan/action/end/aggr, `max_steps=16`, timeouts, multiprocessing ensemble, seeds y soporte multimodal.  
**Nivel seleccionado:** deep-research multi-step agent + ensemble action selection.  
**Qué aporta a un agente:** investigación profunda delegada a subagentes especializados y posibilidad de ejecutar/seleccionar varias alternativas por paso.

---

## YAIWES 24 — Continual-Harness ➡️ Auto-refinamiento online del propio harness sin reset

**URL raíz / ubicación:** `Core kernel Yaiwes/Continual-Harness/`  
**Handoff:** nodo `212`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `HarnessEvolver`; `should_evolve()` + `evolve()`, `code/agents/utils/harness_evolver.py`.  
**Determinista:** **No — ≈45%**: el disparo temporal es determinista (warmup 25; frecuencia 25 hasta step 200 y 100 después), pero las reescrituras de prompt/subagents/skills/memory usan un Refiner LLM.  
**¿Es agente?:** **No como componente global**; es un framework/harness de adaptación que hospeda agentes y modifica su scaffold.  
**Cómo funciona el kernel/core para tomar decisiones:** observa ventanas recientes de trayectoria, decide determinísticamente cuándo evolucionar y ejecuta cuatro pases independientes: prompt, subagents, skills y memory. Cada pase puede fallar sin bloquear los demás; se incrementa generación y persiste evolution log.  
**Microflujo horizontal:** `trayectoria continua → should_evolve(step) → ventana reciente → Refiner → evolve prompt → CRUD subagents → CRUD skills → CRUD memory → guardar generation/log → continuar episodio sin reset`  
**Contexto estructural:** scaffold `continualharness`, `evolve_harness`, PromptOptimizer, stores de memoria/skills/subagents, trajectory history, bootstrap de harness previo y MCP para agentes CLI externos.  
**Nivel seleccionado:** online self-improving agent harness / in-context adaptation.  
**Qué aporta a un agente:** capacidad de corregir su propio prompt, subagentes, skills y memoria durante una ejecución larga basándose en fallos observados, sin reiniciar el episodio.

---

## YAIWES 25 — Contextual-AI ➡️ Componente de contexto/RAG para agentes

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Contextual-AI/`  
**Handoff:** según inventario fresh, componente siguiente tras Continual-Harness; **nodo/target: NO VERIFICADO** en esta pasada.  
**Fuente seleccionada:** **NO VERIFICADA**: no se obtuvo un símbolo interno fiable antes del cierre de este bloque.  
**Determinista:** **NO VERIFICADO**.  
**¿Es agente?:** **NO VERIFICADO**.  
**Cómo funciona el kernel/core para tomar decisiones:** **NO VERIFICADO**; no se atribuye lógica decisora sin fuente física leída.  
**Microflujo horizontal:** `NO VERIFICADO`  
**Contexto estructural:** `NO VERIFICADO`.  
**Nivel seleccionado:** `NO VERIFICADO`.  
**Qué aporta a un agente:** `NO VERIFICADO`.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 25`  
`RANGO = 21-25`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 229`  
`SIGUIENTE_BLOQUE = 26-30`  
`ARCHIVO_SIGUIENTE = readme índice componentes 6 .md`
