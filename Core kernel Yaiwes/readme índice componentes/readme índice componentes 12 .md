# 📂 README ÍNDICE COMPONENTES 12 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque documental: **YAIWES 56–60**  
Inventario fresh: **245 componentes** (`CORE-KERNEL-COMPONENT-INVENTORY.md`, generado `2026-09-15T07:24:18.021985+00:00`).

> Continuidad fresh: `readme índice componentes 11 .md` cerró en YAIWES 55 con `gpt-researcher`. Los siguientes componentes físicos del inventario son Grafana, Graph-of-Agents-GoA, Graph-of-Thoughts, Graphiti y GrayMatter. Todo detalle no demostrado queda como `NO VERIFICADO`.

---

## YAIWES 56 — Grafana ➡️ Monitorización, observabilidad, visualización y alertas
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Grafana/`.  
**Handoff:** inventario fresh: componente `59`; Crazy Wall nodo `63`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Grafana/README.md`; demuestra consulta, visualización, alertas, dashboards, métricas/logs y múltiples fuentes. Símbolo interno decisor único: **NO VERIFICADO**.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** **No**; plataforma de monitoring/observability.  
**Cómo funciona el kernel/core para tomar decisiones:** demuestra reglas de alerta evaluadas continuamente sobre métricas/consultas configuradas; kernel autónomo que seleccione objetivos/planes: **NO VERIFICADO**.  
**Microflujo horizontal:** `fuentes → query → métricas/logs → dashboard o regla → evaluación → visualización/notificación`  
**Contexto estructural:** data sources, queries, metrics, logs, dashboards, panels, variables y alert rules.  
**Nivel seleccionado:** observability/alerting layer.  
**Qué aporta a un agente:** telemetría, consultas operacionales, dashboards y alertas.

---

## YAIWES 57 — Graph-of-Agents-GoA ➡️ Selección y orquestación dinámica de múltiples LLM como grafo colaborativo
**URL raíz / ubicación:** `Core kernel Yaiwes/Graph-of-Agents-GoA/` · código `Core kernel Yaiwes/Graph-of-Agents-GoA/code/`.  
**Handoff:** inventario fresh: componente `60`; Crazy Wall nodo `218`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Graph-of-Agents-GoA/code/README.md`; demuestra selección/evaluación/orquestación de modelos especializados, `meta_llm`, `top_k`, threshold, rounds, pooling y endpoints.  
**Determinista:** **No — % exacto NO VERIFICADO**; expone `temperature=0.7` y sampling aunque también `seed`.  
**¿Es agente?:** **Sí, arquitectura multiagente basada en modelos especializados**, según su definición Graph-of-Agents.  
**Cómo funciona el kernel/core para tomar decisiones:** meta-LLM participa en node sampling y graph pooling; selecciona hasta `top_k`, conserva relaciones por threshold, ejecuta message passing y agrega el grafo. Función interna única del ciclo: **NO VERIFICADO**.  
**Microflujo horizontal:** `pregunta → meta-LLM/node sampling → selección top-k → grafo de especialistas → message passing → pooling → respuesta`  
**Contexto estructural:** reference models, endpoints, meta-LLM, graph edges/scores, threshold, top-k, rounds, pooling y outputs.  
**Nivel seleccionado:** multi-LLM dynamic orchestration.  
**Qué aporta a un agente:** selección dinámica de especialistas y colaboración estructurada entre modelos.

---

## YAIWES 58 — Graph-of-Thoughts ➡️ Razonamiento mediante grafos ejecutables de operaciones sobre pensamientos
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Graph-of-Thoughts/`.  
**Handoff:** inventario fresh: componente `61`; Crazy Wall nodo `64`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Graph-of-Thoughts/README.md`; demuestra `GraphOfOperations`, `Generate`, `Score`, `GroundTruth`, `Controller`, LLM engine y `ctrl.run()`.  
**Determinista:** **No — % exacto NO VERIFICADO**; grafo/operaciones estructurados, pero usa LLM y no demuestra tasa porcentual.  
**¿Es agente?:** **NO VERIFICADO**; se define como framework de razonamiento/Graph of Operations.  
**Cómo funciona el kernel/core para tomar decisiones:** se construye Graph of Operations, conecta LLM y `Controller` con prompter/parser/estado; `run()` ejecuta el grafo, pudiendo generar, puntuar y validar pensamientos.  
**Microflujo horizontal:** `problema + estado → GraphOfOperations → Controller + LLM → Generate → Score → GroundTruth/validación → salida`  
**Contexto estructural:** thoughts/state, operations, Controller, language model, prompter, parser y output graph.  
**Nivel seleccionado:** graph-structured reasoning controller.  
**Qué aporta a un agente:** razonamiento no lineal como grafo explícito, extensible y evaluable.

---

## YAIWES 59 — Graphiti ➡️ Memoria temporal mediante grafos de contexto para agentes
**URL raíz / ubicación:** `Core kernel Yaiwes/Graphiti/` · código `Core kernel Yaiwes/Graphiti/code/`.  
**Handoff:** inventario fresh: componente `62`; Crazy Wall nodo `65`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Graphiti/code/README.md`; demuestra temporal context graphs, entidades, facts/relationships con ventanas de validez, episodes/provenance, ontologías, actualizaciones incrementales y recuperación híbrida.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** **No**; framework de contexto/memoria para AI agents.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel planificador autónomo: **NO VERIFICADO**. Integra episodios/datos, mantiene hechos/relaciones temporales con procedencia y recupera contexto por tiempo, significado y relaciones para decisiones externas.  
**Microflujo horizontal:** `interacciones/datos → episodes → entidades + facts → validez temporal + provenance → actualización → hybrid retrieval → contexto`  
**Contexto estructural:** entities, facts, validity windows, episodes, ontology, provenance y retrieval híbrido.  
**Nivel seleccionado:** temporal context/memory graph.  
**Qué aporta a un agente:** memoria estructurada evolutiva con historia temporal y procedencia.

---

## YAIWES 60 — GrayMatter ➡️ Memoria persistente y knowledge graph auto-construido para agentes vía MCP/Go
**URL raíz / ubicación:** `Core kernel Yaiwes/GrayMatter/` · código `Core kernel Yaiwes/GrayMatter/code/`.  
**Handoff:** inventario fresh: componente `63`; Crazy Wall nodo `219`, paso `1`, estado `PENDING_STEP1`, destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/GrayMatter/code/README.md`; demuestra memoria persistente, servidor MCP, biblioteca Go, consolidación, knowledge graph con `--kg`, extracción de entidades/relaciones y edges trazables a fact IDs.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO** para el sistema completo; README menciona `deterministic corpus` para timelapse, no determinismo global.  
**¿Es agente?:** **No**; infraestructura de memoria para agentes/clientes MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel autónomo de planificación: **NO VERIFICADO**. Persiste memoria; en consolidación extrae entidades/relaciones, conserva receipts/fact IDs y devuelve contexto a clientes.  
**Microflujo horizontal:** `sesión → memoria persistente → consolidación → facts → entidades + relaciones → graph + receipts → recuperación → siguiente sesión`  
**Contexto estructural:** memory, facts, consolidation, typed entities, edges, fact-ID receipts, MCP server y Go library.  
**Nivel seleccionado:** persistent agent-memory substrate.  
**Qué aporta a un agente:** continuidad entre sesiones, contexto recuperable y grafo con trazabilidad.

---

## Estado del bloque
`COMPONENTES_DOCUMENTADOS = 60`  
`RANGO_DOCUMENTAL = 56-60`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 245`  
`PRIMEROS_PENDIENTES_CONSUMIDOS = Grafana | Graph-of-Agents-GoA | Graph-of-Thoughts | Graphiti | GrayMatter`  
`SIGUIENTE_ARCHIVO = readme índice componentes 13 .md`  
`SIGUIENTE_SECUENCIA_DOCUMENTAL = 61-65`