# README ÍNDICE COMPONENTES 21 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque: **YAIWES 101–105** · Inventario fresh: **245**. Continuidad fresh: archivo 20 cerró en YAIWES 100; el inventario físico fresh confirma a continuación LlamaIndex, llm-guard, LM-Evaluation-Harness, LMQL y Luigi. La previsión anterior que incluía LMCache/lmdeploy no coincide con el inventario fresh y queda descartada. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 101 — LlamaIndex ➡️ framework de datos y aplicaciones agentic para LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/LlamaIndex/`; código físico `Core kernel Yaiwes/Componentes recuperados A/LlamaIndex/LlamaIndex/`; upstream visible en README: `run-llama/llama_index`.  
**Handoff:** inventario `104`; Crazy Wall nodo `86`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/LlamaIndex/LlamaIndex/README.md` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json`.  
**Determinista:** **No / % NO VERIFICADO**.  
**¿Es agente?:** No como componente completo; es framework para construir aplicaciones agentic y agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** LlamaIndex core ofrece conectores, índices/grafos, retrieval/query engines e integraciones; el razonamiento/selección final depende del LLM/agente configurado. Política autónoma única del core: **NO VERIFICADO**.  
**Microflujo horizontal:** `datos → conectores → estructura/índice → retrieval/query → contexto → LLM/agente → salida`.  
**Contexto estructural:** `llama-index-core` + más de 300 paquetes de integración; ingestión, índices/grafos, retrieval, query engines, reranking, Workflows/LlamaAgents.  
**Nivel seleccionado:** agentic-data/retrieval-context layer.  
**Qué aporta a un agente:** contexto privado estructurado, recuperación de conocimiento, RAG, conectores e infraestructura para workflows/agentes.

## YAIWES 102 — llm-guard ➡️ toolkit de seguridad para entradas y salidas LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/llm-guard/`; código `Core kernel Yaiwes/llm-guard/code/`; upstream exacto `https://github.com/protectai/llm-guard.git`.  
**Handoff:** inventario `105`; Crazy Wall: nodo/destino **NO VERIFICADO**; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/llm-guard/code/README.md` + `Core kernel Yaiwes/llm-guard/DOWNLOAD_EXTRACT_MANIFEST.json`; `source_commit=168c1034ffdb33837e7ae6fd6a16b80567c1be03`, 320 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No; toolkit/guardrail de seguridad.  
**Cómo funciona el kernel/core para tomar decisiones:** aplica scanners a prompt y output para sanitización/detección: prompt injection, secrets, regex, toxicity, sensitive data, factual consistency y otros; un kernel cognitivo general **NO VERIFICADO**.  
**Microflujo horizontal:** `prompt → input scanners → LLM → output scanners → salida filtrada/validada`.  
**Contexto estructural:** proyecto archivado/no mantenido según README; scanners de prompt y output, integración Python/API.  
**Nivel seleccionado:** LLM-security/input-output-guardrail layer.  
**Qué aporta a un agente:** filtros antes/después del LLM contra inyección, fuga de datos, contenido sensible y otras clases de riesgo.

## YAIWES 103 — LM-Evaluation-Harness ➡️ framework unificado de evaluación reproducible de modelos generativos
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/LM-Evaluation-Harness/`; upstream demostrado en README: `EleutherAI/lm-evaluation-harness`.  
**Handoff:** inventario `106`; Crazy Wall nodo `87`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/LM-Evaluation-Harness/README.md` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel cognitivo; ejecuta tareas/benchmarks configurados sobre backends de modelos y calcula resultados/métricas.  
**Microflujo horizontal:** `modelo/backend + tarea/config → ejecución benchmark → postproceso/extracción → métrica → resultado comparable`.  
**Contexto estructural:** 60+ benchmarks académicos, cientos de subtareas/variantes, backends HF/vLLM/API y tareas configurables YAML.  
**Nivel seleccionado:** model-evaluation/quality-gate layer.  
**Qué aporta a un agente:** evaluación reproducible de modelos candidatos y regresiones antes de seleccionar o desplegar capacidades.

## YAIWES 104 — LMQL ➡️ lenguaje de programación y restricciones para LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/LMQL/`; upstream demostrado en README: `eth-sri/lmql`.  
**Handoff:** inventario `107`; Crazy Wall nodo `174`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/LMQL/README.md` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json`.  
**Determinista:** **No / % NO VERIFICADO**.  
**¿Es agente?:** No; lenguaje/runtime para programar interacción con LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** entrelaza control-flow Python, llamadas LLM, constraints `where`, tipos y algoritmos de decoding; la selección depende del programa/decoder/modelo. Kernel agentic autónomo **NO VERIFICADO**.  
**Microflujo horizontal:** `programa LMQL → control-flow/variables → llamada LLM → constraints/logit masking → decoder → salida válida`.  
**Contexto estructural:** superset de Python, constraints, datatypes, control-flow, speculative execution, caching, APIs sync/async y soporte multimodelo.  
**Nivel seleccionado:** constrained-LLM-programming/decoding layer.  
**Qué aporta a un agente:** control programático de generación, restricciones de salida y decodificación avanzada para reducir respuestas fuera de contrato.

## YAIWES 105 — Luigi ➡️ orquestación de pipelines batch por dependencias
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Luigi/`; upstream demostrado en README: `spotify/luigi`.  
**Handoff:** inventario `108`; Crazy Wall nodo `88`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Luigi/README.rst` + `Core kernel Yaiwes/CORE-KERNEL-COMPONENT-INVENTORY.json`.  
**Determinista:** **Sí en resolución/orquestación declarada de dependencias; % NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** resuelve dependencias entre tareas, administra workflow/fallos y ejecuta el grafo requerido; no demuestra razonamiento cognitivo ni selección autónoma de objetivos.  
**Microflujo horizontal:** `tareas + dependencias → resolución DAG → tareas listas → ejecución batch → outputs/estado → dependientes`.  
**Contexto estructural:** package Python para pipelines batch, dependency resolution, workflow management, visualización, failure handling, CLI y tareas de larga duración.  
**Nivel seleccionado:** deterministic-workflow/dependency-orchestration layer.  
**Qué aporta a un agente:** ejecución ordenada y observable de trabajos dependientes, recuperación operativa y composición de pipelines extensos.

---
**COMPONENTES_DOCUMENTADOS = 105**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 106–110**  
**SIGUIENTES FÍSICOS = mabwiser, Marshmallow, Math-Shepherd, MCP, MCP-Go**