# Índice componentes YAIWES — bloque 141–145

Estado fresh en `main`: inventario 243 componentes; archivo anterior `readme índice componentes 28 .md`. Este bloque documental corresponde a entradas físicas 142–146. Todo dato no demostrado se marca `NO VERIFICADO`.

## YAIWES 141 — OpenCoconut ➡️ reproducción archivada del paradigma Chain of Continuous Thought (COCONUT)
- **URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/OpenCoconut/`; upstream del componente `https://github.com/casper-hansen/OpenCoconut`; el README remite al código original de Meta `https://github.com/facebookresearch/coconut`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenCoconut/README.md`, `OpenCoconut/setup.py`; inventario entrada física 142.
- **Determinista:** **No**; **%: NO VERIFICADO**.
- **¿Es agente?:** **No**; es una implementación/reproducción de un paradigma de razonamiento latente para modelos.
- **Cómo funciona el kernel/core para tomar decisiones:** no implementa un kernel decisor de agente demostrado. El README describe generación de pensamientos en espacio latente usando hidden states durante prefilling antes de decodificar la respuesta. Política autónoma de selección de acciones: `NO VERIFICADO`.
- **Microflujo horizontal:** `entrada → prefilling → hidden states/pensamiento latente → decodificación → respuesta`.
- **Contexto estructural:** paquete Python + entrenamiento/inferencia + ejemplos + scripts + datasets de razonamiento.
- **Nivel seleccionado:** **razonamiento/model core experimental**.
- **Qué aporta a un agente:** una técnica de razonamiento latente que podría servir como motor cognitivo; integración concreta en un agente: `NO VERIFICADO`.

## YAIWES 142 — OpenCognit ➡️ sistema operativo de orquestación multiagente con CEO, memoria y ejecución real
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenCognit/`; upstream `https://github.com/OpenCognit/opencognit`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenCognit/code/README.md`; `OpenCognit/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `e6dba4255dc79992044df10e324d9e0743055008`, 558 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí, sistema/orquestador multiagente**; el README lo define como AI agent orchestration OS.
- **Cómo funciona el kernel/core para tomar decisiones:** el CEO Agent recibe el objetivo, lo descompone, asigna tareas a especialistas, usa un Critic loop para revisar resultados y escala bloqueos; Task DAG resuelve dependencias y desbloquea tareas downstream. MemPalace, memoria semántica y documentos SOUL mantienen contexto persistente. Algoritmo exacto del LLM para cada decisión: `NO VERIFICADO`.
- **Microflujo horizontal:** `objetivo → CEO → descomposición/DAG → agentes especialistas → ejecución → Critic → memoria → aceptar/revisar/escalar`.
- **Contexto estructural:** CEO orchestrator + agentes especializados + Task DAG + Critic loop + memoria persistente + presupuestos atómicos + CLI executor + MCP + plugins + War Room.
- **Nivel seleccionado:** **agent OS / orchestration kernel**.
- **Qué aporta a un agente:** delegación jerárquica, memoria persistente, revisión automática, dependencias, límites presupuestarios, ejecución y observabilidad.

## YAIWES 143 — openevolve ➡️ agente evolutivo autónomo para optimización y descubrimiento de código
- **URL raíz / ubicación:** `Core kernel Yaiwes/openevolve/`; upstream `https://github.com/algorithmicsuperintelligence/openevolve`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `openevolve/code/README.md`; `openevolve/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `411fb59c886c18704caaffb611e17cf9e7d824d2`, 486 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **Sí según README para reproducibilidad**; **%: NO VERIFICADO**. El README declara reproducibilidad totalmente determinista, pero no se asigna porcentaje sin medición reproducible local.
- **¿Es agente?:** **Sí**; el README lo denomina explícitamente evolutionary coding agent.
- **Cómo funciona el kernel/core para tomar decisiones:** usa LLMs para proponer variantes de código, evaluación para puntuar candidatos y evolución/selección para continuar la búsqueda; soporta optimización multiobjetivo/Pareto y evolución paralela por islas. Los detalles exactos de cada política de selección requieren código/configuración específica y no se generalizan aquí.
- **Microflujo horizontal:** `programa inicial → LLM genera variante → evaluator → fitness/objetivos → selección/evolución → nueva población → iteración → mejor programa`.
- **Contexto estructural:** runner evolutivo + LLM provider + programa candidato + evaluator + configuración + población/islas + objetivos + historial/resultados.
- **Nivel seleccionado:** **evolutionary coding agent / optimization kernel**.
- **Qué aporta a un agente:** búsqueda autónoma de soluciones, evaluación cerrada, selección iterativa, optimización multiobjetivo y reproducibilidad declarada.

## YAIWES 144 — OpenFang ➡️ Agent OS autónomo con runtime, Hands, skills y guardrails
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenFang/`; upstream `https://github.com/RightNow-AI/openfang`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenFang/code/README.md`; `OpenFang/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `acf2587e46be174c10200489c9a2d23a39a98aeb`, 538 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** extremo-a-extremo; **%: NO VERIFICADO**.
- **¿Es agente?:** **Sí, Agent Operating System para agentes autónomos**.
- **Cómo funciona el kernel/core para tomar decisiones:** el runtime activa agentes/Hands autónomos; cada Hand empaqueta `HAND.toml`, system prompt operativo, `SKILL.md` y guardrails. Los Hands pueden ejecutarse por horario, mantener estado y usar herramientas; acciones sensibles pueden pasar por approval gates. El criterio LLM exacto para cada decisión: `NO VERIFICADO`.
- **Microflujo horizontal:** `schedule/objetivo → Hand manifest + prompt + skill → agente → tools/pipeline → guardrail/approval → acción → estado/reporte`.
- **Contexto estructural:** binario Rust + Agent OS + Hands + manifests + prompts + skills + tools + schedules + guardrails + dashboard + estado.
- **Nivel seleccionado:** **agent OS / autonomous runtime**.
- **Qué aporta a un agente:** ejecución autónoma programada, paquetes de capacidad autocontenidos, skills, herramientas, estado y gates de aprobación.

## YAIWES 145 — OpenGuardrails ➡️ protocolo vendor-neutral de seguridad y política para tráfico de agentes
- **URL raíz / ubicación:** `Core kernel Yaiwes/OpenGuardrails/`; upstream `https://github.com/openguardrails/openguardrails`.
- **Handoff:** `NO VERIFICADO`.
- **Fuente seleccionada exacta:** `OpenGuardrails/code/README.md`; `OpenGuardrails/DOWNLOAD_EXTRACT_MANIFEST.json`: commit `a982f7c84ca567043b21697f0c634c659ef3aeba`, 304 archivos, extracción/reconstrucción verificadas.
- **Determinista:** **No** como sistema completo; **%: NO VERIFICADO**. El contrato/composición puede ser reglado, pero detectores pueden usar modelos/clasificadores.
- **¿Es agente?:** **No**; es protocolo/especificación e integraciones de seguridad para agentes y LLMs.
- **Cómo funciona el kernel/core para tomar decisiones:** OGR define eventos `GuardEvent`, verdicts, composición y taxonomía. La integración intercepta eventos en los límites del loop —request antes del modelo y response antes de que el agente actúe— y obtiene un veredicto mientras todavía puede rechazar la operación. Los detectores pueden ser reglas de configuración o modelo/clasificador.
- **Microflujo horizontal:** `evento request → OGR → detector/composición → verdict → modelo/agente → evento response → OGR → verdict → permitir/bloquear`.
- **Contexto estructural:** modelo L6 Session → L5 Turn → L4 Step → L3 Event → L2 Call → L1 Exec; contrato wire + identidad + payload + detector plugins + integraciones + benchmark.
- **Nivel seleccionado:** **policy/safety protocol layer**.
- **Qué aporta a un agente:** interfaz uniforme para políticas, veredictos pre/post modelo, composición de detectores, identidad/contexto de ejecución y punto de bloqueo antes de acciones.

## Control del bloque
- Progreso acumulado: **145 / 243**.
- Entradas físicas cubiertas: **142–146**.
- Se preserva la numeración documental existente; no se renumeran archivos anteriores.
- Próximo bloque, sujeto a lectura fresh: **YAIWES 146–150**, desde entrada física **147 OpenHands**.
