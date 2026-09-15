# README ÍNDICE COMPONENTES 20 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque: **YAIWES 96–100** · Inventario fresh: **245**. Continuidad fresh: archivo 19 cerró en YAIWES 95; siguen físicamente Lean4, Letta, Life-Harness, LiteLLM y LlamaFirewall. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 96 — Lean4 ➡️ lenguaje y entorno de demostración formal / theorem proving
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/Lean4/`; URL upstream exacta: **NO VERIFICADO**.  
**Handoff:** inventario `99`; Crazy Wall nodo `83`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/Lean4/README.md`.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel cognitivo autónomo **NO VERIFICADO**; la fuente demuestra Lean 4, theorem proving y programación funcional, no selección autónoma de acciones.  
**Microflujo horizontal:** `definición/teorema → código Lean 4 → comprobación formal → resultado/verificación`.  
**Contexto estructural:** instalación, referencia del lenguaje, tutorial theorem proving, programación funcional y build desde fuente.  
**Nivel seleccionado:** formal-verification/theorem-proving layer.  
**Qué aporta a un agente:** comprobación potencial de propiedades e invariantes; integración YAIWES **NO VERIFICADO**.

## YAIWES 97 — Letta ➡️ agentes stateful con memoria persistente
**URL raíz/ubicación:** `Core kernel Yaiwes/Letta/`; código `Letta/code/`; manifiesto upstream `letta-ai/letta`; README indica código activo en `letta-ai/letta-code`.  
**Handoff:** inventario `100`; Crazy Wall nodo `84`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; adicional **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Letta/code/README.md` + `Letta/DOWNLOAD_EXTRACT_MANIFEST.json`; `source_commit=5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a`, 12 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **No / % NO VERIFICADO**.  
**¿Es agente?:** Sí, framework/runtime de agentes stateful.  
**Cómo funciona el kernel/core para tomar decisiones:** agent harness/runtime + memoria, identidad y conversaciones persistentes; política exacta de modelo/tool/action/terminación **NO VERIFICADO**.  
**Microflujo horizontal:** `entrada → agente stateful → memoria/contexto → runtime/harness → acción/respuesta → memoria persistida`.  
**Contexto estructural:** terminal UI, App Server, canales, Agent SDK, Cloud y memoria persistente.  
**Nivel seleccionado:** stateful-agent memory/runtime layer.  
**Qué aporta a un agente:** memoria, identidad y continuidad entre interacciones; integración YAIWES **NO VERIFICADO**.

## YAIWES 98 — Life-Harness ➡️ adaptación runtime del harness para agentes LLM en entornos deterministas
**URL raíz/ubicación:** `Core kernel Yaiwes/Life-Harness/`; código `Life-Harness/code/`; upstream `Tianshi-Xu/Life-Harness`.  
**Handoff:** inventario `101`; Crazy Wall sin nodo registrado; adicional **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Life-Harness/code/README.md` + `Life-Harness/DOWNLOAD_EXTRACT_MANIFEST.json`; commit `d29aeed80a046e858a5f7c52b8267c41d164ad59`, 3057 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **Sí respecto al entorno objetivo; % NO VERIFICADO**.  
**¿Es agente?:** No; harness adaptativo alrededor del agente.  
**Cómo funciona el kernel/core para tomar decisiones:** aprende intervenciones runtime de fallos observados sin cambiar pesos: h2 Action Realization, h3 Environment Contract, h4 Trajectory Regulation, h5 Procedural Skill; el modelo sigue produciendo la decisión.  
**Microflujo horizontal:** `agente congelado → fallo → evolución harness → capas h2/h3/h4/h5 → nueva ejecución → intervención reutilizable`.  
**Contexto estructural:** training-free; README reporta 7 benchmarks, 18 backbones, 116/126 settings mejorados y 88.5% ganancia relativa media; esto no es porcentaje de determinismo.  
**Nivel seleccionado:** adaptive agent-harness/runtime-control layer.  
**Qué aporta a un agente:** recuperación de fallos, contratos de entorno, regulación de trayectorias y skills sin fine-tuning.

## YAIWES 99 — LiteLLM ➡️ gateway AI unificado para 100+ proveedores LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/LiteLLM/`; código `LiteLLM/code/`; upstream `BerriAI/litellm`.  
**Handoff:** inventario `102`; Crazy Wall nodo `85`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`; adicional **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `LiteLLM/code/README.md` + `LiteLLM/DOWNLOAD_EXTRACT_MANIFEST.json`; commit `30f33a949b8a2bb890a2baee18e2ab7ab015a4f7`, 10707 archivos, extracción verificada.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no demuestra kernel cognitivo; normaliza llamadas OpenAI-format hacia 100+ proveedores. Política exacta de routing YAIWES **NO VERIFICADO**.  
**Microflujo horizontal:** `agente/app → API unificada → LiteLLM SDK/Gateway → proveedor LLM → respuesta normalizada`.  
**Contexto estructural:** gateway open source, Python SDK, proxy centralizado y múltiples proveedores.  
**Nivel seleccionado:** multi-LLM gateway/provider-abstraction layer.  
**Qué aporta a un agente:** desacopla proveedores y unifica acceso multi-LLM; integración concreta YAIWES **NO VERIFICADO**.

## YAIWES 100 — LlamaFirewall ➡️ policy engine multicapa de seguridad para agentes AI
**URL raíz/ubicación:** `Core kernel Yaiwes/LlamaFirewall/`; código `LlamaFirewall/code/`; upstream `meta-llama/PurpleLlama`, subdir `LlamaFirewall`.  
**Handoff:** inventario `103`; Crazy Wall sin nodo registrado; adicional **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `LlamaFirewall/code/README.md` + `LlamaFirewall/DOWNLOAD_EXTRACT_MANIFEST.json`; commit `4be64c3a24442b51c76175e6ec67722cc3f5fe38`, 96 archivos, extracción/reconstrucción verificadas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**.  
**¿Es agente?:** No; framework de guardrails.  
**Cómo funciona el kernel/core para tomar decisiones:** policy engine que orquesta PromptGuard 2, AlignmentCheck, regex/custom scanners y CodeShield en etapas del lifecycle; decide seguridad/mitigación, no razonamiento cognitivo general.  
**Microflujo horizontal:** `input/plan/output/acción → policy engine → scanners → riesgo → mitigar/bloquear o pasar → siguiente etapa`.  
**Contexto estructural:** defensa multicapa, tiempo real, extensible, chat y operaciones agentic multi-step; CodeShield usa Semgrep/regex en 8 lenguajes según README.  
**Nivel seleccionado:** agent-security/guardrail-policy layer.  
**Qué aporta a un agente:** controles de prompt injection, alineación, patrones y seguridad de código; integración YAIWES **NO VERIFICADO**.

---
**COMPONENTES_DOCUMENTADOS = 100**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 101–105**  
**SIGUIENTES FÍSICOS = LlamaIndex, llm-guard, LM-Evaluation-Harness, LMCache, lmdeploy**