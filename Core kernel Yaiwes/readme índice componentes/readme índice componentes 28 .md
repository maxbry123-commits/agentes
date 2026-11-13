# Índice componentes YAIWES — bloque 136–140

Estado fresh en `main`: inventario 243 componentes; archivo anterior `readme índice componentes 27 .md`. Este bloque documental corresponde a entradas físicas 137–141. Todo dato no demostrado se marca `NO VERIFICADO`.

## YAIWES 136 — OpenAgentd ➡️ workspace coding-first para ejecutar y supervisar un agente local
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenAgentd/`; upstream `https://github.com/lthoangg/openagentd`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenAgentd/code/README.md`, `OpenAgentd/code/DESIGN.md` (presente), `OpenAgentd/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `a05350f3141488268b018824bb04c2fcd3bf8022`, 1496 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No**; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí, runtime/workspace de agente de código local**; ejecuta un agente y expone tool calls, diffs y estado.
- **Cómo funciona el kernel/core para tomar decisiones:** mantiene sesión/workspace local, usa proveedor/modelo configurado, ejecuta el turno y expone herramientas, resultados, cambios, diagnósticos y estado. Política exacta de selección de cada acción: `NO VERIFICADO`.
- **Microflujo horizontal:** `prompt → sesión local → modelo/agente → tool call → workspace → diff/diagnóstico → resultado`.
- **Contexto estructural:** desktop/mobile + backend local + sesiones + repos/worktrees + modelos + herramientas + telemetría.
- **Nivel seleccionado:** **runtime/harness de agente de código**.
- **Qué aporta a un agente:** observabilidad, workspace real, sesiones persistentes, herramientas, diffs, diagnósticos y control local.

## YAIWES 137 — OpenAI-Evals ➡️ framework de evaluación de LLMs y sistemas LLM
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenAI-Evals/`; upstream `https://github.com/openai/evals`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenAI-Evals/README.md`; inventario entrada física 138.
- **Determinista:** **No**; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; es framework de evaluación, aunque contempla flujos de agentes con herramientas.
- **Cómo funciona el kernel/core para tomar decisiones:** no hay kernel decisor de agente demostrado; ejecuta evals registradas/personalizadas y obtiene resultados para comparar modelos/sistemas. Política autónoma: `NO VERIFICADO`.
- **Microflujo horizontal:** `eval → modelo/sistema → ejecución → criterio/evaluador → resultado → comparación`.
- **Contexto estructural:** registry + datos + templates + completion functions + runners/resultados.
- **Nivel seleccionado:** **evaluación/QA**.
- **Qué aporta a un agente:** pruebas de capacidades/regresiones y comparación de modelos/flujos.

## YAIWES 138 — OpenAI-Guardrails ➡️ validación configurable de seguridad y cumplimiento para aplicaciones LLM
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/OpenAI-Guardrails/`; upstream `https://github.com/openai/openai-guardrails-python`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenAI-Guardrails/README.md`; inventario entrada física 139.
- **Determinista:** **No**; **%: NO VERIFICADO**.
- **¿Es agente?:** **No** como paquete base; ofrece integración Agents SDK mediante `GuardrailAgent`.
- **Cómo funciona el kernel/core para tomar decisiones:** envuelve el cliente OpenAI, carga configuración y aplica validación/moderación automática de entrada/salida; una violación puede activar tripwire. Algoritmos concretos dependen del guardrail.
- **Microflujo horizontal:** `input → guardrails entrada → LLM/agente → output → guardrails salida → permitir/tripwire`.
- **Contexto estructural:** wrapper + configuración + validadores/moderación + tripwires + Agents SDK.
- **Nivel seleccionado:** **policy/safety middleware**.
- **Qué aporta a un agente:** límites configurables, validación pre/post y señal explícita de bloqueo.

## YAIWES 139 — OpenAI-Skills ➡️ instrucciones, scripts y recursos reutilizables por agentes
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenAI-Skills/`; upstream histórico `https://github.com/openai/skills`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenAI-Skills/README.md`; inventario entrada física 140. El README marca el repositorio **deprecated** y remite a OpenAI Plugins.
- **Determinista:** **No**; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; son capacidades descubribles por agentes.
- **Cómo funciona el kernel/core para tomar decisiones:** no implementa kernel autónomo demostrado; un agente descubre una skill y consume instrucciones/scripts/recursos. Criterio exacto de selección: `NO VERIFICADO`.
- **Microflujo horizontal:** `tarea → descubrir skill → cargar instrucciones/recursos → ejecutar → resultado`.
- **Contexto estructural:** carpetas de skills + instrucciones + scripts + recursos.
- **Nivel seleccionado:** **capability/skill layer**.
- **Qué aporta a un agente:** capacidades especializadas reutilizables para tareas repetibles.

## YAIWES 140 — OpenClaw ➡️ asistente multicanal con Gateway local, herramientas, skills y plugins
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenClaw/`; upstream `https://github.com/openclaw/openclaw`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenClaw/code/README.md`; `OpenClaw/DOWNLOAD_EXTRACT_MANIFEST.json`: 43030 archivos, extracción verificada, motor1 `VERIFIED_CLOSED`.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**. El README sí describe `deterministic policy`, pero no demuestra generación determinista del agente.
- **¿Es agente?:** **Sí**; el README lo define como asistente AI y usa modelos/harnesses como plugins.
- **Cómo funciona el kernel/core para tomar decisiones:** Gateway controla sesiones, herramientas, eventos y canales; modelos/harnesses son intercambiables y tools/skills/plugins amplían acciones. Algoritmo exacto que decide cada acción: `NO VERIFICADO`.
- **Microflujo horizontal:** `mensaje/canal → Gateway → sesión → modelo/harness → tool/skill/plugin → ejecución → resultado → Gateway → canal/UI`.
- **Contexto estructural:** Gateway + UI/CLI/TUI + canales + apps/nodes + modelos + harnesses + tools + skills + plugins + estado/memoria local.
- **Nivel seleccionado:** **gateway/runtime de asistente-agente**.
- **Qué aporta a un agente:** control plane local, sesiones/estado, multicanal, herramientas/skills/plugins, proveedores intercambiables y separación política/ejecución.

## Control del bloque
- Progreso acumulado: **140 / 243**.
- Entradas físicas cubiertas: **137–141**.
- Se preserva la numeración documental existente; no se renumeran archivos anteriores.
- Próximo bloque, sujeto a lectura fresh: **YAIWES 141–145**, desde entrada física **142 OpenCoconut**.
