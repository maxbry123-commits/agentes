# 📂 README ÍNDICE COMPONENTES 13 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque documental: **YAIWES 61–65**  
Inventario fresh: **245 componentes** (`CORE-KERNEL-COMPONENT-INVENTORY.md`).

> Continuidad fresh: `readme índice componentes 12 .md` cerró en YAIWES 60 con `GrayMatter`. Los siguientes componentes físicos del inventario son great-expectations, GrowthBook, GTPyhop, Guardrails-AI y Guidance. Todo detalle no demostrado queda como `NO VERIFICADO`.

---

## YAIWES 61 — great-expectations ➡️ Validación y calidad de datos mediante Expectations
**URL raíz / ubicación:** `Core kernel Yaiwes/great-expectations/` · código `Core kernel Yaiwes/great-expectations/code/`.  
**Handoff:** inventario fresh: componente `64`; Crazy Wall: sin nodo registrado todavía.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/great-expectations/code/README.md`; demuestra GX Core, Expectations como tests extensibles de datos, resultados de validación, documentación automática y `gx.get_context()`.  
**Determinista:** **Sí para la evaluación de Expectations configuradas — % NO VERIFICADO**; determinismo global de todas las integraciones: **NO VERIFICADO**.  
**¿Es agente?:** **No**; es un framework/core de calidad de datos.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe contexto y Expectations configuradas, ejecuta validaciones sobre datos y produce resultados; un kernel autónomo que elija objetivos o planes: **NO VERIFICADO**.  
**Microflujo horizontal:** `datos + Data Context → Expectations → validación → resultados → documentación/estado de calidad`  
**Contexto estructural:** Data Context, data sources/integrations, Expectations, validation results y documentación.  
**Nivel seleccionado:** data-quality validation layer.  
**Qué aporta a un agente:** contratos verificables para entradas/salidas de datos y evidencia de validación.

---

## YAIWES 62 — GrowthBook ➡️ Feature flags, experimentación y product analytics
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/GrowthBook/GrowthBook/`.  
**Handoff:** inventario fresh: componente `65`; Crazy Wall nodo `167`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/GrowthBook/GrowthBook/README.md`; demuestra feature flags con targeting/rollouts/experiments, motor estadístico, métricas SQL, analytics, REST API, webhooks y servidor MCP.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; las reglas de flags están estructuradas, pero el README no demuestra determinismo porcentual global y el sistema incluye experimentación/estadística.  
**¿Es agente?:** **No**; plataforma de feature management y experimentación.  
**Cómo funciona el kernel/core para tomar decisiones:** aplica configuración de feature flags, targeting, rollouts y experimentos; el motor estadístico evalúa resultados. Kernel autónomo de planificación: **NO VERIFICADO**.  
**Microflujo horizontal:** `configuración → flag/targeting → rollout o experimento → SDK/usuario → métricas → motor estadístico → resultado`  
**Contexto estructural:** feature flags, targeting, SDKs, experiments, metrics, data sources, analytics, API/webhooks y MCP.  
**Nivel seleccionado:** feature-control/experimentation layer.  
**Qué aporta a un agente:** activación controlada de capacidades, experimentos y medición de resultados sin acoplar la decisión al código principal.

---

## YAIWES 63 — GTPyhop ➡️ Planificación jerárquica Goal-Task-Network con búsqueda y backtracking
**URL raíz / ubicación:** `Core kernel Yaiwes/GTPyhop/` · código `Core kernel Yaiwes/GTPyhop/code/`.  
**Handoff:** inventario fresh: componente `66`; Crazy Wall: sin nodo registrado todavía.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/GTPyhop/code/README.md`; demuestra planificación automática GTN, listas con acciones/tareas/metas, planning domains, task methods, goal methods, backtracking y Run-Lazy-Lookahead.  
**Determinista:** **Sí para una misma definición de dominio/orden de métodos según el algoritmo descrito — % NO VERIFICADO**; garantía porcentual explícita: **NO VERIFICADO**.  
**¿Es agente?:** **No**; es un sistema de planificación automatizada, aunque puede integrarse con acting.  
**Cómo funciona el kernel/core para tomar decisiones:** toma una lista `T` de acciones, tareas y metas; busca hacia atrás en un dominio; selecciona métodos aplicables para descomponer tareas/metas, retrocede cuando una rama falla y construye una secuencia de acciones solución.  
**Microflujo horizontal:** `estado + T → acción/tarea/meta → método aplicable → descomposición → backtracking si falla → secuencia de acciones → plan`  
**Contexto estructural:** state, actions, tasks, goals, task methods, goal methods, planning domains, to-do list y solution plan.  
**Nivel seleccionado:** hierarchical symbolic planner.  
**Qué aporta a un agente:** planificación explícita y auditable que alterna metas y tareas y puede reintentar ramas mediante backtracking.

---

## YAIWES 64 — Guardrails-AI ➡️ Validación y mitigación de riesgos en entradas/salidas de LLM
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Guardrails-AI/`.  
**Handoff:** inventario fresh: componente `67`; Crazy Wall nodo `66`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Guardrails-AI/README.md`; demuestra Input/Output Guards, validators combinables, detección/cuantificación/mitigación de riesgos, structured data y acciones `on_fail`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; validadores concretos pueden aplicar reglas/thresholds, pero el README no demuestra determinismo global de todos los validators.  
**¿Es agente?:** **No**; framework de guardrails/validación para aplicaciones de IA.  
**Cómo funciona el kernel/core para tomar decisiones:** intercepta entrada o salida, ejecuta validators configurados, evalúa sus criterios y aplica la acción `on_fail`; planificación autónoma o selección propia de objetivos: **NO VERIFICADO**.  
**Microflujo horizontal:** `input/output LLM → Guard → validators → pass/fail + riesgo → on_fail/mitigación → salida controlada`  
**Contexto estructural:** Guard, Input/Output Guards, validators, thresholds/configuración, validation result y OnFailAction.  
**Nivel seleccionado:** AI validation/safety control layer.  
**Qué aporta a un agente:** barreras verificables alrededor de llamadas LLM y control de respuestas que incumplen criterios configurados.

---

## YAIWES 65 — Guidance ➡️ Control programático y generación restringida para modelos de lenguaje
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Guidance/Guidance/`.  
**Handoff:** inventario fresh: componente `68`; Crazy Wall nodo `67`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Guidance/Guidance/README.md`; demuestra steering de LLM, generación restringida con regex/CFG, condicionales, loops, tool use, `gen()` y `select()`, además de múltiples backends.  
**Determinista:** **No — % NO VERIFICADO** para generación LLM general; las restricciones sintácticas pueden garantizar forma de salida, pero no equivalen a determinismo semántico.  
**¿Es agente?:** **No**; paradigma/librería de programación para controlar modelos.  
**Cómo funciona el kernel/core para tomar decisiones:** el programa intercala control Python y generación; `gen()` solicita generación bajo restricciones y `select()` limita elecciones a opciones configuradas. Un kernel autónomo que formule objetivos/planes: **NO VERIFICADO**.  
**Microflujo horizontal:** `programa Guidance → contexto/control → gen/select + restricciones → backend LLM → salida válida/capturada → siguiente control`  
**Contexto estructural:** model object inmutable, roles/context managers, `gen`, `select`, regex/CFG, conditionals, loops, tool use y backends.  
**Nivel seleccionado:** constrained-generation/control layer.  
**Qué aporta a un agente:** salidas estructuradas, selección restringida y mezcla explícita de lógica de control con generación LLM.

---

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 65`  
`RANGO_DOCUMENTAL = 61-65`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 245`  
`PRIMEROS_PENDIENTES_CONSUMIDOS = great-expectations | GrowthBook | GTPyhop | Guardrails-AI | Guidance`  
`SIGUIENTE_ARCHIVO = readme índice componentes 14 .md`  
`SIGUIENTE_SECUENCIA_DOCUMENTAL = 66-70`