# 📂 MAPA DE RUTA — Integración de Loops, Multi-API, Memoria 20M y Chat
**Depende de:** cierre de los Bloques 1-4 anteriores (kernel base ya delegando correctamente)
**Objetivo:** cerrar el diseño de Fables (Time-Wheel, Multi-API Fabric, Input Block, Fleet Manager, Memoria de 5 niveles, gateway de chat) con librerías reales, no desde cero.

## TABLA DE TAREAS

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso | IA sugerida |
|---|---|---|---|---|---|
| 71 | Implementar Time-Wheel scheduler | "Implementa un scheduler periódico usando APScheduler que dispare triggers según config declarativa (cron o intervalo), sustituyendo el `timewheel.py` sin código." | `parallel/timewheel.py` | APScheduler + `croniter` | Codex |
| 72 | Implementar Multi-API Fabric — modo SINGLE/RACE | "Configura LiteLLM Router con al menos 3 proveedores registrados, y añade un modo RACE con `asyncio.wait(FIRST_COMPLETED)` sobre esos proveedores." | `llmnet/fanout.py` | LiteLLM Router | Codex |
| 73 | Implementar Multi-API Fabric — modo QUORUM | "Implementa el patrón Mixture-of-Agents: N proveedores responden en paralelo, un agregador exige coincidencia mínima antes de aceptar." | `llmnet/fanout.py` | Mixture-of-Agents | Grok |
| 74 | Implementar Multi-API Fabric — modo SPLIT | "Divide el input en N partes lógicas y despacha cada una a un proveedor distinto vía LiteLLM Router, combinando resultados al final." | `llmnet/fanout.py` | LiteLLM Router + `asyncio.gather` | Codex |
| 75 | Implementar Input Block Reader (cola con hash-chain+TTL) | "Configura NATS JetStream (o Redis Streams) con deduplicación por hash de mensaje y TTL de retención, para que el sistema siga aceptando input mientras procesa." | `inputblock/store.py` | NATS JetStream | Claude Code |
| 76 | Implementar Fleet Manager real | "Implementa un pool de Ray Actors, uno por cada agente externo (Aider, Codex, Hermes), cada uno en su propio worktree aislado." | `fleet/manager.py` | Ray + Grok Build (worktrees) | Grok |
| 77 | Extraer patrón "fleet profile rail" de Hermes v0.20.6 | "Revisa el release v0.20.6 de NousResearch/hermes-agent y adapta el mecanismo de fleet profile rail a `agent-fleet-parallelism/`, descartando su lógica de decisión propia." | `agent-fleet-parallelism/` | Hermes Agent v0.20.6 (solo esa pieza) | Grok |
| 78 | Implementar memoria Nivel 1 (cache/búsqueda) | "Integra Letta para reasoningBank + hierarchicalMemory + vectorBackend." | `tools-models-memory-knowledge/memory/nivel1/` | Letta (MemGPT) | GPT |
| 79 | Implementar memoria Nivel 2 (grafo) | "Integra Graphiti para memoryGraph + causalGraph + gnnService." | `tools-models-memory-knowledge/memory/nivel2/` | Graphiti | GPT |
| 80 | Implementar memoria Nivel 3 (skills/reflexión) | "Implementa explainableRecall y reflexion usando el patrón Reflexion ya identificado, conectado al registro de skills." | `tools-models-memory-knowledge/memory/nivel3/` | Reflexion | Codex |
| 81 | Implementar memoria Nivel 4-5 (síntesis avanzada) | "Integra LlamaIndex Property Graph Index para contextSynthesizer y mmrDiversityRanker (MMR nativo)." | `tools-models-memory-knowledge/memory/nivel4-5/` | LlamaIndex | GPT |
| 82 | Adoptar patrón sesión/harness de Anthropic | "Separa explícitamente el log de sesión (append-only) del bucle harness siguiendo el patrón Managed Agents de Anthropic; documenta cuál archivo es cuál." | `state-events-durability/` (sesión) vs `kernel-principal/` (harness) | — (patrón, no librería) | GPT |
| 83 | Separar Generador de Evaluador (anti self-evaluation bias) | "Verifica que CHEF_FINAL y JUDGE nunca corran en la misma instancia/contexto que generó la solución que están evaluando." | `chef_final/`, `control-governance/verdict-authority/` | — | Claude Code |
| 84 | Implementar contexto reset estructurado (anti context-anxiety) | "Cuando el score de complejidad indique tarea larga, implementa reinicio de contexto con resumen estructurado en vez de dejar crecer el mismo hilo." | `reasoning-kernel/decision-on-demand/` | Claude Agent SDK (compactación) como referencia | GPT |
| 85 | Elicitación estructurada por listas (rutas previas) | "Implementa un schema Pydantic con campos `enum` para cada decisión de ruta que hoy se pregunta como texto libre." | `input-layer/reception/` | PydanticAI (o Rasa si se quiere framework dedicado) | Codex |
| 86 | Adoptar gateway multicanal de OpenClaw 2.0 | "Estudia el Gateway de OpenClaw 2.0 (separación daemon/agentes) y adapta el patrón a `input-layer/route-entry/`, sin copiar su bucle decisor." | `input-layer/route-entry/` | OpenClaw 2.0 (solo el Gateway) | Grok |
| 87 | Registrar catálogo MCP de Hermes | "Registra en `capability-registry/` los servidores MCP verificados que Hermes v0.20.6 ya cataloga, con su passport correspondiente." | `extension-kernel/capability-passport/` | Hermes MCP catalog | MiniMax |
| 88 | Test de integración Multi-API Fabric | "Prueba los 4 modos (SINGLE/RACE/QUORUM/SPLIT) contra al menos 3 proveedores reales, verificando que cada modo produce el comportamiento esperado." | `llmnet/tests/` | `pytest` | Codex |
| 89 | Test de integración Input Block bajo carga | "Simula input concurrente llegando mientras el sistema procesa una tarea larga, verifica que no se pierde ni duplica ningún mensaje." | `inputblock/tests/` | `pytest` + NATS test harness | Codex |
| 90 | Auditoría final de esta capa | "Actualiza el gap-registry marcando qué tareas 71-89 quedaron resueltas, y qué parte del diseño Fables (Time-Wheel, Multi-API, Input Block, Fleet, Memoria 5 niveles) ya tiene código real vs solo diseño." | `control-governance/gap-registry/` | — | MiniMax |

## CHECKPOINTS

📝 Checkpoint tarea 71 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 72 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 73 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 74 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 75 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___

🔍 Auditoría tareas 71-75 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 76 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 77 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 78 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 79 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 80 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___

🔍 Auditoría tareas 76-80 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 81 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 82 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 83 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 84 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 85 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___

🔍 Auditoría tareas 81-85 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 86 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 87 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 88 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 89 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___
📝 Checkpoint tarea 90 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia: ___

🔍 Auditoría tareas 86-90 (cierre de esta capa) — Quién audita: ___ | Fecha: ___ | Veredicto: ___
