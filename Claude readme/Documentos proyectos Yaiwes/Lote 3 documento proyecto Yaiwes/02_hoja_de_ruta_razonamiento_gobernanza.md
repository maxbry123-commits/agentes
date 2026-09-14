# 📂 MAPA DE RUTA — BLOQUE 2 DE 4
## Kernel de razonamiento y gobernanza (Fase 1-2)
**Depende de:** cierre del Bloque 1 (las 8 primitivas ya existen como archivo real)
**Objetivo del bloque:** que `reasoning-kernel/` y `control-governance/` dejen de tener 0 tests y placeholders, e integrar Mythos/EURS/DRE como contenido versionado, no como código.

---

## TABLA DE TAREAS 16-35

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso a usar | IA sugerida |
|---|---|---|---|---|---|
| 16 | Implementar `goal-dual-driver` real | "Crea un schema Pydantic para objetivo primario + lista de objetivos secundarios, con validación de que siempre haya exactamente un primario." | `reasoning-kernel/goal-dual-driver/` | Pydantic | GPT |
| 17 | Implementar `decision-on-demand` | "Implementa un módulo DSPy tipo `ChainOfThought` que reciba una tarea y el template Mythos seleccionado, y devuelva una decisión estructurada." | `reasoning-kernel/decision-on-demand/` | DSPy | GPT |
| 18 | Mover los prompts de Fables a contenido versionado | "Extrae el texto de los 40 pasos Mythos, EURS Standard, EURS Turbo y DRE de los documentos originales y guárdalos como archivos `.md` independientes, sin lógica de código." | `reasoning-kernel/decision-on-demand/prompts/` | — | MiniMax |
| 19 | Implementar el score de complejidad | "Implementa la fórmula: score = (dependencias×2) + pasos_estimados + (5 si ambiguo) + (5 si alto riesgo), y clasifica en LOW/MEDIUM/HIGH/EXTREME." | `execution-orchestration/classifier-scheduler/` | — | Codex |
| 20 | Conectar score → selección de plantilla | "Usa el score de la tarea 19 para elegir automáticamente entre `dre_by_score.md`, `eurs_standard.md`, `eurs_turbo.md` o `mythos_40.md`." | `reasoning-kernel/decision-on-demand/` | — | Codex |
| 21 | Implementar `expert-panel-router` | "Implementa un comparador que reciba una tarea nueva y la compare contra `workflow-definition/` existentes, devolviendo el mejor match y su score de confianza." | `reasoning-kernel/expert-panel-router/` | `semantic-router` | GPT |
| 22 | Implementar `consensus-trigger` | "Implementa el patrón Mixture-of-Agents: varios proponentes generan candidatos en paralelo, un agregador elige o fusiona." | `reasoning-kernel/consensus-trigger/` | Mixture-of-Agents (Together AI) | Grok |
| 23 | Implementar `workflow-capacity` | "Define cuántos workflows pueden correr concurrentemente según recursos disponibles, y expón esa cifra como config, no hardcodeada." | `reasoning-kernel/workflow-capacity/` | — | Codex |
| 24 | Definir `schema-contracts` (contrato cerrado) | "Define con Pydantic el esquema exacto de entrada/salida que cualquier capacidad, workflow o agente debe cumplir para ser aceptado por el kernel." | `definition-registry/schema-contracts/` | PydanticAI | GPT |
| 25 | Implementar validador de contrato cerrado | "Implementa un validador que rechace cualquier capacidad que no cumpla el schema de la tarea 24, antes de que llegue a `mount-guard`." | `kernel-principal/contracts/validator.py` | `jsonschema` / PydanticAI | Codex |
| 26 | Implementar deadline/timeout en el Scheduler | "Añade un timeout configurable por tarea; si se excede, cancela y reporta al Policy Engine." | `kernel-principal/scheduler.py` | `asyncio.wait_for` | Codex |
| 27 | Implementar idempotencia en el State Manager | "Añade una clave de deduplicación por `mission_id` para que reintentar una tarea no duplique efectos." | `kernel-principal/state_manager.py` | — | Codex |
| 28 | Implementar concurrencia segura del State Manager | "Añade bloqueo optimista (versión por registro) para que dos réplicas paralelas no se pisen al escribir el mismo estado." | `kernel-principal/state_manager.py` | — | Claude Code |
| 29 | Implementar `sheriff-sentinel-council` | "Implementa reglas duras (deny-list de acciones) usando un motor de políticas declarativo." | `control-governance/sheriff-sentinel-council/` | Open Policy Agent (OPA) | GPT |
| 30 | Implementar `verdict-authority` (Judge) | "Implementa un evaluador que compare dos o más soluciones candidatas y elija según criterios objetivos, no preferencia arbitraria." | `control-governance/verdict-authority/` | Prometheus (modelo juez OSS) / TruLens | Grok |
| 31 | Implementar `forensic-core` | "Implementa un log append-only que registre cada decisión del kernel con timestamp, mission_id y resultado." | `control-governance/forensic-core/` | OpenTelemetry | Codex |
| 32 | Implementar `llm-control-deny` | "Define una lista explícita de acciones que el LLM nunca puede ejecutar directamente sin pasar por Policy Engine, y valida contra ella cada llamada." | `control-governance/llm-control-deny/` | Guardrails AI | GPT |
| 33 | Tests unitarios de `reasoning-kernel` | "Escribe tests unitarios para goal-dual-driver, decision-on-demand, expert-panel-router y consensus-trigger (hoy: 0 tests)." | `reasoning-kernel/tests/` | `pytest` | Codex |
| 34 | Tests unitarios de `extension-kernel` | "Escribe tests unitarios para capability-registry, abi-mount y mount-guard (hoy: 0 tests)." | `extension-kernel/tests/` | `pytest` | Codex |
| 35 | Cerrar `gap-registry` | "Actualiza el registro de huecos pendientes marcando qué tareas de este bloque quedaron resueltas y cuáles no." | `control-governance/gap-registry/` | — | MiniMax |

---

## CHECKPOINTS — rellenar al cerrar cada tarea

📝 Checkpoint tarea 16 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 17 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 18 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 19 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 20 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 16-20 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 21 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 22 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 23 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 24 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 25 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 21-25 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 26 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 27 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 28 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 29 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 30 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 26-30 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 31 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 32 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 33 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 34 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 35 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 31-35 (cierre del Bloque 2) — Quién audita: ___ | Fecha: ___ | Veredicto: ___

**Criterio de cierre del Bloque 2:** el "ciclo cognitivo" que la auditoría marcó como no cerrado en `reasoning-kernel/` ahora tiene código real y tests; Mythos/EURS/DRE viven como archivos de prompt versionados, nunca como lógica de control.
