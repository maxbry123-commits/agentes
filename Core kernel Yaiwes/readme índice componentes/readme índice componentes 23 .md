# README ÍNDICE COMPONENTES 23 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 111–115** · Inventario fresh: **245**. Continuidad fresh: archivo 22 cerró en YAIWES 110. Inventario físico: MCP-Python-SDK, MCP-Servers, MCP-TypeScript-SDK, Mem0 y MemForge (entradas físicas 114–118). Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 111 — MCP-Python-SDK ➡️ SDK Python para servidores y clientes Model Context Protocol
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/MCP-Python-SDK/`; upstream demostrado: `https://github.com/modelcontextprotocol/python-sdk`.  
**Handoff:** inventario físico `114`; Crazy Wall nodo `92`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/MCP-Python-SDK/README.md` + inventario. README declara v2 estable y MCP `2026-07-28`.  
**Determinista:** **Sí para parsing/validación/dispatch protocolario; % NO VERIFICADO**.  
**¿Es agente?:** No; SDK Python MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel cognitivo. Declara tools/resources con funciones tipadas; deriva schema, procesa/valida solicitudes y ejecuta handlers. Selección autónoma de herramienta: **NO VERIFICADO**.  
**Microflujo horizontal:** `función tipada → @mcp.tool/resource → schema MCP → stdio/HTTP/SSE → llamada cliente → validación/dispatch → handler → resultado`.  
**Contexto estructural:** Python 3.10+, servidor/cliente MCP, tools/resources/prompts y transports estándar.  
**Nivel seleccionado:** MCP Python runtime/client-server adapter layer.  
**Qué aporta a un agente:** expone y consume capacidades Python mediante MCP estandarizado.

## YAIWES 112 — MCP-Servers ➡️ implementaciones de referencia de servidores MCP
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/MCP-Servers/`; upstream exacto desde manifiesto: **NO VERIFICADO**.  
**Handoff:** inventario físico `115`; Crazy Wall nodo `176`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/MCP-Servers/README.md` + inventario.  
**Determinista:** **Depende del servidor/capability; % NO VERIFICADO**.  
**¿Es agente?:** No; colección de referencias MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** no hay kernel único; cada servidor expone capacidades controladas y el cliente/LLM decide cuándo invocarlas. README identifica Everything, Fetch, Filesystem, Git, Memory, Sequential Thinking y Time.  
**Microflujo horizontal:** `fuente/capacidad → servidor MCP → tools/resources/prompts → cliente → LLM/app → llamada → resultado`.  
**Contexto estructural:** ejemplos educativos; README advierte que no son production-ready y exige safeguards según threat model.  
**Nivel seleccionado:** reference-capability/server-pattern layer.  
**Qué aporta a un agente:** patrones reales para filesystem, Git, memoria, fetch, tiempo y otras capacidades MCP.

## YAIWES 113 — MCP-TypeScript-SDK ➡️ SDK TypeScript para clientes, servidores y middleware MCP
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/MCP-TypeScript-SDK/`; upstream demostrado: `https://github.com/modelcontextprotocol/typescript-sdk`.  
**Handoff:** inventario físico `116`; Crazy Wall nodo `177`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/MCP-TypeScript-SDK/README.md` + inventario; v2 estable, MCP `2026-07-28`.  
**Determinista:** **Sí para schema/transport/dispatch dada configuración y handler; % NO VERIFICADO**.  
**¿Es agente?:** No; SDK TypeScript MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** no contiene política cognitiva. `McpServer` registra tools con schema; transporte conecta servidor; handler produce respuesta.  
**Microflujo horizontal:** `registerTool + schema → McpServer → stdio/HTTP → client → request validada → handler → result`.  
**Contexto estructural:** paquetes server/client; Node.js/Bun/Deno; middleware Node HTTP, Express, Fastify y Hono.  
**Nivel seleccionado:** MCP TypeScript interoperability/runtime layer.  
**Qué aporta a un agente:** expone/consume tools y contexto MCP con schemas y transports.

## YAIWES 114 — Mem0 ➡️ capa de memoria inteligente y personalizada para asistentes/agentes
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Mem0/`; upstream demostrado: `https://github.com/mem0ai/mem0`.  
**Handoff:** inventario físico `117`; Crazy Wall nodo `93`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Mem0/README.md` + inventario.  
**Determinista:** **No / % NO VERIFICADO**; usa extracción LLM, embeddings y retrieval híbrido.  
**¿Es agente?:** No; memory layer.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra planner general. Documenta extracción ADD-only, entity linking, señales semantic/BM25/entity en paralelo, fusión y temporal reasoning; la memoria recuperada alimenta decisiones del agente.  
**Microflujo horizontal:** `interacción → ADD-only extraction → memoria + entidades → embeddings → semantic + BM25 + entity → fusión temporal → recuerdos → contexto agente`.  
**Contexto estructural:** library/self-hosted/cloud; memoria User, Session y Agent; algoritmo nuevo abril 2026; optimizaciones managed no todas OSS.  
**Nivel seleccionado:** persistent-personalized-memory/retrieval layer.  
**Qué aporta a un agente:** continuidad contextual, preferencias, estado y recuperación híbrida.

## YAIWES 115 — MemForge ➡️ memoria agentic multinivel con consolidación, revisión y reflexión
**URL raíz/ubicación:** `Core kernel Yaiwes/MemForge/`; código `code/`; upstream verificado por manifiesto: `salishforge/memforge`.  
**Handoff:** inventario físico `118`; Crazy Wall nodo `226`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/MemForge/code/README.md` + `DOWNLOAD_EXTRACT_MANIFEST.json` + inventario. `source_commit=16e2f15c5881a38911f64ca81b3dc0b25d6207ec`, 190 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**; usa reflexión/revisión LLM y adaptación autónoma de pesos.  
**¿Es agente?:** No; sistema de memoria para agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** hot→warm→cold; búsqueda híbrida/grafo; ciclo de sueño: scoring → triage → conflict resolution → revision → graph maintenance → temporal chains → reflection → schema detection → meta-reflection → gap analysis. Active Recall alimenta al agente; no sustituye su planner.  
**Microflujo horizontal:** `eventos hot → consolidación warm → scoring/triage → revisión/conflictos → grafo/temporal → reflection → procedural memory/gaps → retrieval/active recall → acción agente → outcome feedback`.  
**Contexto estructural:** TypeScript/Node, PostgreSQL/pgvector/pg_trgm, tiers, hybrid search, graph, sleep cycles, MCP, SDK TS/Python, multi-tenant; README marca Beta y retracta cifras LongMemEval anteriores por bug del scorer.  
**Nivel seleccionado:** adaptive-agent-memory/consolidation/reflection layer.  
**Qué aporta a un agente:** memoria persistente que consolida, revisa, detecta contradicciones, aprende reglas procedurales y recupera contexto antes de actuar.

---
**COMPONENTES_DOCUMENTADOS = 115**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 116–120**  
**SIGUIENTES FÍSICOS = MemOS, MemRL, Mesa, Meta-Agent-Search, MetaGPT**