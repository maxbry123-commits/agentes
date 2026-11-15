# 📂 README ÍNDICE COMPONENTES 3 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque: **YAIWES 11–15**  
Inventario fresh: **229 componentes**.  
Regla: estado físico `main` > read-back/hash/tree/test > Crazy Wall/state > Handoff/README > histórico > inferencia. Lo no demostrado se marca `NO VERIFICADO`.

---

## YAIWES 11 — autogen ➡️ Agente conversacional con tools, memoria, handoffs y reflexión

**Ubicación física:** `Core kernel Yaiwes/Componentes recuperados A/autogen/`  
**Handoff:** nodo `48`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `AssistantAgent`, especialmente `on_messages/on_messages_stream` y su ciclo de tool-use, `autogen/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py`.  
**Determinista:** **No — ≈35%** del camino completo: lifecycle, límites de tool iterations, handoff y ejecución son programáticos; selección de herramientas, contenido y razonamiento dependen del modelo.  
**¿Es agente?:** **Sí**; `AssistantAgent` es un agente concreto dentro del framework AutoGen.  
**Cómo decide el core:** mantiene estado/contexto entre llamadas, consulta el modelo, ejecuta tool calls, puede reflexionar sobre resultados, repetir hasta `max_tool_iterations` y emitir handoff o respuesta final.  
**Microflujo horizontal:** `mensajes nuevos → model context/memory → inferencia → texto | tool calls → ejecutar tools → resultados → reflexión opcional → nueva inferencia/iteración → handoff | respuesta final`  
**Contexto estructural:** `ChatCompletionContext`, memory, workbench/tools, handoffs, streaming, structured output, cancellation y estado persistente del agente.  
**Nivel seleccionado:** agent runtime / multi-agent framework.  
**Qué aporta a YAIWES:** patrón de agente con tools, memoria, handoff entre agentes y loop de ejecución/reflexión acotado.

---

## YAIWES 12 — Backend watchdog workflow adaptativo ➡️ Contrato de watchdog durable con reparación de GAP en el paso propietario

**Ubicación física:** `Core kernel Yaiwes/Backend watchdog workflow adaptativo/`  
**Handoff:** nodo `42`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** elemento de protocolo `yaiwes.watchdog.minimax-contract/v1` y ABI `Job.validate/execute/checkpoint/resume/cleanup`, archivo `CONTRATO-MINIMAX-WATCHDOG-PARALELO-SANDBOX-MEMORIA.md`.  
**Determinista:** **Sí — ≈99% como contrato**, pero **implementación runtime completa NO VERIFICADA**; el propio documento declara `ACTIVE / IMPLEMENTATION_PENDING`.  
**¿Es agente?:** **No**; es contrato/arquitectura de watchdog y ejecución.  
**Cómo decide el core:** fuerza tres pasos `ANALYZE_AND_DEFINE → WIRE_AND_RUN → TEST_AND_CLOSE`; un `GAP` vuelve al paso propietario, sin crear fases nuevas. Define owner único por capability, Job ABI, límites de concurrencia, idempotencia, checkpoints, sandbox y métricas.  
**Microflujo horizontal:** `Definition/DSL → schema/ports/owners → wire scheduler+queue+workers+state+memory+sandbox → ejecutar Job → checkpoint/recovery → E2E test → PASS:CLOSED | GAP:repair owning step→repeat`  
**Contexto estructural:** PostgreSQL como state durable, Redis para eventos/leases, pgvector para memoria semántica, artifact storage, bounded pools, priority queue, dedup/backpressure y sandbox.  
**Nivel seleccionado:** watchdog contract + durable execution architecture.  
**Qué aporta a YAIWES:** contrato fail-closed retomable para supervisión, recuperación, paralelismo y cierre por evidencia. **GAP:** no confundir contrato activo con runtime ya implementado.

---

## YAIWES 13 — backoff ➡️ Retry determinista con espera, give-up y límites de tiempo/intentos

**Ubicación física:** `Core kernel Yaiwes/Componentes recuperados B/backoff/`  
**Handoff:** nodo `153`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `retry_exception()` y `retry_predicate()`, `backoff/_sync.py`.  
**Determinista:** **Sí — ≈98%** en control; número de intentos, give-up y límites son explícitos. El jitter configurado, tiempo real y resultado del target pueden variar.  
**¿Es agente?:** **No**; librería de resiliencia/reintentos.  
**Cómo decide el core:** ejecuta el target, evalúa excepción o predicado, comprueba `giveup`, `max_tries` y `max_time`, calcula siguiente espera y decide `retry | giveup | success`.  
**Microflujo horizontal:** `call → success? → return | excepción/predicado → giveup/limit? → sí: stop/raise → no: next_wait(+jitter) → sleep → retry`  
**Contexto estructural:** wait generators, jitter, elapsed time, handlers `on_success/on_backoff/on_giveup`, máximos de intentos/tiempo.  
**Nivel seleccionado:** resilience primitive / retry controller.  
**Qué aporta a YAIWES:** recuperación controlada de fallos transitorios sin implementar bucles de retry distintos en cada herramienta/agente.

---

## YAIWES 14 — Bayesian-Agent ➡️ Evolución de Skills/SOP mediante evidencia bayesiana y política de reescritura

**Ubicación física:** `Core kernel Yaiwes/Bayesian-Agent/`  
**Handoff:** nodo `43`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `RewritePolicy.decide(SkillBelief)`, `code/bayesian_agent/core/policy.py`, apoyado por `core/algorithms/categorical_bayes.py`, `belief.py` y registry físicos.  
**Determinista:** **Mixto — ≈90% en la política seleccionada**: sus umbrales `explore/retire/patch/split/compress` son explícitos; las trayectorias, verificadores y ejecución LLM que generan evidencia no son deterministas.  
**¿Es agente?:** **No como componente único**; es un framework/capa de autoevolución que además incluye un native harness de agente.  
**Cómo decide el core:** convierte trayectorias verificadas en evidencia, actualiza creencias por Skill/SOP y `RewritePolicy.decide()` decide: sin observaciones→`explore`; fallos dominantes→`retire`; failure mode repetido→`patch`; varios contextos→`split`; éxito estable→`compress`; en otro caso→`explore`.  
**Microflujo horizontal:** `trajectory → verifier → evidence(features+success/failure) → Bayesian belief/posterior → rank/RewritePolicy → explore|patch|split|compress|retire → Skill/SOP actualizado → siguiente ejecución`  
**Contexto estructural:** Bayesian Evidence Model categórico, Beta-Bernoulli opcional, failure modes, contextos, tokens, turns, latency, adapters cross-harness, registry, repair y native harness.  
**Nivel seleccionado:** self-evolution / skill-policy subsystem.  
**Qué aporta a YAIWES:** aprendizaje operativo basado en evidencia verificada, reutilizando fallos/éxitos para adaptar Skills y SOPs sin modificar pesos del modelo.

---

## YAIWES 15 — business-rules ➡️ Motor determinista de reglas `all/any` y acciones

**Ubicación física:** `Core kernel Yaiwes/Componentes recuperados A/business-rules/`  
**Handoff:** nodo `49`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `run_all()`, `run()`, `check_conditions_recursively()` y `do_actions()`, `business_rules/engine.py`.  
**Determinista:** **Sí — ≈100%** para un mismo conjunto de variables/reglas/acciones sin side-effects externos.  
**¿Es agente?:** **No**; rule engine.  
**Cómo decide el core:** recorre reglas; evalúa condiciones recursivas `all`/`any`; para hojas resuelve variable+operador+valor; si la condición resulta verdadera ejecuta las acciones declaradas. Puede detenerse en la primera regla disparada.  
**Microflujo horizontal:** `rule_list → run_all → regla → conditions → all/any recursivo → variable → operator comparison → false:next rule | true:do_actions → continue | stop_on_first_trigger`  
**Contexto estructural:** variables tipadas, operadores, reglas serializables, acciones con parámetros y política opcional de primer trigger.  
**Nivel seleccionado:** deterministic rule engine / policy primitive.  
**Qué aporta a YAIWES:** decisiones auditables y reproducibles para routing, gates, permisos o políticas donde no se necesita razonamiento LLM.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 15`  
`RANGO = 11-15`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 229`  
`SIGUIENTE_BLOQUE = 16-20`  
`ARCHIVO_SIGUIENTE = readme índice componentes 4 .md`
