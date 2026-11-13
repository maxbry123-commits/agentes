# Índice componentes YAIWES — bloque 146–150

Estado fresh en `main`: inventario 243 componentes; archivo anterior `readme índice componentes 29 .md`. Este bloque documental corresponde a entradas físicas 147–151. Todo dato no demostrado se marca `NO VERIFICADO`.

## YAIWES 146 — OpenHands ➡️ control center autoalojado para agentes de programación y automatizaciones
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenHands/`; upstream indicado por README: `https://github.com/OpenHands/OpenHands`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenHands/README.md`; inventario entrada física 147.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí como plataforma que ejecuta agentes**; incluye OpenHands y admite agentes ACP de terceros.
- **Cómo funciona el kernel/core para tomar decisiones:** Agent Canvas inicia conversaciones y automatizaciones, conecta backends locales/remotos/cloud y ejecuta OpenHands u otros agentes ACP. La política concreta de decisión depende del backend/modelo; algoritmo decisor uniforme de Agent Canvas: `NO VERIFICADO`.
- **Microflujo horizontal:** `usuario/webhook/schedule → Agent Canvas → backend/agente → LLM/tools → ejecución → integración/salida`.
- **Contexto estructural:** control center + agent server/backend + automatizaciones + múltiples backends + ACP + integraciones + perfiles LLM.
- **Nivel seleccionado:** **agent control plane / coding-agent runtime**.
- **Qué aporta a un agente:** operación persistente, selección de backend, automatizaciones e integración con servicios.

## YAIWES 147 — OpenLLMetry ➡️ observabilidad OpenTelemetry para aplicaciones LLM
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenLLMetry/`; upstream `https://github.com/traceloop/openllmetry`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenLLMetry/README.md`; inventario entrada física 148.
- **Determinista:** **Sí para instrumentación reglada; %: NO VERIFICADO**. Sistema LLM observado: **No / NO VERIFICADO**.
- **¿Es agente?:** **No**; es instrumentación/observabilidad.
- **Cómo funciona el kernel/core para tomar decisiones:** no implementa kernel decisor; instrumenta proveedores LLM/vector DB sobre OpenTelemetry y exporta telemetría.
- **Microflujo horizontal:** `app LLM → OpenLLMetry → spans OpenTelemetry → exporter → observabilidad`.
- **Contexto estructural:** SDK + instrumentaciones + convenciones semánticas + exporters/integraciones.
- **Nivel seleccionado:** **observability/telemetry layer**.
- **Qué aporta a un agente:** trazabilidad de llamadas LLM y componentes asociados; uso decisor: `NO VERIFICADO`.

## YAIWES 148 — OpenMythos ➡️ Recurrent-Depth Transformer teórico para razonamiento de profundidad variable
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenMythos/`; upstream exacto: `NO VERIFICADO`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenMythos/README.md`; inventario entrada física 149.
- **Determinista:** **No** como generación; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; es arquitectura de modelo.
- **Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel de agente. Usa Prelude, Recurrent Block hasta `max_loop_iters` y Coda; atención MLA/GQA y sparse MoE. Política autónoma de acciones: `NO VERIFICADO`.
- **Microflujo horizontal:** `tokens → Prelude → Recurrent Block × N → MoE/attention → Coda → logits/generación`.
- **Contexto estructural:** PyTorch + RDT + bloques recurrentes + MLA/GQA + sparse MoE.
- **Nivel seleccionado:** **model/reasoning core experimental**.
- **Qué aporta a un agente:** posible motor de razonamiento de profundidad variable; integración real: `NO VERIFICADO`.

## YAIWES 149 — OpenR ➡️ framework para razonamiento avanzado, búsqueda y entrenamiento con LLMs
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenR/`; upstream `https://github.com/openreasoner/openr`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/OpenR/README.md`; inventario entrada física 150.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **No demostrado**; es framework de razonamiento/entrenamiento/búsqueda.
- **Cómo funciona el kernel/core para tomar decisiones:** ofrece supervisión de proceso, policy/PRM training y búsqueda Greedy, Best-of-N, Beam, MCTS, rStar y Critic-MCTS. Política única de kernel: `NO VERIFICADO`.
- **Microflujo horizontal:** `problema → candidatos → búsqueda → evaluación/PRM → selección/expansión → respuesta/training signal`.
- **Contexto estructural:** reasoning framework + data generation + policy training + PRM + search strategies.
- **Nivel seleccionado:** **reasoning/search framework**.
- **Qué aporta a un agente:** búsqueda explícita, evaluación de pasos y mecanismos de selección para mejorar razonamiento.

## YAIWES 150 — OpenSwarm ➡️ orquestador local para coordinar múltiples agentes en paralelo
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenSwarm/`; upstream `https://github.com/openswarm-ai/openswarm`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenSwarm/code/README.md`; `OpenSwarm/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `14120a43f7e43cbe5a1263fe379b8dfe0a195fb0`, 2024 archivos, extracción/reconstrucción verificadas; inventario entrada física 151.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí como sistema/orquestador multiagente**.
- **Cómo funciona el kernel/core para tomar decisiones:** Agent Manager coordina agentes aislados por git worktree/branch; tool-use pasa por permisos HITL `always allow / ask / deny`; soporta modos con prompts/restricciones, MCP y sesiones persistentes. Algoritmo LLM de cada agente: `NO VERIFICADO`.
- **Microflujo horizontal:** `tarea → Agent Manager → agente/worktree → LLM/tools/MCP → permiso → allow/ask/deny → ejecución → diff/estado`.
- **Contexto estructural:** Electron + React/TypeScript + FastAPI + WebSocket + Agent Manager + claude-agent-sdk + MCP + JSON storage + worktrees.
- **Nivel seleccionado:** **multi-agent orchestration/control plane**.
- **Qué aporta a un agente:** paralelismo aislado, coordinación, approvals HITL, MCP, modos, persistencia y observación de cambios.

## Control del bloque
- Progreso acumulado: **150 / 243**.
- Entradas físicas cubiertas: **147–151**.
- Próximo bloque sujeto a lectura fresh: **YAIWES 151–155**, desde entrada física **152 OpenTelemetry-Collector**.
