# Índice componentes YAIWES — bloque 151–155

Estado fresh en `main`: archivo anterior `readme índice componentes 30 .md` confirma progreso 150/243. Inventario fresh: entradas físicas 152–156 = OpenTelemetry-Collector, OpenTelemetry-Python, OpenThoughts, OpenThoughts-Agent y Ouroboros. Todo dato no demostrado: `NO VERIFICADO`.

## YAIWES 151 — OpenTelemetry-Collector ➡️ recepción, procesamiento y exportación vendor-agnostic de telemetría
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenTelemetry-Collector/`; upstream README: `https://github.com/open-telemetry/opentelemetry-collector`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenTelemetry-Collector/README.md`; inventario entrada 152.
- **Determinista:** **Sí en pipeline configurado; %: NO VERIFICADO**. Telemetría externa extremo-a-extremo: `NO VERIFICADO`.
- **¿Es agente?:** **No como agente IA**; puede desplegarse como agent o collector de telemetría.
- **Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel decisor IA; ejecuta configuración para recibir, procesar y exportar traces, metrics y logs.
- **Microflujo horizontal:** `fuentes → receivers → processors → exporters → backend`.
- **Contexto estructural:** collector unificado + protocolos + configuración + pipelines + traces/metrics/logs.
- **Nivel seleccionado:** **observability / telemetry pipeline**.
- **Qué aporta a un agente:** recogida, transformación y exportación de telemetría; uso decisor directo: `NO VERIFICADO`.

## YAIWES 152 — OpenTelemetry-Python ➡️ API y SDK Python para producir y exportar telemetría
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/OpenTelemetry-Python/`; upstream README: `https://github.com/open-telemetry/opentelemetry-python`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados B/OpenTelemetry-Python/README.md`; inventario entrada 153.
- **Determinista:** **Sí para API/SDK reglados; %: NO VERIFICADO**; extremo-a-extremo: `NO VERIFICADO`.
- **¿Es agente?:** **No**; API/SDK de observabilidad.
- **Cómo funciona el kernel/core para tomar decisiones:** no implementa kernel decisor; `opentelemetry-api` define API/abstracciones/no-op y `opentelemetry-sdk` es implementación de referencia; exporters/propagators conectan otros sistemas.
- **Microflujo horizontal:** `app Python → API → SDK → exporter/propagator → backend`.
- **Contexto estructural:** API + SDK + exporters + propagators; traces/metrics estables y logs en desarrollo según README.
- **Nivel seleccionado:** **application observability SDK**.
- **Qué aporta a un agente:** instrumentación y emisión de telemetría; decisión autónoma: `NO VERIFICADO`.

## YAIWES 153 — OpenThoughts ➡️ curación y generación abierta de datasets/modelos de razonamiento
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenThoughts/`; sitio README `https://open-thoughts.ai`; código indicado `https://github.com/open-thoughts/open-thoughts`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenThoughts/README.md`; inventario entrada 154.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**; README menciona evaluaciones con diferentes seeds.
- **¿Es agente?:** **No**; proyecto/pipeline de datos y modelos de razonamiento.
- **Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel de agente; cura datasets, genera trazas, entrena y evalúa modelos.
- **Microflujo horizontal:** `datos/preguntas → curación → trazas → dataset → entrenamiento → evaluación`.
- **Contexto estructural:** datasets + data generation + training + OpenThinker + Evalchemy.
- **Nivel seleccionado:** **reasoning data / training pipeline**.
- **Qué aporta a un agente:** datos/recetas para capacidades de razonamiento; integración runtime: `NO VERIFICADO`.

## YAIWES 154 — OpenThoughts-Agent ➡️ tooling y recetas de datos para entrenar modelos agentic pequeños
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenThoughts-Agent/`; website README `https://www.openthoughts.ai/`; upstream repo exacto: `NO VERIFICADO`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenThoughts-Agent/README.md`; inventario entrada 155.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No demostrado como runtime único**; proyecto de investigación para tooling/datos de modelos agentic.
- **Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel decisor único; documenta datagen, SFT, Ray/vLLM y helpers cloud.
- **Microflujo horizontal:** `tareas → datagen → trazas/dataset → SFT → modelo agentic → evaluación`.
- **Contexto estructural:** research codebase + datagen + Ray/vLLM + LLaMA-Factory + cloud helpers + trace viewer/leaderboard.
- **Nivel seleccionado:** **agentic-model data/training research stack**.
- **Qué aporta a un agente:** tooling para producir trazas/datos y entrenar modelos agentic; runtime concreto: `NO VERIFICADO`.

## YAIWES 155 — Ouroboros ➡️ transformer recursivo con modulación LoRA condicionada por entrada
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Ouroboros/`; upstream README: `https://github.com/RightNow-AI/ouroboros`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/Ouroboros/README.md`; inventario entrada 156.
- **Determinista:** **No** como modelo/generación extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; arquitectura/modelo experimental.
- **Cómo funciona el kernel/core para tomar decisiones:** no implementa kernel de agente. Controller observa hidden state y genera por paso modulación diagonal sobre bases LoRA SVD; usa gated recurrence y LayerNorm por paso.
- **Microflujo horizontal:** `tokens → Prelude → recurrent block → Controller(state,step) → LoRA+gate+LayerNorm → Coda → LM head`.
- **Contexto estructural:** recursive transformer + CompactController + SVD-LoRA + gated recurrence + per-step LayerNorm.
- **Nivel seleccionado:** **model / recursive reasoning core experimental**.
- **Qué aporta a un agente:** posible motor recurrente condicionado por entrada; integración agentic real: `NO VERIFICADO`.

## Control del bloque
- Progreso acumulado: **155 / 243**.
- Entradas físicas cubiertas: **152–156**.
- Próximo bloque sujeto a lectura fresh: **YAIWES 156–160**, desde entrada física **157**.
