# 📂 README ÍNDICE COMPONENTES 1 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes`  
Rama: `main`  
Raíz: `Core kernel Yaiwes/`  
Bloque: **1–5**  
Regla: ficha basada en código/README/manifiesto/Handoff físicos; lo no demostrado se marca `NO VERIFICADO`.

---

## YAIWES 01 — A2A-Protocol ➡️ Interoperabilidad y ciclo de tareas agente ↔ agente

**URL raíz / ubicación:** https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/A2A-Protocol  
**Handoff:** Handoff global YAIWES; destino funcional específico `NO REGISTRADO`.  
**Fuente seleccionada:** `A2AService.SendMessage()` + `Task` + `TaskState`, `code/specification/a2a.proto`.  
**Determinista:** Sí, ≈98% en protocolo; estados/schemas/rutas son deterministas, no la conducta del agente remoto.  
**¿Es agente?:** No; es un protocolo de interoperabilidad entre agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** no razona objetivos; define mensaje, contexto, tarea, lifecycle, streaming y artefactos. La decisión semántica queda en el agente receptor.  
**Microflujo horizontal:** `AgentCard → capacidad → SendMessage → Task → SUBMITTED → WORKING → stream/intercambio → COMPLETED | FAILED | CANCELED | INPUT_REQUIRED | REJECTED`  
**Contexto funcional:** incluye Send/Streaming, Get/List/Cancel/Subscribe Task, push notifications y AgentCard; `Task` conserva id, context_id, status, artifacts, history y metadata.  
**Nivel seleccionado:** protocolo de interoperabilidad multiagente.  
**Qué aporta a un agente:** delegación/supervisión interoperable sin conocer memoria, prompt o tools internas del agente remoto.  
**Evidencia física:** manifest de `a2aproject/A2A`, 135 archivos, extracción/reconstrucción verificadas.

---

## YAIWES 02 — Agent-xpu-LLM-xpu ➡️ Scheduling heterogéneo de inferencia agentic CPU/NPU/iGPU

**URL raíz / ubicación:** https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/Agent-xpu-LLM-xpu  
**Handoff:** Handoff global YAIWES; destino funcional específico `NO REGISTRADO`.  
**Fuente seleccionada:** `hllm::ContextOV::continue_or_preempt()` + `submit_job()` y event loops, `code/csrc/end2end/ov/context.h`.  
**Determinista:** No, ≈80% en scheduling; políticas/colas son programáticas, pero concurrencia, llegada de jobs, hardware y sampling pueden variar.  
**¿Es agente?:** No; es runtime/motor de inferencia para workloads agentic.  
**Cómo funciona el kernel/core para tomar decisiones:** decide cuándo/dónde/con qué prioridad ejecutar inferencia mediante colas prefill/decode, high-priority, batching y preemption; no decide el objetivo del agente.  
**Microflujo horizontal:** `InferJob → submit_job → prioridad → prefill_queue → NPU/GPU prefill → decode_queue → batching → continue_or_preempt → sampling → complete_job`  
**Contexto funcional:** ContextOV contiene Llama, tokenizer, sampler, OpenVINO, buffers, colas, mutexes/condition variables y threads prefill/decode/GC.  
**Nivel seleccionado:** runtime de inferencia + scheduler heterogéneo.  
**Qué aporta a un agente:** ejecución concurrente local con batching, prioridad y preemption sobre CPU/NPU/iGPU.

---

## YAIWES 03 — AgentCgroup ➡️ Aislamiento y prioridad de recursos OS por sesión y tool-call

**URL raíz / ubicación:** https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/AgentCgroup  
**Handoff:** Handoff global YAIWES; destino funcional específico `NO REGISTRADO`.  
**Fuente seleccionada:** `AgentCGroupDaemon.start()` + `setup_cgroup_hierarchy()`, `code/agentcg/agentcgroupd.py`.  
**Determinista:** Sí, ≈95% en política; jerarquía/pesos/límites son explícitos, el consumo/timing real depende de kernel y carga.  
**¿Es agente?:** No; es controlador de recursos para agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** crea `session_high/session_low`, activa CPU+memory, asigna pesos y coordina scheduler, memcg y process monitor; decide QoS de recursos, no semántica.  
**Microflujo horizontal:** `tool-call → wrapper → cgroup → session_high/session_low → sched_ext + memcg → EXEC/EXIT monitor → health/poll → liberar`  
**Contexto funcional:** daemon, bash wrappers, scheduler eBPF, memcg, process monitor, health checks y experimentos multi-tenant.  
**Nivel seleccionado:** aislamiento/QoS de runtime.  
**Qué aporta a un agente:** evita monopolio de CPU/memoria y permite prioridades independientes de la conducta del LLM.

---

## YAIWES 04 — AgentGuard ➡️ Gate determinista de seguridad antes de ejecutar comandos

**URL raíz / ubicación:** https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/AgentGuard  
**Handoff:** Handoff global YAIWES; destino funcional específico `NO REGISTRADO`.  
**Fuente seleccionada:** `RuleEngine.validate(command, rules)`, `code/src/rule-engine.ts`.  
**Determinista:** Sí, ≈99%; usa reglas/pattern matching, no un LLM para decidir permiso.  
**¿Es agente?:** No; es guardrail/policy engine frente a agentes.  
**Cómo funciona el kernel/core para tomar decisiones:** verifica comandos inherentemente peligrosos, rutas catastróficas y segmentos de pipes/chains; después aplica `BLOCK | CONFIRM | ALLOW`. Un segmento bloqueado bloquea toda la cadena; sin match usa allow por defecto.  
**Microflujo horizontal:** `tool-call shell → tokenize → unwrap → peligro? → ruta crítica? → chain/pipe → match reglas → BLOCK | CONFIRM | ALLOW → ejecutar/detener → audit`  
**Contexto funcional:** tokenizer, unwrapper, matcher, rule parser, script analyzer, audit logger e integraciones de hooks.  
**GAP comprobado:** `applyProtectDirectives()`, `applySandboxDirectives()`, `detectWriteOperation()` y `extractTargetPaths()` siguen como `TODO`; no es sandbox completo.  
**Nivel seleccionado:** gate determinista de seguridad / policy enforcement.  
**Qué aporta a un agente:** somete cada shell action a una política reproducible antes de ejecutarla.

---

## YAIWES 05 — AgentScope ➡️ Runtime ReAct con estado, tools, permisos y memoria

**URL raíz / ubicación:** https://github.com/maxbry123-commits/agentes/tree/main/Core%20kernel%20Yaiwes/AgentScope  
**Handoff:** Handoff global YAIWES; destino funcional específico `NO REGISTRADO`.  
**Fuente seleccionada:** clase `agentscope.agent.Agent`, especialmente `Agent.reply()`, `code/src/agentscope/agent/_agent.py`.  
**Determinista:** No, ≈35% en el camino decisor completo; runtime/permisos son programáticos, la selección semántica depende del modelo.  
**¿Es agente?:** El proyecto es framework/runtime; sí contiene una implementación concreta `Agent`.  
**Cómo funciona el kernel/core para tomar decisiones:** combina AgentState/contexto, modelo, ReAct, PermissionEngine, middleware y Toolkit; el modelo propone acciones y el runtime gobierna permisos/estado/continuación.  
**Microflujo horizontal:** `Msg → Agent.reply → AgentState/context injection → reasoning/model → tool proposal → PermissionEngine → tool execution → observation → state update → repeat | interrupt/resume → final`  
**Contexto funcional:** Toolkit Python/MCP/skills, modelos, eventos, permisos/HITL, middleware, memoria, workspace/sandbox, persistencia/scheduling y compresión de contexto con token thresholds, resumen y actualización de `state.summary/state.context`.  
**Nivel seleccionado:** framework/runtime agentic ReAct.  
**Qué aporta a un agente:** esqueleto operacional con estado, tools, permisos, memoria, compresión contextual e interrupción/reanudación.

---

## Estado del bloque

`COMPONENTES_DOCUMENTADOS = 5`  
`RANGO = 1-5`  
`SIGUIENTE_BLOQUE = 6-10`  
`ARCHIVO_SIGUIENTE = readme índice componentes 2 .md`
