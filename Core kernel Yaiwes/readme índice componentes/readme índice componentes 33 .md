# Índice componentes YAIWES — bloque 161–165

Estado fresh en `main`: archivo 32 confirma 160/243. Inventario fresh SHA `ee2aeeaa7ebbd9a909f194835319725144fd1c5b`: entradas físicas 162–166 = Phoenix, Portkey-AI-Gateway, PostHog, Prefect y PRISM. Todo dato no demostrado: `NO VERIFICADO`.

## YAIWES 161 — Phoenix ➡️ observabilidad, evaluación y troubleshooting de aplicaciones AI
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Phoenix/`; upstream visible en README: `https://github.com/Arize-ai/phoenix`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/Phoenix/README.md`; inventario 162.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No** como plataforma; README documenta **PXI** como agente integrado.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel decisor YAIWES demostrado. Instrumenta con OpenTelemetry/OpenInference, captura trazas, mantiene datasets/experimentos y ejecuta evaluaciones; PXI usa ese contexto para depuración e iteración.
- **Microflujo horizontal:** `app/LLM → instrumentación → traces/datasets → evals/experiments → diagnóstico/PXI → ajuste`.
- **Contexto estructural:** tracing + evaluation + datasets + experiments + prompt management + PXI + Remote MCP.
- **Nivel seleccionado:** **AI observability / evaluation platform**.
- **Qué aporta a un agente:** telemetría, evaluación, experimentación, diagnóstico y acceso MCP a trazas/datasets.

## YAIWES 162 — Portkey-AI-Gateway ➡️ gateway de routing fiable y seguro hacia múltiples modelos AI
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Portkey-AI-Gateway/Portkey-AI-Gateway/`; upstream `https://github.com/Portkey-AI/gateway`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/Portkey-AI-Gateway/Portkey-AI-Gateway/README.md`; inventario 163.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; gateway de infraestructura AI.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel IA demostrado; aplica configuración de proveedor/modelo y políticas de routing, retries, fallbacks, load balancing, conditional routing y guardrails.
- **Microflujo horizontal:** `request → gateway/config → routing/guardrails → provider/model → retry/fallback → response`.
- **Contexto estructural:** API compatible + múltiples proveedores/modelos + routing + resiliencia + guardrails + MCP Gateway.
- **Nivel seleccionado:** **AI gateway / model routing infrastructure**.
- **Qué aporta a un agente:** abstracción de proveedores, failover, balanceo, routing condicional, guardrails y gestión MCP.

## YAIWES 163 — PostHog ➡️ plataforma de producto con analítica, observabilidad y modo self-driving
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/PostHog/PostHog/`; upstream `https://github.com/PostHog/posthog`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/PostHog/PostHog/README.md`; inventario 164.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No** como plataforma; contiene capacidades agentic/self-driving documentadas.
- **Cómo funciona el kernel/core para tomar decisiones:** no se demuestra un kernel único. Captura contexto y señales del producto; self-driving transforma señales en investigación, reportes y pull requests sujetos a revisión humana.
- **Microflujo horizontal:** `eventos/traces/señales → contexto → análisis/self-driving → diagnóstico → reporte/PR → revisión humana`.
- **Contexto estructural:** analytics + replay + flags + experiments + errors/logs + warehouse/pipelines + AI observability + workflows + MCP.
- **Nivel seleccionado:** **product intelligence / agent context platform**.
- **Qué aporta a un agente:** contexto operativo, señales de usuario, trazas AI, experimentos y propuestas de cambio.

## YAIWES 164 — Prefect ➡️ orquestación resiliente de workflows y pipelines Python
- **URL raíz / ubicación:** `Core kernel Yaiwes/Prefect/`; código `Prefect/code/`; upstream `https://github.com/PrefectHQ/prefect`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Prefect/code/README.md` + `Prefect/DOWNLOAD_EXTRACT_MANIFEST.json`; inventario 165. `source_commit=9795fc271ce582dbe94165cdc43a9119bc3828f6`, 5385 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **Sí para scheduling/dependencias/branching dadas las mismas condiciones; %: NO VERIFICADO**.
- **¿Es agente?:** **No**; framework de orquestación.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel IA; flows/tasks declaran trabajo y runtime aplica scheduling, dependencias, caching, retries, branching y automaciones por eventos.
- **Microflujo horizontal:** `flow → tasks/dependencies → scheduler/runtime → execute → retry/cache/branch → tracked state`.
- **Contexto estructural:** Python flows + tasks + scheduler + caching + retries + event automations + monitoring.
- **Nivel seleccionado:** **workflow orchestration runtime**.
- **Qué aporta a un agente:** ejecución durable, retries, dependencias, scheduling y observabilidad de estado.

## YAIWES 165 — PRISM ➡️ recuperación y compresión de memoria estructurada para agentes de horizonte largo
- **URL raíz / ubicación:** `Core kernel Yaiwes/PRISM/`; código `PRISM/code/`; upstream `https://github.com/jingyip-cat/PRISM`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `PRISM/code/README.md` + `PRISM/DOWNLOAD_EXTRACT_MANIFEST.json`; inventario 166. `source_commit=fdc09e6bfe31f9c2852eb830ee07de1d750472f4`, 69 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; framework de memoria retrieval-side para agentes long-horizon.
- **Cómo funciona el kernel/core para tomar decisiones:** cuatro módulos: Hierarchical Bundle Search, Query-Sensitive Edge Costing, Evidence Compression y Adaptive Intent Routing; intenta tiers sin LLM y usa fallback LLM para casos difíciles.
- **Microflujo horizontal:** `query → intent routing → graph search → edge costing → evidence → LLM compression → contexto compacto → answer model`.
- **Contexto estructural:** graph memory + typed paths + query intent + retrieval + evidence compression + adaptive routing.
- **Nivel seleccionado:** **long-horizon agent memory retrieval/compression**.
- **Qué aporta a un agente:** memoria relevante con menor presupuesto de contexto y routing adaptativo del coste.

## Control del bloque
- Progreso acumulado: **165 / 243**.
- Entradas físicas cubiertas: **162–166**.
- Próximo bloque fresh: **YAIWES 166–170**, desde entrada física **167**.
