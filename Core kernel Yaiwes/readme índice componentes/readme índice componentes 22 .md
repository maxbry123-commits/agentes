# README ÍNDICE COMPONENTES 22 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 106–110** · Inventario fresh: **245**. Continuidad fresh: archivo 21 cerró en YAIWES 105; el inventario físico fresh confirma a continuación mabwiser, Marshmallow, Math-Shepherd, MCP y MCP-Go. Nota de numeración: en `CORE-KERNEL-COMPONENT-INVENTORY.md` estos corresponden a entradas físicas 109–113 porque la numeración documental previa sigue su propia secuencia. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 106 — mabwiser ➡️ selección adaptativa mediante multi-armed bandits contextuales
**URL raíz/ubicación:** `Core kernel Yaiwes/mabwiser/`; código `Core kernel Yaiwes/mabwiser/code/`; upstream exacto `https://github.com/fidelity/mabwiser.git`.  
**Handoff:** inventario físico `109`; Crazy Wall: sin nodo registrado todavía; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/mabwiser/code/README.md` + `Core kernel Yaiwes/mabwiser/DOWNLOAD_EXTRACT_MANIFEST.json`; `source_commit=b104071351d532aae977955d19b83872a9c1b1e3`, 311 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**; incluye políticas estocásticas como Random, Thompson Sampling y Epsilon Greedy, además de otras políticas.  
**¿Es agente?:** No; biblioteca de investigación para algoritmos multi-armed bandit.  
**Cómo funciona el kernel/core para tomar decisiones:** aprende una política a partir de brazos, decisiones/recompensas y, cuando aplica, contexto; luego `predict` selecciona un brazo según la política configurada. El README demuestra UCB1, Epsilon Greedy, LinGreedy, LinTS, LinUCB, Popularity, Random, Softmax y Thompson Sampling, más políticas de vecindad. No demuestra un kernel agentic general.  
**Microflujo horizontal:** `brazos + historial/recompensas + contexto opcional → política MAB → fit → estimación/selección → predict brazo → nueva recompensa → actualización/reentrenamiento`.  
**Contexto estructural:** biblioteca Python, modelos context-free y contextual paramétricos/no paramétricos, paralelización de entrenamiento/prueba, simulación y ajuste de hiperparámetros.  
**Nivel seleccionado:** adaptive-decision/policy-selection layer.  
**Qué aporta a un agente:** mecanismo explícito para elegir entre acciones/herramientas/estrategias usando recompensa observada y contexto, con políticas de exploración/explotación.

## YAIWES 107 — Marshmallow ➡️ validación, serialización y deserialización estructurada
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Marshmallow/`; upstream demostrado por badges/README: `marshmallow-code/marshmallow`.  
**Handoff:** inventario físico `110`; Crazy Wall nodo `89`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Marshmallow/README.rst` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí para transformación/validación conforme al schema dado; % NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel cognitivo; un `Schema` y sus campos/reglas determinan cómo validar datos, deserializar entrada a objetos de aplicación y serializar objetos a tipos Python primitivos.  
**Microflujo horizontal:** `dato/objeto → Schema + fields → validación → deserialize/load o serialize/dump → estructura Python/JSON-ready`.  
**Contexto estructural:** biblioteca agnóstica de ORM/ODM/framework para convertir datatypes complejos a/desde tipos nativos de Python.  
**Nivel seleccionado:** structured-data/schema-validation layer.  
**Qué aporta a un agente:** contratos de entrada/salida, validación y normalización de payloads antes y después de herramientas, APIs o memoria estructurada.

## YAIWES 108 — Math-Shepherd ➡️ datos y señal de supervisión paso a paso para razonamiento matemático
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Math-Shepherd/`; Project Page y paper están declarados en el README; repositorio upstream exacto: **NO VERIFICADO**.  
**Handoff:** inventario físico `111`; Crazy Wall nodo `90`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Math-Shepherd/README.md` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No; la fuente local es una Dataset Card y referencia modelos/checkpoints.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel de agente. Cada instancia contiene problema + solución paso a paso; la etiqueta automática marca cada paso con `+` si puede conducir a la respuesta correcta y `-` si es malo, usando el token `ки` como posición para predecir el score de paso. El README indica entrenamiento de PRM calculando pérdida sólo en esas posiciones.  
**Microflujo horizontal:** `problema + solución paso a paso → posiciones ки → etiquetas +/- → entrenamiento/evaluación PRM → score por paso → señal para razonamiento`.  
**Contexto estructural:** dataset con campos `input`, `label`, `task`; tareas GSM8K o MATH; checkpoints SFT, PRM y RL enlazados; código interno de PPO step-wise no fue abierto según README.  
**Nivel seleccionado:** reasoning-verification/process-reward layer.  
**Qué aporta a un agente:** señal supervisada para evaluar pasos intermedios de razonamiento matemático y entrenar/usar verificadores de proceso; integración directa como decisor runtime: **NO VERIFICADO**.

## YAIWES 109 — MCP ➡️ especificación y schema estándar para conectar aplicaciones LLM con contexto/capacidades
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/MCP/`; documentación oficial declarada: `modelcontextprotocol.io`; URL upstream Git exacta desde esta fuente: **NO VERIFICADO**.  
**Handoff:** inventario físico `112`; Crazy Wall nodo `175`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/MCP/README.md` + schema declarado `schema/2026-07-28/schema.ts` / `schema/2026-07-28/schema.json` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí para contrato/schema del protocolo; % NO VERIFICADO**.  
**¿Es agente?:** No; especificación/protocolo/schema/documentación.  
**Cómo funciona el kernel/core para tomar decisiones:** MCP no demuestra un kernel cognitivo ni decide qué herramienta debe elegir un LLM; define el contrato/protocolo que separa provisión de contexto/capacidades de la interacción con el modelo. La política de selección del agente: **NO VERIFICADO**.  
**Microflujo horizontal:** `aplicación/host ↔ contrato MCP/schema ↔ proveedor MCP/capacidad → contexto/resultado ↔ aplicación LLM`.  
**Contexto estructural:** repositorio de especificación MCP, protocol schema y documentación oficial; schema fuente en TypeScript y distribución adicional JSON Schema.  
**Nivel seleccionado:** interoperability/context-protocol-contract layer.  
**Qué aporta a un agente:** interfaz estandarizada y tipable para conectar contexto y capacidades externas sin acoplar el kernel a una implementación propietaria.

## YAIWES 110 — MCP-Go ➡️ SDK Go de MCP para exponer herramientas, recursos y prompts
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/MCP-Go/`; upstream demostrado por README/badges/imports: `github.com/mark3labs/mcp-go`.  
**Handoff:** inventario físico `113`; Crazy Wall nodo `91`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/MCP-Go/README.md` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí para dispatch/validación protocolaria dada una petición y handler; % NO VERIFICADO**.  
**¿Es agente?:** No; implementación/SDK Go del protocolo MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** el ejemplo crea un MCP server, declara capacidades, registra una herramienta con schema de argumento y asocia un handler; al recibir la llamada, valida el argumento requerido y ejecuta el handler. No demuestra selección cognitiva autónoma de herramientas: esa decisión pertenece a la aplicación/LLM que consume MCP.  
**Microflujo horizontal:** `definir server → declarar capability/tool + schema → registrar handler → transporte MCP/stdio → CallToolRequest → validar argumentos → handler → CallToolResult`.  
**Contexto estructural:** implementación Go de MCP; conceptos Server, Resources, Tools y Prompts; README declara transports, OAuth metadata y session management, y advierte desarrollo activo con capacidades avanzadas aún en progreso.  
**Nivel seleccionado:** MCP-runtime/tool-server-adapter layer.  
**Qué aporta a un agente:** servidor MCP implementable en Go con menor boilerplate para convertir funciones/datos externos en capacidades consumibles mediante el protocolo.

---
**COMPONENTES_DOCUMENTADOS = 110**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 111–115**  
**SIGUIENTES FÍSICOS = MCP-Python-SDK, MCP-Servers, MCP-TypeScript-SDK, Mem0, MemForge**