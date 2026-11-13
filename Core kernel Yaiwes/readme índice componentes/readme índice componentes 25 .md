# README ÍNDICE COMPONENTES 25 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 121–125** · Inventario fresh: **245**. Continuidad fresh: archivo 24 cerró en YAIWES 120. La lectura fresh del inventario físico corrige la previsión escrita al cierre del archivo 24: entradas físicas **124–128 = Meta-Muse-Glimmer-Agent-2026, Microsoft-Agent-Framework, Microsoft-AutoGen, Microsoft-Presidio y MINIX3**. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 121 — Meta-Muse-Glimmer-Agent-2026 ➡️ cookbook y stack local-first para construir agentes con Muse Glimmer
**URL raíz/ubicación:** `Core kernel Yaiwes/Meta-Muse-Glimmer-Agent-2026/`; fuente upstream declarada por manifiesto: `meta-models/meta-oss-cookbook`.  
**Handoff:** inventario físico `124`; Crazy Wall nodo `232`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Meta-Muse-Glimmer-Agent-2026/code/README.md` + `Meta-Muse-Glimmer-Agent-2026/DOWNLOAD_EXTRACT_MANIFEST.json` + `CORE-KERNEL-COMPONENT-INVENTORY.md`. Manifiesto: `source_commit=499ad7422c2175cf47dbad5df37c4c8f6c11f924`, 40 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO** para la decisión generativa; los contratos/recetas no demuestran un porcentaje global de determinismo.  
**¿Es agente?:** El componente es un cookbook/stack; el README demuestra que permite ejecutar un agente local que planifica, llama herramientas, realimenta resultados y se autocorrige.  
**Cómo funciona el kernel/core para tomar decisiones:** el loop documentado es agentic-first: el modelo recibe contexto, planifica, emite tool calls, incorpora el resultado y se autocorrige durante varios pasos hasta alcanzar el objetivo. El README documenta canal de razonamiento `to=self` y formato de herramientas `<atem:function_calls>`; una política interna más profunda del modelo es **NO VERIFICADO**.  
**Microflujo horizontal:** `objetivo/contexto → Muse Glimmer → plan/razonamiento → tool call → herramienta → resultado → contexto actualizado → autocorrección → siguiente paso/salida`.  
**Contexto estructural:** modelo local-first, 30B dense decoder, contexto 128K, texto+imagen de entrada, texto+tool calling de salida; cookbook con quickstart, fundamentos agentic, recipes, servidores de inferencia, platform y hosted.  
**Nivel seleccionado:** local agentic model + cookbook/runtime integration layer.  
**Qué aporta a un agente:** planificación multi-step, tool use, autocorrección, ejecución local/offline y recetas de integración/serving.

## YAIWES 122 — Microsoft-Agent-Framework ➡️ framework productivo para agentes y workflows multiagente
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Microsoft-Agent-Framework/`; upstream declarado en README: `https://github.com/microsoft/agent-framework`.  
**Handoff:** inventario físico `125`; Crazy Wall nodo `94`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados A/Microsoft-Agent-Framework/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO** como framework completo; el README demuestra workflows/checkpointing pero no un porcentaje global de determinismo.  
**¿Es agente?:** No; es framework para construir y orquestar agentes y sistemas multiagente.  
**Cómo funciona el kernel/core para tomar decisiones:** no impone una única política cognitiva. Compone agentes/proveedores con middleware y workflows en grafo; soporta patrones secuencial, concurrente, handoff y colaboración grupal, además de checkpointing, streaming y human-in-the-loop. La decisión semántica depende del agente/model provider configurado.  
**Microflujo horizontal:** `tarea → agente/provider → middleware → workflow/grafo → agente(s)/tool(s) → checkpoint/HITL → resultado/continuación`.  
**Contexto estructural:** Python y C#/.NET, Go en SDK separado; multi-provider, middleware, workflows, hosting, OpenTelemetry, agentes declarativos YAML y skills.  
**Nivel seleccionado:** production agent orchestration/workflow framework layer.  
**Qué aporta a un agente:** orquestación multiagente, durabilidad, restartability, observabilidad, gobernanza, HITL y flexibilidad de proveedores.

## YAIWES 123 — Microsoft-AutoGen ➡️ framework para aplicaciones de IA multiagente autónomas o con humanos
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Microsoft-AutoGen/Microsoft-AutoGen/`; upstream indicado por el README/documentación: `https://github.com/microsoft/autogen`.  
**Handoff:** inventario físico `126`; Crazy Wall nodo `178`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/Microsoft-AutoGen/Microsoft-AutoGen/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`. El README marca AutoGen en **maintenance mode** y recomienda Microsoft Agent Framework para usuarios nuevos.  
**Determinista:** **No / % NO VERIFICADO**; la ejecución depende de modelos generativos y no se demuestra porcentaje de determinismo.  
**¿Es agente?:** No; es framework que crea aplicaciones/agentes multiagente.  
**Cómo funciona el kernel/core para tomar decisiones:** el ejemplo real crea `AssistantAgent` con un `model_client`; para tools puede conectar un `McpWorkbench`, ejecutar tool iterations y transmitir la ejecución. La política final depende del modelo, agentes y configuración; un kernel cognitivo único es **NO VERIFICADO**.  
**Microflujo horizontal:** `tarea → AssistantAgent → model client → decisión/tool request → MCP/workbench/tool → resultado → iteración → respuesta`.  
**Contexto estructural:** Python 3.10+, AgentChat, extensiones de modelos, AutoGen Studio y soporte MCP; actualmente maintenance mode.  
**Nivel seleccionado:** multi-agent application framework layer (legacy/maintenance).  
**Qué aporta a un agente:** abstracciones de agente, ejecución multiagente, integración de modelos, MCP/tools y streaming.

## YAIWES 124 — Microsoft-Presidio ➡️ protección y desidentificación de PII en texto e imágenes
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Microsoft-Presidio/Microsoft-Presidio/`; README actual referencia el proyecto en `data-privacy-stack/presidio`; procedencia upstream histórica exacta adicional: **NO VERIFICADO** en esta ficha.  
**Handoff:** inventario físico `127`; Crazy Wall nodo `179`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/Microsoft-Presidio/Microsoft-Presidio/README.MD` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO** como sistema completo; combina NER, regex, lógica basada en reglas y checksum, y el README advierte que la detección automática no garantiza encontrar toda información sensible.  
**¿Es agente?:** No; SDK/servicio de identificación y anonimización de PII.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee planner de agente. Evalúa contenido mediante recognizers predefinidos/custom, NER, expresiones regulares, reglas, checksum y contexto; los hallazgos alimentan módulos de anonimización/redacción.  
**Microflujo horizontal:** `texto/imagen → recognizers/NER/regex/reglas/checksum → detecciones PII + contexto → decisión de anonimización configurada → anonimizar/redactar → salida protegida`.  
**Contexto estructural:** Analyzer, Anonymizer, Image-Redactor y Structured; Python/PySpark, Docker/Kubernetes y modelos externos de detección.  
**Nivel seleccionado:** privacy/PII guardrail and de-identification layer.  
**Qué aporta a un agente:** filtro de privacidad para detectar y desidentificar PII antes/después de llamadas a modelos, tools o memoria.

## YAIWES 125 — MINIX3 ➡️ sistema operativo/microkernel y material explícito de kernel
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/MINIX3/MINIX3/`; URL upstream exacta: **NO VERIFICADO** en las fuentes seleccionadas de esta ficha.  
**Handoff:** inventario físico `128`; Crazy Wall nodo `180`, paso `1`, estado `PENDING_STEP1`, destino `None`; inventario lo clasifica `HOLD_KERNEL_MATERIAL — EXPLICIT_KERNEL_COMPONENT`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** árbol físico `Componentes recuperados B/MINIX3/MINIX3/` + `CORE-KERNEL-COMPONENT-INVENTORY.md`; en raíz física se verifican `Makefile`, `build.sh`, `bin/`, `common/`, `crypto/`, `dist/`, `distrib/`, `docs/` y otros árboles. README raíz: **NO VERIFICADO**.  
**Determinista:** **Sí para ejecución de código/reglas del sistema operativo bajo estado/entradas definidos; % NO VERIFICADO**. Un porcentaje empírico no está demostrado.  
**¿Es agente?:** No; es material de sistema operativo/kernel, no agente de IA.  
**Cómo funciona el kernel/core para tomar decisiones:** la política cognitiva de agente no aplica. El inventario demuestra que es material explícito de kernel; detalles arquitectónicos específicos que no estén demostrados por las fuentes seleccionadas quedan **NO VERIFICADO**.  
**Microflujo horizontal:** `evento/entrada de sistema → kernel/servicios del SO → reglas/estado → operación/servicio → resultado`; desglose interno adicional: **NO VERIFICADO**.  
**Contexto estructural:** árbol fuente de sistema operativo con build system, binarios, librerías/árboles comunes, crypto, distribución y documentación; clasificación explícita como material kernel en el inventario YAIWES.  
**Nivel seleccionado:** operating-system/kernel reference-material layer.  
**Qué aporta a un agente:** patrones de aislamiento, servicios de sistema y arquitectura kernel como material de referencia; una integración directa con un agente YAIWES es **NO VERIFICADO**.

---
**COMPONENTES_DOCUMENTADOS = 125**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 126–130**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO FRESH = Mixture-of-Agents, mypy, n8n y siguientes dos componentes físicos del inventario fresh (a verificar antes de escribir el próximo archivo)**