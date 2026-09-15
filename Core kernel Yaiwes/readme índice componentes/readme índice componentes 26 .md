# README ÍNDICE COMPONENTES 26 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Bloque documental: **YAIWES 126–130** · Inventario fresh: **245**. Continuidad fresh: archivo 25 cerró en YAIWES 125. Entradas físicas **129–133 = Mixture-of-Agents, mypy, n8n, nats-server y NeMo-Guardrails**. Lo no demostrado se marca `NO VERIFICADO`.

## YAIWES 126 — Mixture-of-Agents ➡️ agregación por capas de múltiples LLM/agentes
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/Mixture-of-Agents/Mixture-of-Agents/`; upstream exacto: **NO VERIFICADO** en las fuentes seleccionadas.  
**Handoff:** inventario físico `129`; Crazy Wall nodo `181`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/Mixture-of-Agents/Mixture-of-Agents/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO**; usa múltiples LLM y temperatura configurable.  
**¿Es agente?:** Es una arquitectura de múltiples agentes/modelos LLM; no un agente único.  
**Cómo funciona el kernel/core para tomar decisiones:** organiza varios LLM como agentes de referencia por capas; sus respuestas alimentan capas posteriores y un modelo agregador produce/refina la respuesta final. La política cognitiva interna de cada LLM es **NO VERIFICADO**.  
**Microflujo horizontal:** `instrucción → modelos/agentes de referencia en paralelo → respuestas → siguiente capa/refinamiento → agregador → respuesta final`.  
**Contexto estructural:** README demuestra ejemplo de 2 capas/4 LLM y ejemplo avanzado de 3+ capas; CLI multi-turn mantiene contexto y permite configurar agregador, modelos, temperatura y rondas.  
**Nivel seleccionado:** multi-model ensemble / agent aggregation layer.  
**Qué aporta a un agente:** diversidad de razonamiento, agregación de respuestas y refinamiento multicapa.

## YAIWES 127 — mypy ➡️ verificación estática de tipos para Python
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/mypy/`; upstream indicado por badges/issues del README: `python/mypy`.  
**Handoff:** inventario físico `130`; Crazy Wall nodo `182`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/mypy/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **Sí / % NO VERIFICADO** para análisis estático dado código/configuración/versiones iguales; porcentaje empírico no demostrado.  
**¿Es agente?:** No; es un static type checker.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee planner cognitivo; analiza type hints y uso de variables/funciones y emite advertencias cuando los tipos se usan incorrectamente.  
**Microflujo horizontal:** `código Python + type hints → análisis estático mypy → reglas/sistema de tipos → diagnósticos → corrección/gate`.  
**Contexto estructural:** checker de tipado estático para Python basado en anotaciones compatibles con PEP 484.  
**Nivel seleccionado:** code-quality / static-analysis layer.  
**Qué aporta a un agente:** gate determinista para validar código Python generado antes de ejecutar o integrar cambios.

## YAIWES 128 — n8n ➡️ plataforma visual/código para agentes de IA y automatización de workflows
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados B/n8n/n8n/`; upstream declarado por enlaces del README: `n8n-io/n8n`.  
**Handoff:** inventario físico `131`; Crazy Wall nodo `183`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados B/n8n/n8n/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO** como plataforma completa: los workflows pueden contener lógica fija pero los agentes/modelos generativos no garantizan determinismo.  
**¿Es agente?:** No como producto completo; es plataforma para construir y desplegar agentes y workflows.  
**Cómo funciona el kernel/core para tomar decisiones:** el workflow conecta nodos, lógica, modelos, herramientas y aprobaciones humanas; la decisión semántica del agente depende del modelo/configuración, mientras el grafo de workflow gobierna secuencia y conexiones.  
**Microflujo horizontal:** `trigger/dato → workflow/nodos → lógica/modelo → tool/integración → aprobación humana opcional → siguiente nodo → salida/observabilidad`.  
**Contexto estructural:** canvas visual + JavaScript/Python/npm, self-host/cloud, 1500+ integraciones, workflows multi-step, tool use, human approvals y observabilidad.  
**Nivel seleccionado:** agent/workflow automation and integration layer.  
**Qué aporta a un agente:** orquestación visual, herramientas, integraciones, HITL, despliegue y observabilidad.

## YAIWES 129 — nats-server ➡️ sistema de mensajería para sistemas, servicios y dispositivos distribuidos
**URL raíz/ubicación:** `Core kernel Yaiwes/nats-server/`; upstream verificado por manifiesto: `https://github.com/nats-io/nats-server.git`.  
**Handoff:** inventario físico `132`; Crazy Wall: sin nodo registrado todavía; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `nats-server/code/README.md` + `nats-server/DOWNLOAD_EXTRACT_MANIFEST.json` + `CORE-KERNEL-COMPONENT-INVENTORY.md`. Manifiesto: `source_commit=973e238eaed7de34b6b5fa36935a1cd39a0385a9`, 598 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **Sí para routing/protocolo configurado / % NO VERIFICADO**; comportamiento temporal distribuido global no se cuantifica.  
**¿Es agente?:** No; es infraestructura de comunicaciones/mensajería.  
**Cómo funciona el kernel/core para tomar decisiones:** no toma decisiones cognitivas; recibe/publica/enruta mensajes según protocolo, configuración y estado del sistema. Política interna detallada de routing no demostrada por las fuentes seleccionadas: **NO VERIFICADO**.  
**Microflujo horizontal:** `productor/servicio → NATS server → protocolo/routing/configuración → suscriptor/servicio → procesamiento`.  
**Contexto estructural:** servidor NATS desplegable on-premise, cloud, edge y dispositivos; más de 40 implementaciones cliente según README.  
**Nivel seleccionado:** distributed messaging / event transport layer.  
**Qué aporta a un agente:** bus de eventos/mensajes para desacoplar agentes, tools y servicios distribuidos.

## YAIWES 130 — NeMo-Guardrails ➡️ guardrails programables para aplicaciones conversacionales basadas en LLM
**URL raíz/ubicación:** `Core kernel Yaiwes/Componentes recuperados A/NeMo-Guardrails/`; upstream demostrado por README/badges: `NVIDIA-NeMo/Guardrails`.  
**Handoff:** inventario físico `133`; Crazy Wall nodo `95`, paso `1`, estado `PENDING_STEP1`, destino `None`; handoff independiente: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Componentes recuperados A/NeMo-Guardrails/README.md` + `CORE-KERNEL-COMPONENT-INVENTORY.md`.  
**Determinista:** **No / % NO VERIFICADO** como sistema completo; rails programables controlan comportamiento pero la aplicación subyacente usa LLM.  
**¿Es agente?:** No; es toolkit/capa de guardrails para aplicaciones LLM.  
**Cómo funciona el kernel/core para tomar decisiones:** inserta guardrails programables entre aplicación y LLM para controlar salidas, temas, estilo, rutas conversacionales, extracción estructurada y acceso seguro a tools; no sustituye el planner/modelo cognitivo.  
**Microflujo horizontal:** `entrada → aplicación → guardrails/rails → LLM/tool permitido → guardrails de salida/flujo → respuesta controlada`.  
**Contexto estructural:** toolkit open source con control de diálogo, conexión segura de modelos/chains/tools y mecanismos contra jailbreaks/prompt injection; soporta RAG, asistentes, endpoints LLM y cadenas LangChain.  
**Nivel seleccionado:** safety/policy/LLM guardrail layer.  
**Qué aporta a un agente:** políticas programables, control de diálogo, protección de tool use y mitigación de vulnerabilidades LLM.

---
**COMPONENTES_DOCUMENTADOS = 130**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 131–135**  
**SIGUIENTE FÍSICO = inventario desde entrada 134; verificar fresh antes de escribir el próximo archivo.**