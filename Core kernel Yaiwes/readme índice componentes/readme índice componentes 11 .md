# 📂 README ÍNDICE COMPONENTES 11 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque documental: **YAIWES 51–55**  
Inventario fresh: **245 componentes** (`CORE-KERNEL-COMPONENT-INVENTORY.md`, generado `2026-09-15T07:10:10.674608+00:00`).

> Continuidad fresh: `readme índice componentes 10 .md` cerró en YAIWES 50 con Flagsmith. El inventario actual coloca a continuación Flowable, gatekeeper, Git, Godel-Agent y gpt-researcher. Lo no demostrado por código/README/manifiesto/Handoff se marca `NO VERIFICADO`.

---

## YAIWES 51 — Flowable ➡️ Orquestación BPMN/CMMN y evaluación de reglas DMN

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Flowable/` · fuente física en `Flowable/Flowable/`.  
**Handoff:** inventario fresh: componente `54`; Crazy Wall nodo `61`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Flowable/Flowable/README.md`; demuestra BPMN process engine, CMMN case engine, DMN rule engine, Java/REST API y ejecución embedded/server/cluster/cloud. Símbolo interno único que centralice la decisión: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈98%** para modelo, variables y reglas fijas (estimación técnica); tareas humanas, servicios externos y concurrencia pueden variar el estado operacional.  
**¿Es agente?:** **No**; plataforma/engine BPM y workflow.  
**Cómo funciona el kernel/core para tomar decisiones:** interpreta modelos BPMN/CMMN y reglas DMN; el estado del proceso/caso y las condiciones del modelo determinan qué actividad o rama queda habilitada. La implementación interna única responsable de toda esa decisión no fue demostrada en esta pasada: **NO VERIFICADO**.  
**Microflujo horizontal:** `modelo BPMN/CMMN + reglas DMN → instancia + variables → evaluación de condición/regla → actividad habilitada → tarea humana/sistema → persistencia de estado → siguiente transición → cierre`  
**Contexto estructural:** procesos BPMN, casos CMMN, decisiones DMN, variables, tareas, Java/REST API, persistencia y despliegue distribuido.  
**Nivel seleccionado:** durable BPM/workflow decision engine.  
**Qué aporta a un agente:** convierte planes estructurados en workflows persistentes con reglas, estados, actividades humanas/sistema y reanudación controlada.

---

## YAIWES 52 — gatekeeper ➡️ Control de admisión y políticas para Kubernetes mediante OPA

**URL raíz / ubicación:** `Core kernel Yaiwes/gatekeeper/` · código `Core kernel Yaiwes/gatekeeper/code/`.  
**Handoff:** inventario fresh: componente `55`; Crazy Wall **sin nodo registrado todavía**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/gatekeeper/code/README.md`; demuestra policy library parametrizable, CRDs `constraints`, `constraint templates`, mutation, audit y external data. Símbolo interno único de evaluación/admission: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈99%** para objeto, constraints, templates y external data fijos (estimación técnica); cambios de políticas/datos externos cambian el resultado.  
**¿Es agente?:** **No**; policy/admission control plane.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe recursos Kubernetes en admisión/auditoría, aplica constraints instanciadas desde constraint templates y usa OPA para determinar cumplimiento; además puede mutar recursos según políticas configuradas.  
**Microflujo horizontal:** `recurso Kubernetes → admission/audit → constraint templates + constraints + external data → evaluación OPA → allow/deny/violation o mutation → API server/resultado`  
**Contexto estructural:** Kubernetes CRDs, OPA, constraints, templates, mutation, audit, external data y policy library.  
**Nivel seleccionado:** policy enforcement/admission guardrail.  
**Qué aporta a un agente:** guardrails deterministas antes de ejecutar cambios de infraestructura, con políticas declarativas auditables y posibilidad de bloqueo/mutación.

---

## YAIWES 53 — Git ➡️ Control de versiones distribuido y trazabilidad de cambios

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Git/`.  
**Handoff:** inventario fresh: componente `56`; Crazy Wall nodo `62`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Git/README.md`; lo define como sistema rápido, escalable y distribuido de control de revisiones con operaciones de alto nivel y acceso a internals. Símbolo interno único que represente todo el motor: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈99%** para contenido, árbol, padres y metadatos de commit fijos (estimación técnica); timestamps, identidad, conflictos y concurrencia pueden producir objetos/resultado distintos.  
**¿Es agente?:** **No**; sistema de control de versiones distribuido.  
**Cómo funciona el kernel/core para tomar decisiones:** modela contenido e historial como objetos/referencias y aplica operaciones explícitas de staging, commit, branch, merge/rebase y transferencia. No decide objetivos autónomamente; ejecuta transformaciones de historial solicitadas y detecta conflictos cuando no puede resolver una combinación automáticamente.  
**Microflujo horizontal:** `working tree → diff/status → index/stage → commit/objetos → refs/branch → merge|rebase|cherry-pick → conflicto o nuevo historial → fetch/push`  
**Contexto estructural:** blobs, trees, commits, refs, index, working tree, ramas, remotes, merges y DAG de historial.  
**Nivel seleccionado:** provenance/version-control substrate.  
**Qué aporta a un agente:** checkpoints, rollback, comparación de deltas, procedencia y coordinación reproducible de cambios de código/documentación.

---

## YAIWES 54 — Godel-Agent ➡️ Agente autorreferencial con auto-modificación y mejora recursiva

**URL raíz / ubicación:** `Core kernel Yaiwes/Godel-Agent/` · código `Core kernel Yaiwes/Godel-Agent/code/`.  
**Handoff:** inventario fresh: componente `57`; Crazy Wall nodo `217`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Godel-Agent/code/README.md`; identifica `src/agent_module.py` como core con self-awareness, self-modification y action execution, `src/main.py` como entry point, `src/logic.py` como código generado y describe reward functions + `action_evaluate_on_task` + `solver`. Función/clase interna exacta del ciclo completo: **NO VERIFICADO**.  
**Determinista:** **No — ≈30%** del ciclo completo (estimación técnica): harness/actions/reward plumbing son programáticos, pero generación de política/código y selección LLM son no deterministas.  
**¿Es agente?:** **Sí**; framework de agente autorreferencial para recursive self-improvement.  
**Cómo funciona el kernel/core para tomar decisiones:** parte de una política/solver y un goal prompt, dispone de acciones descritas para invocación LLM, evalúa la política mediante reward/feedback del entorno y puede modificar su propio código/política mediante el módulo de agente; los resultados auto-optimizados se guardan para cada tarea.  
**Microflujo horizontal:** `goal + entorno + solver inicial → agent_module/contexto de acciones → LLM selecciona acción → ejecutar/evaluar → reward/feedback → self-modification/monkey patch → nueva política/código → re-evaluación → resultado`  
**Contexto estructural:** goal prompt, solver/policy, action functions, reward functions, task evaluators, código generado, resultados y self-modification.  
**Nivel seleccionado:** self-referential adaptive agent runtime.  
**Qué aporta a un agente:** ciclo explícito de evaluación y modificación de política/código para adaptar comportamiento a feedback del entorno, sujeto a guardrails externos.

---

## YAIWES 55 — gpt-researcher ➡️ Investigación profunda multiagente con planificación, recuperación y publicación

**URL raíz / ubicación:** `Core kernel Yaiwes/gpt-researcher/` · código `Core kernel Yaiwes/gpt-researcher/code/`.  
**Handoff:** inventario fresh: componente `58`; Crazy Wall **sin nodo registrado todavía**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/gpt-researcher/code/README.md`; demuestra clase `GPTResearcher`, métodos `conduct_research()` y `write_report()`, y arquitectura planner → execution/crawler agents → publisher.  
**Determinista:** **No — ≈35%** del resultado completo (estimación técnica): pipeline, agregación y llamadas están estructurados, pero preguntas, búsquedas, fuentes disponibles y síntesis LLM pueden variar.  
**¿Es agente?:** **Sí**; deep-research agent con variantes multiagente.  
**Cómo funciona el kernel/core para tomar decisiones:** crea un agente específico desde la query, el planner genera preguntas de investigación, agentes de ejecución/crawler recopilan información por pregunta, cada recurso se resume y conserva su fuente, luego se filtran/agregan los resúmenes y el publisher construye el informe final citado.  
**Microflujo horizontal:** `query → task-specific agent → planner/questions → execution/crawler agents → web/local/MCP retrieval → source tracking + summaries → filter/aggregate → publisher → cited report`  
**Contexto estructural:** query, preguntas, web/local docs, retrievers/MCP, memoria/contexto, fuentes, resúmenes, planner/execution agents, publisher y formatos de reporte.  
**Nivel seleccionado:** deep-research multi-agent pipeline.  
**Qué aporta a un agente:** investigación factual trazable, descomposición de preguntas, recuperación paralela, memoria de fuentes y síntesis final con citas.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 55`  
`RANGO_DOCUMENTAL = 51-55`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 245`  
`PRIMEROS_PENDIENTES_CONSUMIDOS = Flowable | gatekeeper | Git | Godel-Agent | gpt-researcher`  
`SIGUIENTE_ARCHIVO = readme índice componentes 12 .md`  
`SIGUIENTE_SECUENCIA_DOCUMENTAL = 56-60`
