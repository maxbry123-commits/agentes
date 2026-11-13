# 📂 README ÍNDICE COMPONENTES 7 — YAIWES CORE KERNEL

Repositorio `maxbry123-commits/agentes` · `main` · **YAIWES 31–35** · inventario fresh **229**.

## YAIWES 31 — Dagu ➡️ Ejecutor local-first de workflows DAG declarativos
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Dagu/`  
**Handoff:** nodo 21 · `IN_PROGRESS_STEP2_PROVENANCE` · target `Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu/`.  
**Fuente seleccionada:** `README.md`: DAG YAML, scheduling, retries, human tasks, run history, shell/Docker/Kubernetes/SSH; símbolo interno único `NO VERIFICADO`.  
**Determinista:** Sí ≈95% en control; ejecución externa/timing puede variar. **¿Es agente?:** No.  
**Kernel/core:** interpreta dependencias declaradas, habilita pasos, aplica scheduling/concurrencia/retries y registra estado; no decide objetivos semánticos.  
**Microflujo:** `YAML DAG → parse → dependencias → runnable → acción → resultado → retry/human gate → downstream → historial`  
**Contexto:** single binary, estado local, scheduler, logs, Web UI, MCP, sub-DAGs/workers. **Nivel:** workflow/DAG executor.  
**Aporta:** ejecución operacional de planes estructurados sin DB/broker externos.

## YAIWES 32 — Dapr ➡️ Runtime distribuido durable para agentes y workflows
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Dapr/`  
**Handoff:** nodo 53 · `PENDING_STEP1` · target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md`: durable execution, state management, event messaging, HTTP/gRPC; símbolo interno único `NO VERIFICADO`.  
**Determinista:** Sí ≈90% en control; red/servicios externos varían. **¿Es agente?:** No.  
**Kernel/core:** encapsula persistencia, comunicación, eventos y recuperación; no razona objetivos.  
**Microflujo:** `agente/workflow → Dapr API → runtime → state|service|pubsub|workflow → persistir → fallo? → recuperar → continuar`  
**Contexto:** sidecar, workflows durables, state stores, messaging, seguridad/observabilidad. **Nivel:** distributed agent runtime.  
**Aporta:** durabilidad, estado y comunicación distribuida desacoplada de infraestructura.

## YAIWES 33 — Dask-Distributed ➡️ Scheduler distribuido stateful para grafos de tareas
**URL raíz / ubicación:** `Core kernel Yaiwes/Dask-Distributed/`  
**Handoff:** nodo 213 · `PENDING_STEP1` · target `NO REGISTRADO`.  
**Fuente seleccionada:** clase `Scheduler`, `code/distributed/scheduler.py`; escucha eventos, controla workers y mantiene estado consistente de tasks/workers.  
**Determinista:** Sí ≈90% en política; concurrencia/timing distribuidos varían. **¿Es agente?:** No.  
**Kernel/core:** mantiene `TaskState`/`WorkerState`, observa eventos y asigna trabajo según estado/recursos.  
**Microflujo:** `task graph → Scheduler state → runnable → idle/saturated workers → asignación → ejecución → evento → actualizar estado → siguiente`  
**Contexto:** scheduler, clients, workers, comms, unrunnable/idle/saturated. **Nivel:** distributed graph scheduler.  
**Aporta:** paralelización distribuida y coordinación stateful de subtrabajos.

## YAIWES 34 — datamodel-code-generator ➡️ Compilación de schemas a modelos Python tipados
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/datamodel-code-generator/`  
**Handoff:** nodo 161 · `PENDING_STEP1` · target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md` + `src/datamodel_code_generator/__init__.py`; soporta OpenAPI/AsyncAPI/JSON Schema/Avro/XSD/Protobuf/GraphQL/MCP/raw data; función central única `NO VERIFICADO`.  
**Determinista:** Sí ≈99% con misma entrada/opciones/versión. **¿Es agente?:** No.  
**Kernel/core:** selecciona parser/output, resuelve referencias/tipos y genera código; sin razonamiento LLM.  
**Microflujo:** `schema → detectar formato → parse/ref graph → tipos → output model → render/format → Python`  
**Contexto:** parsers, graph/ref resolution, formatters, modelos, CLI/agent-skill. **Nivel:** schema-to-code compiler.  
**Aporta:** contratos tipados reproducibles para tools, MCP, APIs y estado.

## YAIWES 35 — DeepEval ➡️ Framework de evaluación y tests para sistemas LLM
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/DeepEval/`  
**Handoff:** nodo 54 · `PENDING_STEP1` · target `NO REGISTRADO`.  
**Fuente seleccionada:** `README.md` + paquete `deepeval/`; función evaluadora única `NO VERIFICADO`.  
**Determinista:** No ≈55% con LLM-as-a-judge; harness/thresholds son programáticos. **¿Es agente?:** No.  
**Kernel/core:** ejecuta métricas sobre casos/salidas y convierte scores/criterios en resultados; no persigue objetivos autónomos.  
**Microflujo:** `test case/output → métrica → judge/model|regla → score/reason → threshold → pass/fail → reporte`  
**Contexto:** métricas, datasets, benchmarks, tracing/evals, modelos. **Nivel:** LLM evaluation/test harness.  
**Aporta:** gates medibles para regresiones, alucinación, relevancia y calidad.

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 35` · `RANGO = 31-35` · `TOTAL_COMPONENTES_INVENTARIO_FRESH = 229` · `SIGUIENTE_BLOQUE = 36-40` · `ARCHIVO_SIGUIENTE = readme índice componentes 8 .md`
