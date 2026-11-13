# 📂 README ÍNDICE COMPONENTES 2 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque: **YAIWES 06–10**  
Inventario fresh: **229 componentes**.  
Regla: estado físico `main` > read-back/hash/tree/test > Crazy Wall/state > Handoff/README > histórico > inferencia. Lo no demostrado se marca `NO VERIFICADO`.

---

## YAIWES 06 — Aider ➡️ Edición de código repo-aware con reflexión acotada

**Ubicación física:** `Core kernel Yaiwes/Componentes recuperados B/Aider/Aider/`  
**Handoff:** nodo `151`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `Coder`; `Coder.run_one()` + `Coder.get_repo_map()`, `aider/coders/base_coder.py`.  
**Determinista:** **No — ≈40%** del camino completo (estimación técnica): contexto, límites de reflexión, aplicación, git/lint/test son programáticos; la propuesta de cambios depende del modelo.  
**¿Es agente?:** **Sí**, agente/asistente especializado de programación.  
**Cómo decide el core:** construye contexto de archivos/repo map, consulta al modelo, interpreta/aplica ediciones y realimenta errores/reflexión. `run_one()` repite mensajes reflejados hasta que no haya otro o se alcance `max_reflections`.  
**Microflujo horizontal:** `input → preprocess → archivos/URLs → repo map/contexto → send_message/LLM → edición → aplicar → lint/test/git feedback → reflexión? → reintento acotado → resultado`  
**Contexto estructural:** repo map, archivos editables/read-only, historial, Git, lint/test y recuperación/reflexión.  
**Nivel seleccionado:** coding-agent runtime + contexto de repositorio.  
**Qué aporta a YAIWES:** modificación de repositorios con contexto real, aplicación/verificación de cambios y reintento acotado.

---

## YAIWES 07 — AIOS ➡️ Kernel de sistema operativo para agentes y scheduling de syscalls

**Ubicación física:** `Core kernel Yaiwes/AIOS/`  
**Handoff:** nodo `41`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `FIFOScheduler.process_llm_requests()` + `_execute_syscall()`, `code/aios/scheduler/fifo_scheduler.py`.  
**Determinista:** **Sí — ≈92%** en control (estimación técnica); FIFO/dispatch/lifecycle son explícitos, aunque LLM y latencias externas varían.  
**¿Es agente?:** **No**; es kernel/runtime orientado a agentes.  
**Cómo decide el core:** convierte operaciones del agente en syscalls tipadas y las despacha a managers de LLM, memoria, storage y tools; FIFO arbitra el orden y el lifecycle.  
**Microflujo horizontal:** `agent query → SDK/syscall → cola tipada → FIFOScheduler → LLM batch | memory/storage/tool manager → ejecución → status/response/event → agente reanuda`  
**Contexto estructural:** scheduling LLM, context switching, memoria, storage, tool service, managers y eventos de syscall.  
**Nivel seleccionado:** agent-OS kernel + syscall/resource scheduler.  
**Qué aporta a YAIWES:** punto central para arbitrar recursos y desacoplar la lógica del agente de LLM/memoria/storage/tools.

---

## YAIWES 08 — AlphaCodium ➡️ Pipeline de resolución de código guiado por reflexión y tests

**Ubicación física:** `Core kernel Yaiwes/Componentes recuperados B/AlphaCodium/`  
**Handoff:** nodo `152`, `PENDING_STEP1`, paso `1`, target `NO REGISTRADO`.  
**Fuente seleccionada:** `CodeContestsCompetitor.run(problem, iteration=0, logger_ext=None)`, `alpha_codium/gen/coding_competitor.py`.  
**Determinista:** **No — ≈40%** (estimación técnica): el orden de etapas es fijo, pero reflexión, candidatos y código dependen del modelo.  
**¿Es agente?:** **Sí, especializado**, solver/coding flow; no es agente general.  
**Cómo decide el core:** encadena self-reflection, soluciones posibles, elección de candidata, generación de tests, código inicial y evaluación contra tests públicos y AI.  
**Microflujo horizontal:** `problem → set_configurations → self_reflect → possible_solutions → choose_best_solution → generate_ai_tests → initial_code_generation → public_tests → ai_tests → recent_solution`  
**Contexto estructural:** reflexión, candidatos, selección, tests públicos/generados, iteraciones y solución reciente.  
**Nivel seleccionado:** planner/evaluator especializado de código.  
**Qué aporta a YAIWES:** patrón de decisión que somete propuestas a alternativas y tests antes de aceptarlas.

---

## YAIWES 09 — Apache-Airflow ➡️ Orquestación DAG por dependencias, estado y concurrencia

**Ubicación física:** `Core kernel Yaiwes/Apache-Airflow/`  
**Handoff:** nodo `5`, `IN_PROGRESS_STEP2_PROVENANCE`, paso `2`, target `Agente Yaiwes principal/execution-orchestration/dag-executor/apache-airflow/`.  
**Fuente seleccionada:** clase `SchedulerJobRunner`, con `_task_concurrency_allows_execution()`, `code/airflow-core/src/airflow/jobs/scheduler_job_runner.py`.  
**Determinista:** **Sí — ≈95%** en scheduling (estimación técnica); dependencias/estados/límites son reglas explícitas, pero executor, timing, DB y tareas externas pueden variar.  
**¿Es agente?:** **No**; scheduler/orquestador de workflows DAG.  
**Cómo decide el core:** examina DAG runs/TaskInstances, dependencias y estados, aplica concurrencia por DAG/task/run y entrega workloads aptos al executor. No interpreta objetivos NL: ejecuta un grafo definido.  
**Microflujo horizontal:** `DAG → DagRun → SchedulerJobRunner → dependencias/estado → pool/concurrencia → TaskInstance runnable → queue/executor → ejecución → estado → downstream`  
**Contexto estructural:** DAG/DagRun/TaskInstance, metadata DB, estados, pools, executors, callbacks, assets, heartbeats y retries/rescheduling.  
**Nivel seleccionado:** scheduler/orquestador durable de DAGs.  
**Qué aporta a YAIWES:** ejecución reproducible de planes ya descompuestos con dependencias, concurrencia y estado persistente.

---

## YAIWES 10 — APScheduler ➡️ Scheduling temporal y cola de jobs con persistencia/leases

**Ubicación física:** `Core kernel Yaiwes/APScheduler/`  
**Handoff:** nodo `1`, `IN_PROGRESS_STEP2_PROVENANCE`, paso `2`, target `Agente Yaiwes principal/execution-orchestration/task-classifier-scheduler/`.  
**Fuente seleccionada:** clase `AsyncScheduler`; `run_until_stopped()`, `_process_schedules()` y `_process_jobs()`, `src/apscheduler/_schedulers/async_.py`.  
**Determinista:** **Sí — ≈96%** en control temporal (estimación técnica); triggers/leases/admisión son explícitos, pero `jitter` opcional es aleatorio y timing/executors pueden variar.  
**¿Es agente?:** **No**; scheduler/task queue.  
**Cómo decide el core:** adquiere schedules por lease, calcula `next_fire_time`, aplica coalescing/misfire/jitter, crea y persiste `Job`, adquiere jobs hasta `max_concurrent_jobs`, resuelve callable/executor y libera cada job con `JobResult`.  
**Microflujo horizontal:** `task + trigger → acquire schedule lease → fire time → coalesce/misfire/jitter → Job → datastore → acquire job → concurrency → executor → JobResult → release/update`  
**Contexto estructural:** datastore, event broker, schedules, triggers, jobs, backends persistentes, leases, executors, outcomes, concurrencia, cleanup y HA multi-scheduler/worker.  
**Nivel seleccionado:** scheduler temporal + task queue persistente.  
**Qué aporta a YAIWES:** activación futura/recurrencia, cola durable, control de concurrencia y recuperación compartida entre schedulers/workers.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 10`  
`RANGO = 6-10`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 229`  
`SIGUIENTE_BLOQUE = 11-15`  
`ARCHIVO_SIGUIENTE = readme índice componentes 3 .md`