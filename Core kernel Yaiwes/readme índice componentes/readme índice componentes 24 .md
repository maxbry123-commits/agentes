# README ÍNDICE COMPONENTES 24 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 116–120** · Inventario fresh: **245**. Continuidad fresh: archivo 23 cerró en YAIWES 115. La lectura fresh del inventario físico corrige la previsión anterior: entradas 119–123 = **MemOS, MemRL, Mesa, Meta-Agent-Cookbook-2026 y Meta-Muse-Code-SDK-2026**. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 116 — MemOS ➡️ sistema operativo de memoria persistente para LLM y agentes
**URL raíz/ubicación:** `Core kernel Yaiwes/MemOS/`; upstream: `https://github.com/MemTensor/MemOS`.  
**Handoff:** inventario físico `119`; Crazy Wall nodo `227`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `MemOS/code/README.md` + `MemOS/DOWNLOAD_EXTRACT_MANIFEST.json` + inventario. `source_commit=de8069428a9247bfa7a3d35f59a9b39fa8f231d2`, 2014 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**.  
**¿Es agente?:** No; Memory Operating System para LLM/agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra planner cognitivo general. Unifica add/retrieve/edit/delete, memoria como grafo y memory cubes, memoria multimodal/tool/persona y MemScheduler; la recuperación contextual alimenta al agente.  
**Microflujo horizontal:** `interacción/traza → ingestión → memoria/cubes/grafo → retrieve contextual → contexto → agente decide/actúa → feedback/corrección → memoria`.  
**Contexto estructural:** Cloud API, self-host y plugins; KB, multimodal, tool memory, personas, multi-cube y feedback.  
**Nivel seleccionado:** persistent-memory operating layer.  
**Qué aporta a un agente:** memoria de largo plazo editable, recuperación contextual y compartición/aislamiento por cubes.

## YAIWES 117 — MemRL ➡️ autoevolución en runtime mediante reinforcement learning sobre memoria episódica
**URL raíz/ubicación:** `Core kernel Yaiwes/MemRL/`; upstream: `https://github.com/MemTensor/MemRL`.  
**Handoff:** inventario físico `120`; Crazy Wall nodo `228`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `MemRL/code/README.md` + `MemRL/DOWNLOAD_EXTRACT_MANIFEST.json` + inventario. `source_commit=c1b322ca43de36ddf64c6712f89d0095bfc35ce0`, 246 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**.  
**¿Es agente?:** No por sí solo; método/capa de aprendizaje para agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** separa razonamiento estable de memoria plástica y usa Two-Phase Retrieval para filtrar ruido e identificar estrategias de alta utilidad mediante feedback ambiental, sin actualizar pesos.  
**Microflujo horizontal:** `tarea → memoria episódica → retrieval fase 1 → filtro fase 2 → estrategia → acción → feedback → utilidad en memoria → siguiente tarea`.  
**Contexto estructural:** paquete Python; runners HLE, BigCodeBench, ALFWorld y Lifelong Agent Bench; LLM + embeddings.  
**Nivel seleccionado:** runtime episodic-RL/adaptive-memory layer.  
**Qué aporta a un agente:** selección de experiencias útiles y mejora continua no paramétrica.

## YAIWES 118 — Mesa ➡️ framework Python para modelado y simulación basada en agentes
**URL raíz/ubicación:** `Core kernel Yaiwes/Mesa/`; upstream: `https://github.com/mesa/mesa`.  
**Handoff:** inventario físico `121`; Crazy Wall nodo `229`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Mesa/code/README.md` + `Mesa/DOWNLOAD_EXTRACT_MANIFEST.json` + inventario. `source_commit=a5dfcd6ad2bb7863a00d8735649d4c3ebaf014f8`, 244 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO** como propiedad general.  
**¿Es agente?:** No; framework de agent-based modeling.  
**Cómo funciona el kernel/core para tomar decisiones:** no impone kernel cognitivo; ofrece agentes, espacios/grids y schedulers, mientras la política/step la define el modelo del usuario.  
**Microflujo horizontal:** `estado → scheduler → agent.step/política → interacción → actualización → análisis/visualización`.  
**Contexto estructural:** Python, componentes modulares, grids/schedulers, visualización browser y análisis.  
**Nivel seleccionado:** multi-agent simulation/modeling layer.  
**Qué aporta a un agente:** entorno para modelar poblaciones, interacciones, scheduling y comportamiento emergente.

## YAIWES 119 — Meta-Agent-Cookbook-2026 ➡️ recetas ejecutables para APIs, loops de agentes, Muse Code y casos end-to-end
**URL raíz/ubicación:** `Core kernel Yaiwes/Meta-Agent-Cookbook-2026/`; upstream: `https://github.com/meta-models/meta-model-cookbook`.  
**Handoff:** inventario físico `122`; Crazy Wall nodo `230`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Meta-Agent-Cookbook-2026/code/README.md` + manifiesto + inventario. `source_commit=fb440d68f9f1eb735faca57092b0729ad6195d96`, 519 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO** como conjunto; incluye generación, aunque documenta structured output y deterministic replay para fixtures Muse Code.  
**¿Es agente?:** No; cookbook de patrones/casos de uso.  
**Cómo funciona el kernel/core para tomar decisiones:** demuestra patrones `perceive → decide → act`, tools, contexto, autoevaluación y multiagente; no existe un único kernel ejecutor del cookbook.  
**Microflujo horizontal:** `entrada/contexto → modelo → decide/tool call → herramienta → resultado → contexto → self-assess/validación → salida/siguiente acción`.  
**Contexto estructural:** API fundamentals, agent patterns, use cases y Muse Code; compatibilidad declarada con OpenAI SDK, Anthropic SDK, OpenCode y Claude Code vía Meta Model API.  
**Nivel seleccionado:** agent-pattern/reference-implementation layer.  
**Qué aporta a un agente:** loops, tools, contexto, edición validada, sandbox, multiagente, goal judge y replay.

## YAIWES 120 — Meta-Muse-Code-SDK-2026 ➡️ SDK TypeScript para controlar sesiones de Muse Code mediante MSP
**URL raíz/ubicación:** `Core kernel Yaiwes/Meta-Muse-Code-SDK-2026/`; upstream: `https://github.com/meta-models/muse-code-sdk`.  
**Handoff:** inventario físico `123`; Crazy Wall nodo `231`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Meta-Muse-Code-SDK-2026/code/README.md` + manifiesto + inventario. `source_commit=fbce769ccb75ab971d00e01a00fe076de4c773fc`, 222 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **Sí para tipos/schema/protocolo y replay de transcripts; % NO VERIFICADO**. Decisión generativa de Muse Code: **NO VERIFICADO** como determinista.  
**¿Es agente?:** No; SDK/cliente para sesiones Muse Code.  
**Cómo funciona el kernel/core para tomar decisiones:** no implementa el kernel cognitivo; expone facade, tipos MSP, protocolo, fixtures y clientes. El host `muse` real no forma parte de este repo, por lo que su política interna es **NO VERIFICADO**.  
**Microflujo horizontal:** `cliente TS → SDK → MSP schema/wire → host muse externo → eventos/respuestas → cliente`; conformance: `transcript → replay → validación`.  
**Contexto estructural:** Node.js 20+, cero runtime dependencies, sdk-ts, msp-ts, quickstart/cookbook, schema MSP y conformance transcripts; Developer Preview.  
**Nivel seleccionado:** agent-session protocol/client SDK layer.  
**Qué aporta a un agente:** integración programática, sesiones auditables, contratos MSP tipados y replay/conformidad.

---
**COMPONENTES_DOCUMENTADOS = 120**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 121–125**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO FRESH = Meta-Muse-Glimmer-Agent-2026, Microsoft-Agent-Framework, Microsoft-AutoGen, Microsoft-Semantic-Kernel, Microsoft-TaskWeaver**