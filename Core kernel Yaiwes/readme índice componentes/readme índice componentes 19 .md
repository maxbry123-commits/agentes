# README ÍNDICE COMPONENTES 19 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque documental: **YAIWES 91–95** · Inventario físico fresh: **245**.

Continuidad fresh: `readme índice componentes 18 .md` cerró en YAIWES 90 (`Kong`). El inventario fresh de `main` coloca a continuación, en orden físico real, `Kubernetes`, `LangChain`, `Langfuse`, `LangGraph`, `LatentMAS`. Todo detalle que las fuentes físicas seleccionadas no demuestran se marca `NO VERIFICADO`.

## YAIWES 91 — Kubernetes ➡️ Orquestación de aplicaciones contenerizadas entre múltiples hosts
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Kubernetes/` · origen demostrado por README: `kubernetes/kubernetes`.  
**Handoff:** inventario físico `94`; Crazy Wall nodo `173`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/Kubernetes/README.md`. Manifiesto de extracción/provenance específico: **NO VERIFICADO** en esta auditoría.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la fuente demuestra despliegue, mantenimiento y escalado, pero no garantiza determinismo global del clúster.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel cognitivo de agente demostrado. Kubernetes gestiona aplicaciones contenerizadas mediante mecanismos de despliegue, mantenimiento y escalado; el README indica workloads dinámicamente programados, pero el algoritmo/política exacta de scheduling seleccionada para YAIWES es **NO VERIFICADO**.  
**Microflujo horizontal:** `aplicación contenerizada → recursos Kubernetes → programación/orquestación → hosts → despliegue/mantenimiento/escalado → estado operativo`.  
**Contexto estructural:** sistema open source para múltiples hosts, aplicaciones containerizadas, scheduling dinámico y componentes publicados bajo `k8s.io`.  
**Nivel seleccionado:** container-orchestration/control-plane layer.  
**Qué aporta a un agente:** infraestructura para desplegar, mantener y escalar runtimes y servicios de agentes; integración concreta con YAIWES: **NO VERIFICADO**.

## YAIWES 92 — LangChain ➡️ Framework componible para agentes y aplicaciones impulsadas por LLM
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/LangChain/` · origen demostrado por README: `langchain-ai/langchain`.  
**Handoff:** inventario físico `95`; Crazy Wall nodo `80`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/LangChain/README.md`.  
**Determinista:** **No / % NO VERIFICADO**; compone modelos y herramientas generativas y la fuente no establece porcentaje de determinismo.  
**¿Es agente?:** No por sí mismo; es framework explícitamente destinado a construir agentes y aplicaciones LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** LangChain ofrece interfaces estándar y componentes interoperables para modelos, embeddings, vector stores, herramientas y terceros. La decisión cognitiva depende del modelo/agente configurado; para orquestación avanzada remite a LangGraph. Un kernel decisor autónomo propio de LangChain: **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada → componentes LangChain → modelo/retriever/tool seleccionado → integración externa → respuesta/acción`.  
**Contexto estructural:** abstracciones de alto y bajo nivel, modelos intercambiables, integraciones, Deep Agents, LangGraph y LangSmith dentro del ecosistema.  
**Nivel seleccionado:** agent/LLM composition and integration layer.  
**Qué aporta a un agente:** interfaz uniforme para conectar modelos, herramientas, datos, retrievers y componentes intercambiables; acoplamiento exacto con YAIWES: **NO VERIFICADO**.

## YAIWES 93 — Langfuse ➡️ Observabilidad, evaluación, debugging y gestión de prompts para aplicaciones LLM
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Langfuse/` · origen demostrado por README: `langfuse/langfuse`.  
**Handoff:** inventario físico `96`; Crazy Wall nodo `81`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Langfuse/README.md`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; observabilidad y pipelines de evaluación pueden ser estructurados, pero LLM-as-a-judge y aplicaciones observadas no implican determinismo global.  
**¿Es agente?:** No; es plataforma open source de ingeniería LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** no se demuestra kernel cognitivo. Instrumenta aplicaciones para ingerir traces de llamadas LLM, retrieval, embeddings y acciones de agentes; permite evaluar mediante LLM-as-a-judge, evaluadores de código, feedback, etiquetado y pipelines personalizados, además de gestionar/versionar prompts.  
**Microflujo horizontal:** `app/agente → instrumentación/traces → Langfuse → inspección/evaluación/dataset → feedback/debug → iteración de prompt/configuración`.  
**Contexto estructural:** observabilidad, Prompt Management, Evaluations, Datasets, Playground, API/SDKs y despliegue self-hosted.  
**Nivel seleccionado:** LLMOps observability/evaluation layer.  
**Qué aporta a un agente:** trazabilidad de decisiones/acciones, evaluación reproducible, datasets de prueba, debugging y control de versiones de prompts; integración exacta YAIWES: **NO VERIFICADO**.

## YAIWES 94 — LangGraph ➡️ Orquestación de bajo nivel para agentes stateful y de larga duración
**URL raíz / ubicación:** `Core kernel Yaiwes/LangGraph/` · código: `Core kernel Yaiwes/LangGraph/code/` · origen registrado: `langchain-ai/langgraph`.  
**Handoff:** inventario físico `97`; Crazy Wall nodo `82`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/LangGraph/code/README.md` + `Core kernel Yaiwes/LangGraph/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=e539ac122f4126f6dd850581c1494948cf620e31`, `source_files=673`, extracción y reconstrucción verificadas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; el grafo/control de flujo es explícito, pero los agentes/modelos y efectos externos no permiten afirmar determinismo global desde las fuentes.  
**¿Es agente?:** No por sí solo; es framework de orquestación para construir, gestionar y desplegar agentes stateful.  
**Cómo funciona el kernel/core para tomar decisiones:** proporciona infraestructura de bajo nivel para workflows/agentes stateful: ejecución durable con reanudación, estado persistente, memoria de corto/largo plazo, human-in-the-loop y patrones de branching/subgraphs. La decisión semántica depende de nodos/modelos y lógica configurada; algoritmo cognitivo autónomo propio: **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada/estado → nodo del grafo → transición/branch → persistencia/checkpoint → tool/model/humano → siguiente nodo → estado/resultado`.  
**Contexto estructural:** long-running stateful workflows, durable execution, interrupts humanos, memoria, debugging/tracing y deployment; inspirado por Pregel y Apache Beam.  
**Nivel seleccionado:** stateful agent orchestration/kernel-control layer.  
**Qué aporta a un agente:** control explícito del ciclo de ejecución, persistencia ante fallos, memoria, intervención humana y composición por grafos; integración concreta YAIWES: **NO VERIFICADO**.

## YAIWES 95 — LatentMAS ➡️ Razonamiento multiagente con colaboración en espacio latente
**URL raíz / ubicación:** `Core kernel Yaiwes/LatentMAS/` · código: `Core kernel Yaiwes/LatentMAS/code/` · origen registrado: `Gen-Verse/LatentMAS`.  
**Handoff:** inventario físico `98`; Crazy Wall nodo `225`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/LatentMAS/code/README.md` + `Core kernel Yaiwes/LatentMAS/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=9a9e4d331eb11430bd9e64754c6b252b06d73031`, `source_files=24`, extracción y reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**; usa modelos generativos y la fuente no garantiza determinismo ni porcentaje.  
**¿Es agente?:** Sí como framework/sistema multiagente; coordina múltiples agentes de razonamiento.  
**Cómo funciona el kernel/core para tomar decisiones:** desplaza la colaboración desde texto/token space al espacio latente. Los agentes transmiten pensamientos latentes mediante su working memory; usa alineación latent-space training-free y soporta modelos Hugging Face y opcionalmente vLLM. La política exacta para escoger agentes, terminar razonamiento o fusionar decisiones en YAIWES: **NO VERIFICADO**.  
**Microflujo horizontal:** `problema → agente/modelo → pensamiento latente/working memory → transferencia latente → siguiente agente → razonamiento multi-step → resultado`.  
**Contexto estructural:** framework multi-agent, comunicación latente, working memory, alineación sin entrenamiento, compatibilidad HF/vLLM y extensiones para agentes heterogéneos/recuperación latente.  
**Nivel seleccionado:** latent multi-agent reasoning/collaboration layer.  
**Qué aporta a un agente:** colaboración multiagente con menor tráfico textual/token, transferencia de estados latentes y razonamiento multi-step más eficiente; integración exacta con YAIWES: **NO VERIFICADO**.

---
**COMPONENTES_DOCUMENTADOS = 95**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 96–100**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO = Lean4, Letta, Life-Harness, LiteLLM, LlamaFirewall**