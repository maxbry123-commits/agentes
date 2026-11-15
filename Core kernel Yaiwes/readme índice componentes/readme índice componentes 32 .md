# Índice componentes YAIWES — bloque 156–160

Estado fresh en `main`: archivo 31 confirma 155/243. Inventario fresh SHA `74fcfc30f3a585fc72acb134ed423dc663ded335`: entradas físicas 157–161 = Outlines, Oxios, Pact-Python, Pact-Specification y PettingZoo. Todo dato no demostrado: `NO VERIFICADO`.

## YAIWES 156 — Outlines ➡️ generación estructurada para salidas de LLM
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Outlines/`; upstream: `https://github.com/dottxt-ai/outlines`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados A/Outlines/README.md`; inventario 157.
- **Determinista:** **Sí para estructura impuesta; %: NO VERIFICADO**; semántica del LLM: `NO VERIFICADO`.
- **¿Es agente?:** **No**.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel decisor; recibe tipo/esquema y restringe la generación para cumplirlo.
- **Microflujo horizontal:** `prompt + modelo + schema → generación restringida → salida estructurada`.
- **Contexto estructural:** modelos + tipos/Pydantic + schemas/grammars.
- **Nivel seleccionado:** **structured generation**.
- **Qué aporta a un agente:** contratos de salida y menos errores de parsing.

## YAIWES 157 — Oxios ➡️ sistema operativo de agentes con kernel y orquestador intent-first
- **URL raíz / ubicación:** `Core kernel Yaiwes/Oxios/`; código `Oxios/code/`; upstream por manifiesto: `https://github.com/project-oxi/oxios`.
- **Handoff:** `Oxios/code/AGENTS.md` es onboarding operativo; Handoff nominal: `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Oxios/code/AGENTS.md` + `Oxios/DOWNLOAD_EXTRACT_MANIFEST.json`; inventario 158. `source_commit=a200e30c08680c80dd38862bb577d0f2686efc23`, 1561 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí como Agent Operating System/runtime**, no un agente único.
- **Cómo funciona el kernel/core para tomar decisiones:** `oxios-kernel` integra supervisor/scheduler/brain/security/tools; Orchestrator ejecuta Ouroboros `assess → crystallize → execute → review`; AgentRuntime envuelve tool-calling de `oxicode-sdk`; Supervisor gestiona fork/exec/wait/kill.
- **Microflujo horizontal:** `usuario → canal → gateway → kernel → assess → crystallize → execute/tools → review → respuesta`.
- **Contexto estructural:** kernel + Supervisor + Orchestrator + AgentRuntime + Engine + oxibrain + AccessManager + MCP.
- **Nivel seleccionado:** **agent OS / orchestration kernel**.
- **Qué aporta a un agente:** lifecycle, scheduling, tools, seguridad, memoria, MCP y protocolo intent-first.

## YAIWES 158 — Pact-Python ➡️ pruebas consumer-driven de contratos API
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Pact-Python/`; upstream `https://github.com/pact-foundation/pact-python`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados B/Pact-Python/README.md`; inventario 159.
- **Determinista:** **Sí para matching/verificación con contrato y datos dados; %: NO VERIFICADO**.
- **¿Es agente?:** **No**.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel IA; expectativas del consumidor producen contratos que se verifican contra el proveedor.
- **Microflujo horizontal:** `expectation → pact → mock/test → provider verification → pass/fail`.
- **Contexto estructural:** contratos + mocks + provider verification.
- **Nivel seleccionado:** **API contract testing**.
- **Qué aporta a un agente:** validación reproducible de integraciones API.

## YAIWES 159 — Pact-Specification ➡️ reglas de matching consistentes entre implementaciones Pact
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Pact-Specification/`; upstream `https://github.com/pact-foundation/pact-specification`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `Componentes recuperados B/Pact-Specification/README.md`; inventario 160.
- **Determinista:** **Sí para reglas/casos especificados; %: NO VERIFICADO**.
- **¿Es agente?:** **No**.
- **Cómo funciona el kernel/core para tomar decisiones:** reglas de matching y casos benchmark deciden pass/fail; no hay kernel IA.
- **Microflujo horizontal:** `pact JSON + interacción → matching rules → benchmark → pass/fail`.
- **Contexto estructural:** specification + JSON + matching + V1–V4.
- **Nivel seleccionado:** **contract specification / validation**.
- **Qué aporta a un agente:** criterio verificable de compatibilidad API.

## YAIWES 160 — PettingZoo ➡️ entornos estándar para multi-agent reinforcement learning
- **URL raíz / ubicación:** `Core kernel Yaiwes/PettingZoo/`; código `PettingZoo/code/`; upstream por manifiesto `https://github.com/Farama-Foundation/PettingZoo`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `PettingZoo/code/README.md` + `PettingZoo/DOWNLOAD_EXTRACT_MANIFEST.json`; inventario 161. `source_commit=a865c24671b269e4091ee16069901cfa6e88efc5`, 642 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** para policies/entrenamiento; **%: NO VERIFICADO**; API/versionado son reglados.
- **¿Es agente?:** **No**; entorno multiagente.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel decisor; AEC entrega observación/reward/estado al agente y una policy externa elige acción; también existe Parallel API.
- **Microflujo horizontal:** `reset → agente → observation/reward → policy/action → step → siguiente agente`.
- **Contexto estructural:** Python MARL + AEC + Parallel API + entornos.
- **Nivel seleccionado:** **multi-agent RL environment**.
- **Qué aporta a un agente:** entrenamiento/evaluación reproducible de coordinación y competición.

## Control del bloque
- Progreso acumulado: **160 / 243**.
- Entradas físicas cubiertas: **157–161**.
- Próximo bloque fresh: **YAIWES 161–165**, desde entrada física **162**.
