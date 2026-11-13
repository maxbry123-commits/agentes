# README ÍNDICE COMPONENTES 18 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque documental: **YAIWES 86–90** · Inventario físico fresh: **245**.

Continuidad fresh: `readme índice componentes 17 .md` cerró en YAIWES 85 (`JSON-Schema`). El inventario fresh de `main` coloca a continuación, en orden físico real, `k3s`, `Kata-Containers`, `Kestra`, `Kimi-K2.5`, `Kong`. Esto corrige la previsión anterior que había saltado `Kong`. Todo detalle que las fuentes físicas seleccionadas no demuestran se marca `NO VERIFICADO`.

## YAIWES 86 — k3s ➡️ Distribución Kubernetes ligera y lista para producción
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/k3s/` · origen declarado por README/badges: `k3s-io/k3s`.  
**Handoff:** inventario físico `89`; Crazy Wall nodo `171`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/k3s/README.md`. Manifiesto de extracción/provenance específico: **NO VERIFICADO** en esta auditoría.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; el README demuestra orquestación Kubernetes y componentes empaquetados, pero no garantiza determinismo global del clúster.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel de razonamiento agente. K3s empaqueta Kubernetes y componentes de runtime/red/DNS/ingress/storage en una distribución cohesionada; el control plane de Kubernetes reconcilia recursos y estado del clúster. Política/algoritmo interno exacto de scheduling seleccionado para YAIWES: **NO VERIFICADO**.  
**Microflujo horizontal:** `manifiesto/recurso → API/control plane K3s → reconciliación Kubernetes → runtime/containerd → workload → estado observado`.  
**Contexto estructural:** binario único; sqlite3 por defecto con etcd3/MariaDB/MySQL/Postgres soportados; containerd+runc, Flannel, CoreDNS, Metrics Server, Traefik, Klipper-lb, kube-router, Helm controller, Kine y local-path-provisioner.  
**Nivel seleccionado:** lightweight container-orchestration/runtime layer.  
**Qué aporta a un agente:** infraestructura ligera para desplegar, mantener y escalar servicios/agentes contenerizados, especialmente edge/CI/ARM; integración concreta con YAIWES: **NO VERIFICADO**.

## YAIWES 87 — Kata-Containers ➡️ Aislamiento de workloads mediante VMs ligeras con experiencia de contenedor
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Kata-Containers/` · origen demostrado por README: `kata-containers/kata-containers`.  
**Handoff:** inventario físico `90`; Crazy Wall nodo `78`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Kata-Containers/README.md`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la fuente describe runtime, agent e hypervisor, pero no una garantía de determinismo global.  
**¿Es agente?:** No como agente AI; el sistema contiene un componente técnico denominado `agent`, pero no se demuestra que sea un agente autónomo de razonamiento.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel decisor AI: **NO VERIFICADO**. El runtime crea workloads usando VMs ligeras para obtener aislamiento/seguridad de VM manteniendo una experiencia de contenedor; la configuración coordina runtime, agent e hypervisor.  
**Microflujo horizontal:** `solicitud de contenedor → Kata runtime → configuración/hypervisor → VM ligera → Kata agent/runtime → workload aislado`.  
**Contexto estructural:** `src/runtime`, `src/agent`, hypervisors, configuración única, soporte x86_64/aarch64/ppc64le/s390x y comprobación `kata-runtime check`.  
**Nivel seleccionado:** sandbox/isolation runtime layer.  
**Qué aporta a un agente:** aislamiento fuerte de ejecución para herramientas o workloads no confiables, combinando semántica de contenedor con frontera de VM; integración concreta YAIWES: **NO VERIFICADO**.

## YAIWES 88 — Kestra ➡️ Orquestación declarativa event-driven de workflows de datos, AI e infraestructura
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Kestra/` · origen demostrado por README: `kestra-io/kestra`.  
**Handoff:** inventario físico `91`; Crazy Wall nodo `172`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/Kestra/README.md`.  
**Determinista:** **No globalmente demostrado — % NO VERIFICADO**. La definición/orquestación declarativa en YAML es explícita, pero triggers externos, tareas, retries y servicios ejecutados impiden afirmar determinismo global desde esta fuente.  
**¿Es agente?:** No; es plataforma de orquestación.  
**Cómo funciona el kernel/core para tomar decisiones:** la lógica de orquestación queda declarada como código YAML. Triggers programados o por eventos activan workflows; tareas pueden ser secuenciales/paralelas, condicionales o dinámicas, con retries, timeout, error handling, inputs/outputs, variables, subflows y backfills. No se demuestra un kernel autónomo de razonamiento.  
**Microflujo horizontal:** `schedule/event → trigger → workflow YAML → condición/ramificación → tareas secuenciales/paralelas → retry/error handling → outputs/artifacts`.  
**Contexto estructural:** workflows as code, UI/editor, API, Git, plugins, triggers, namespaces, labels, subflows, scheduling y ejecución language-agnostic.  
**Nivel seleccionado:** declarative workflow-orchestration layer.  
**Qué aporta a un agente:** ejecución durable y auditable de procesos AI/infra con control explícito de flujo, paralelismo, fallos y eventos; integración concreta con el kernel YAIWES: **NO VERIFICADO**.

## YAIWES 89 — Kimi-K2.5 ➡️ Modelo multimodal agentic con tool use y ejecución swarm paralela
**URL raíz / ubicación:** `Core kernel Yaiwes/Kimi-K2.5/` · código: `Core kernel Yaiwes/Kimi-K2.5/code/` · origen registrado: `MoonshotAI/Kimi-K2.5`.  
**Handoff:** inventario físico `92`; Crazy Wall nodo `224`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Kimi-K2.5/code/README.md` + `Core kernel Yaiwes/Kimi-K2.5/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=c119f68d1a9a13f88f6a59b8e5e0840983b22689`, 5 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**; es un modelo generativo MoE y la fuente no establece porcentaje de determinismo.  
**¿Es agente?:** Sí en capacidad agentic según README; además soporta un esquema `Agent Swarm` auto-dirigido.  
**Cómo funciona el kernel/core para tomar decisiones:** la fuente demuestra un modelo MoE multimodal con modos instant/thinking, tool use y capacidades agentic. En Agent Swarm descompone tareas complejas en subtareas paralelas y crea dinámicamente agentes especializados por dominio. El algoritmo completo de selección/consenso interno y su integración con YAIWES: **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada texto/visión → K2.5 MoE → razonamiento/modo agentic → descomponer tarea → instanciar agentes especializados → subtareas paralelas/tool use → integrar resultado`.  
**Contexto estructural:** 1T parámetros totales, 32B activados, 384 expertos, 8 expertos seleccionados por token, 256K de contexto, MLA, MoonViT y capacidades multimodales/agentic.  
**Nivel seleccionado:** multimodal reasoning + agent/swarm intelligence layer.  
**Qué aporta a un agente:** razonamiento multimodal, coding con visión, uso autónomo de herramientas y paralelización mediante agentes especializados; acoplamiento exacto a YAIWES: **NO VERIFICADO**.

## YAIWES 90 — Kong ➡️ Gateway API/LLM/MCP con routing, seguridad, balanceo y gobierno de tráfico AI
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Kong/` · origen demostrado por README: `Kong/kong`.  
**Handoff:** inventario físico `93`; Crazy Wall nodo `79`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Kong/README.md`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; routing/configuración puede ser declarativa, pero la fuente no garantiza determinismo global de tráfico, upstreams, LLMs o plugins.  
**¿Es agente?:** No; es gateway/orquestador de tráfico API, LLM y MCP.  
**Cómo funciona el kernel/core para tomar decisiones:** no tiene kernel cognitivo. Aplica configuración de proxy/routing/load balancing/health checks/auth y plugins; para AI ofrece Universal LLM API multi-provider, semantic routing/security/caching y gobierno/seguridad/observabilidad MCP. La política concreta seleccionada para YAIWES: **NO VERIFICADO**.  
**Microflujo horizontal:** `cliente/agente → Kong Gateway → auth/policy/plugin → routing/balanceo/semantic routing → API/LLM/MCP upstream → observabilidad/response`.  
**Contexto estructural:** REST Admin API o configuración declarativa, plugins, API/LLM/MCP Gateway, multi-LLM, MCP governance/security/observability, L4/L7, control plane/data plane e ingress Kubernetes.  
**Nivel seleccionado:** AI/API/MCP gateway and traffic-policy layer.  
**Qué aporta a un agente:** una frontera central para enrutar modelos y herramientas MCP, aplicar autenticación/políticas, balancear tráfico y observar/asegurar llamadas; integración concreta con YAIWES: **NO VERIFICADO**.

---
**COMPONENTES_DOCUMENTADOS = 90**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 91–95**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO = Kubernetes, LangChain, Langfuse, LangGraph, LatentMAS**