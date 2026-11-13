# README ÍNDICE COMPONENTES 16 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque: **YAIWES 76–80** · Inventario fresh: **245**.

Continuidad fresh: `readme índice componentes 15 .md` cerró en YAIWES 75 (`Hugging-Face-Skills`). El inventario físico fresh coloca a continuación `Huginn`, `Hypothesis`, `Inngest`, `Inspect-AI`, `Instructor`. Se corrige por evidencia fresh la previsión anterior que mencionaba `Intercode`: ese nombre no corresponde a esta posición del inventario. Todo detalle no demostrado queda como `NO VERIFICADO`.

## YAIWES 76 — Huginn ➡️ Modelo depth-recurrent para razonamiento latente con cómputo recurrente en inferencia
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Huginn/`.  
**Handoff:** inventario `79`; Crazy Wall nodo `72`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Huginn/README.md`; código de modelo declarado en `recpre/model_dynamic.py`, inferencia HF-compatible en `recpre/raven_modeling_minimal.py`, entrenamiento orquestado por `train.py`.  
**Determinista:** **No globalmente — % NO VERIFICADO**; el README muestra inferencia con sampling en al menos un benchmark y no demuestra determinismo global.  
**¿Es agente?:** No; lo demostrado es un modelo/stack de pretraining e inference, no un agente autónomo.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel de agente propio: **NO VERIFICADO**. El mecanismo demostrado es recurrent-depth/latent reasoning, con recurrencia configurable en inferencia; política autónoma de selección de herramientas/acciones: **NO VERIFICADO**.  
**Microflujo horizontal:** `tokens de entrada → modelo depth-recurrent → recurrencia/razonamiento latente → generación → salida`.  
**Contexto estructural:** model_dynamic, model registry, train.py, launch configs, SimpleFabric, inference HF/vLLM, lm-eval, tokenizer/dataset scripts.  
**Nivel seleccionado:** model/reasoning-compute layer.  
**Qué aporta a un agente:** un backend de modelo con cómputo recurrente en test-time; integración concreta como decisor de YAIWES: **NO VERIFICADO**.

## YAIWES 77 — Hypothesis ➡️ Testing basado en propiedades con generación de casos y reducción de fallos
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Hypothesis/`.  
**Handoff:** inventario `80`; Crazy Wall nodo `73`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Hypothesis/README.md`: property-based testing para Python, selección aleatoria de inputs dentro de rangos definidos, búsqueda de edge cases y reducción al caso fallido más simple.  
**Determinista:** **No globalmente — % NO VERIFICADO**; la fuente declara selección aleatoria de inputs.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no tiene kernel de agente demostrado; toma una propiedad/rango, genera inputs de prueba y, ante fallo, busca un ejemplo fallido simple. Algoritmo interno exacto de generación/shrinking: **NO VERIFICADO** en la fuente seleccionada.  
**Microflujo horizontal:** `propiedad + estrategia/rango → generación de inputs → ejecutar test → detectar fallo → simplificar caso fallido → reporte`.  
**Contexto estructural:** Python property-based testing, `@given`, strategies, randomized inputs, edge cases, shrinking/simplificación de fallos.  
**Nivel seleccionado:** verification/property-testing layer.  
**Qué aporta a un agente:** pruebas generativas para descubrir edge cases y producir contraejemplos pequeños durante validación de código o reglas.

## YAIWES 78 — Inngest ➡️ Funciones durables y workflows event-driven con retries, scheduling y flow control
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Inngest/` · código recuperado en `Core kernel Yaiwes/Componentes recuperados A/Inngest/Inngest/`.  
**Handoff:** inventario `81`; Crazy Wall nodo `74`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Inngest/Inngest/README.md`: durable functions, triggers por eventos/Cron/webhooks, flow control con concurrency/throttling/debouncing/rate limiting/prioritization y steps recuperables con retries.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; las reglas de workflow son explícitas, pero la fuente no demuestra determinismo global de ejecución distribuida.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no decide objetivos; recibe trigger, aplica reglas de flow control y coordina steps durables, retries y recuperación.  
**Microflujo horizontal:** `evento/Cron/webhook → trigger → enqueue/flow control → step durable → retry/recuperación → siguiente step → resultado`.  
**Contexto estructural:** durable functions, events, triggers, HTTPS invocation, steps, concurrency, throttling, debouncing, rate limiting, priority, retries, scheduling, self-hosting.  
**Nivel seleccionado:** durable-workflow/orchestration layer.  
**Qué aporta a un agente:** ejecución fiable de tareas largas/event-driven con estado operativo, reintentos y controles de concurrencia sin que el agente implemente su propia cola.

## YAIWES 79 — Inspect-AI ➡️ Framework de evaluaciones para modelos de lenguaje
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Inspect-AI/`.  
**Handoff:** inventario `82`; Crazy Wall nodo `75`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Inspect-AI/README.md`: framework de evaluaciones LLM del UK AI Security Institute, con prompt engineering, tool usage, diálogo multi-turn, model-graded evaluations, extensiones y más de 200 evaluaciones preconstruidas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la fuente no demuestra determinismo global de modelos/evaluadores.  
**¿Es agente?:** No como producto principal demostrado; soporta evaluación de uso de herramientas y escenarios LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel autónomo de decisión: **NO VERIFICADO**; lo demostrado es composición/ejecución de evaluaciones y scoring, no planificación autónoma de objetivos.  
**Microflujo horizontal:** `modelo + evaluación → prompt/diálogo/tool-use → ejecución → scorer/model-grader → resultado de evaluación`.  
**Contexto estructural:** eval framework, prompt engineering, tool usage, multi-turn dialog, model grading, extensiones Python, catálogo de evaluaciones.  
**Nivel seleccionado:** evaluation/assurance layer.  
**Qué aporta a un agente:** evaluación sistemática de comportamiento, herramientas y respuestas para medir capacidades antes de aceptar cambios.

## YAIWES 80 — Instructor ➡️ Salidas LLM estructuradas y validadas con Pydantic
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Instructor/` · código recuperado en `Core kernel Yaiwes/Componentes recuperados A/Instructor/Instructor/`.  
**Handoff:** inventario `83`; Crazy Wall nodo `76`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Instructor/Instructor/README.md`: structured outputs para LLMs, JSON fiable, Pydantic para validación/type safety, `response_model`, manejo de errores/retries y abstracción sobre proveedores. La propia fuente diferencia Instructor de un runtime de agentes.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la validación por esquema es explícita, pero la generación LLM global no se demuestra determinista.  
**¿Es agente?:** No; el README indica usar Instructor para extracción y otro runtime cuando se necesitan agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel autónomo demostrado; recibe esquema/modelo esperado, solicita salida al proveedor LLM, valida con Pydantic y gestiona fallos/retries.  
**Microflujo horizontal:** `texto + response_model → proveedor LLM → salida estructurada → validación Pydantic → retry si falla → objeto tipado`.  
**Contexto estructural:** Pydantic models, provider abstraction, structured JSON, validation, type safety, retries, response_model.  
**Nivel seleccionado:** structured-output/validation adapter layer.  
**Qué aporta a un agente:** contratos tipados para convertir respuestas LLM en datos estructurados verificables antes de alimentar decisiones o herramientas.

---
**COMPONENTES_DOCUMENTADOS = 80**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 81–85**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO = Interlat, ipyhop, ISEK, json-logic-py, JSON-Schema**