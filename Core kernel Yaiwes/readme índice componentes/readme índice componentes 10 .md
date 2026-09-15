# 📂 README ÍNDICE COMPONENTES 10 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque documental: **YAIWES 46–50**  
Inventario fresh: **245 componentes** (`CORE-KERNEL-COMPONENT-INVENTORY.md`, generado `2026-09-15T06:58:20.584402+00:00`).

> Continuidad fresh: el archivo 9 cerró con EVOLVE-MEM. En el inventario actual, los siguientes cinco componentes físicos son **faiss, Fast-Downward, FastMCP, Firecracker y Flagsmith**. Lo no demostrado por código/README/manifiesto/Handoff se marca `NO VERIFICADO`.

---

## YAIWES 46 — faiss ➡️ Búsqueda de similitud y clustering eficiente sobre vectores densos

**URL raíz / ubicación:** `Core kernel Yaiwes/faiss/` · código `Core kernel Yaiwes/faiss/code/`.  
**Handoff:** inventario fresh: componente 49; Crazy Wall **sin nodo registrado todavía**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/faiss/code/README.md`; define Faiss como librería de similarity search/clustering y explica que el núcleo se organiza alrededor de tipos de índice que almacenan vectores y buscan mediante L2/dot product. Símbolo interno único central: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈98%** para un índice, datos y parámetros fijos (estimación técnica); índices aproximados, entrenamiento y paralelismo pueden introducir variaciones prácticas.  
**¿Es agente?:** **No**; librería de recuperación vectorial.  
**Cómo funciona el kernel/core para tomar decisiones:** representa elementos como vectores, los incorpora a un índice y, ante un vector query, calcula/busca vecinos según distancia L2 o producto punto; la elección de índice define el compromiso entre velocidad, memoria, entrenamiento y precisión.  
**Microflujo horizontal:** `datos → embeddings/vectores → index type → add/train → query vector → L2/dot-product search → top-k vecinos → contexto recuperado`  
**Contexto estructural:** vectores densos, IDs enteros, índices exactos/aproximados, quantization, HNSW/NSG, CPU/GPU y métricas de similitud.  
**Nivel seleccionado:** vector retrieval/indexing substrate.  
**Qué aporta a un agente:** memoria/RAG de baja latencia para recuperar experiencias, documentos o candidatos semánticamente cercanos antes de razonar.

---

## YAIWES 47 — Fast-Downward ➡️ Planificación clásica independiente del dominio

**URL raíz / ubicación:** `Core kernel Yaiwes/Fast-Downward/` · código `Core kernel Yaiwes/Fast-Downward/code/`.  
**Handoff:** inventario fresh: componente 50; Crazy Wall **sin nodo registrado todavía**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Fast-Downward/code/README.md`; declara explícitamente `Fast Downward is a domain-independent classical planning system`. Algoritmo/clase única que centralice toda la búsqueda: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈95%** para problema/configuración/heurística fijos (estimación técnica); portfolios, límites y configuraciones de búsqueda pueden cambiar la ruta o resultado operacional.  
**¿Es agente?:** **No**; planner clásico.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe un problema de planificación formal y usa búsqueda/heurísticas configuradas para seleccionar una secuencia de acciones que alcance la meta; el README demuestra el rol de planner, pero el símbolo interno exacto de decisión no fue demostrado en esta pasada: **NO VERIFICADO**.  
**Microflujo horizontal:** `dominio + problema/estado inicial/meta → traducción/representación → search + heuristic → expansión de estados → goal test → plan de acciones`  
**Contexto estructural:** dominios/problemas de planificación clásica, estados, acciones, metas, heurísticas, búsqueda y experimentos/benchmarks.  
**Nivel seleccionado:** symbolic classical planner.  
**Qué aporta a un agente:** planificación explícita y comprobable para convertir estados/metas formalizados en secuencias de acciones sin delegar toda la planificación al LLM.

---

## YAIWES 48 — FastMCP ➡️ Framework MCP para conectar LLMs con herramientas y datos

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/FastMCP/`.  
**Handoff:** nodo `59` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/FastMCP/README.md`; define FastMCP como framework MCP completo para servers, clients e interactive apps; ejemplo real `FastMCP("Demo")`, decorador `@mcp.tool` y `mcp.run()`.  
**Determinista:** **Sí — ≈97%** en schema/validation/protocol lifecycle para entradas fijas (estimación técnica); herramientas remotas, red y LLM consumidor pueden variar.  
**¿Es agente?:** **No**; framework/protocolo de integración para aplicaciones agentic/LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** registra funciones como tools/resources/prompts, genera schema/validación/documentación y gestiona transporte, autenticación y lifecycle MCP; no decide objetivos por sí mismo, sino que expone capacidades estructuradas al cliente/LLM.  
**Microflujo horizontal:** `función/recurso/prompt → FastMCP registration → schema + validation → MCP server/transport/auth → client/LLM request → tool invocation → result → MCP response`  
**Contexto estructural:** servidores, clientes, tools, resources, prompts, schemas, validación, auth, transport y protocol lifecycle.  
**Nivel seleccionado:** MCP application/integration framework.  
**Qué aporta a un agente:** interfaz estandarizada para descubrir y ejecutar herramientas/datos con contratos tipados y lifecycle gestionado.

---

## YAIWES 49 — Firecracker ➡️ Aislamiento seguro de workloads mediante microVMs KVM

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Firecracker/Firecracker/`.  
**Handoff:** nodo `166` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/Firecracker/Firecracker/README.md`; identifica al VMM como componente principal y confirma uso de Linux KVM para crear/ejecutar microVMs. Símbolo interno único de decisión: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈98%** en configuración/lifecycle de virtualización (estimación técnica); scheduling del host, I/O y workload huésped varían.  
**¿Es agente?:** **No**; VMM/runtime de aislamiento.  
**Cómo funciona el kernel/core para tomar decisiones:** configura una microVM minimalista sobre KVM, limita dispositivos/superficie expuesta y ejecuta el workload aislado; no contiene razonamiento de agente. La clase/función interna única de lifecycle no quedó demostrada: **NO VERIFICADO**.  
**Microflujo horizontal:** `workload/config → Firecracker VMM → KVM → microVM mínima → ejecución aislada → I/O/resultado → teardown/reuse`  
**Contexto estructural:** KVM, VMM, microVMs, recursos virtuales, aislamiento hardware, workloads container/function y host Linux.  
**Nivel seleccionado:** secure sandbox/virtualization substrate.  
**Qué aporta a un agente:** aislamiento fuerte para ejecutar código/herramientas potencialmente no confiables reduciendo attack surface y overhead frente a VMs tradicionales.

---

## YAIWES 50 — Flagsmith ➡️ Feature flags, configuración remota y segmentación de releases

**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Flagsmith/Flagsmith/`.  
**Handoff:** nodo `60` · paso `1` · `PENDING_STEP1` · destino `NO REGISTRADO`.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Flagsmith/Flagsmith/README.md`; documenta feature flags, remote changes, A/B testing, segments y SDKs. Símbolo interno único de evaluación: **NO VERIFICADO**.  
**Determinista:** **Sí — ≈98%** para estado de flags/identidad/segmentos fijos (estimación técnica); cambios remotos y experimentos modifican el estado de evaluación.  
**¿Es agente?:** **No**; plataforma de feature management/configuración.  
**Cómo funciona el kernel/core para tomar decisiones:** una aplicación consulta flags/configuración y la plataforma evalúa si una capacidad está activa para un environment, usuario o segmento; permite modificar esa política sin desplegar código. El símbolo interno exacto que centraliza la evaluación no quedó demostrado: **NO VERIFICADO**.  
**Microflujo horizontal:** `feature/config → environment + identity/segment → flag evaluation → enabled/value → rama de ejecución → telemetría/experimento → actualización remota`  
**Contexto estructural:** flags, environments, identities, segments, remote config, A/B/multivariate tests, SDKs, projects/orgs y roles.  
**Nivel seleccionado:** runtime feature-policy/config control plane.  
**Qué aporta a un agente:** activación gradual y reversible de tools/modelos/workflows, segmentación de capacidades y kill-switches sin redeploy.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 50`  
`RANGO_DOCUMENTAL = 46-50`  
`TOTAL_COMPONENTES_INVENTARIO_FRESH = 245`  
`PRIMEROS_PENDIENTES_CONSUMIDOS = faiss | Fast-Downward | FastMCP | Firecracker | Flagsmith`  
`SIGUIENTE_ARCHIVO = readme índice componentes 11 .md`  
`SIGUIENTE_SECUENCIA_DOCUMENTAL = 51-55`
