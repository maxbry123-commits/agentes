# 📂 MAPA DE RUTA — BLOQUE 3 DE 4
## Workflows, pool paralelo y memoria (Fase 3-4)
**Depende de:** cierre del Bloque 2 (reasoning-kernel y gobernanza con tests reales)
**Objetivo del bloque:** que exista al menos un workflow real de punta a punta, y que el pool de agentes en paralelo deje de ser "puertos parciales" según la auditoría.

---

## TABLA DE TAREAS 36-55

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso a usar | IA sugerida |
|---|---|---|---|---|---|
| 36 | Definir el primer `yaml-dag` real | "Diseña un DAG en YAML para un caso simple y real (ej. 'recibir tarea de código → analizar → generar → validar → entregar')." | `multi-workflow-engine/instances/workflow-1/` | — | GPT |
| 37 | Crear `step-template` reutilizable | "Extrae de la tarea 36 una plantilla genérica de paso (input, acción, output, siguiente paso) reutilizable para futuros workflows." | `definition-registry/workflow-definition/step-template/` | — | GPT |
| 38 | Registrar workflow-1 en el registry | "Registra el workflow-1 en el índice central de workflows disponibles con su score de complejidad esperado." | `definition-registry/workflow-definition/` | — | Codex |
| 39 | Implementar `dag-executor` | "Implementa un ejecutor de DAGs con estado persistente que siga el yaml-dag de la tarea 36." | `execution-orchestration/state-machine-executor/` | LangGraph o Burr | Claude Code |
| 40 | Implementar `state-machine-executor` con FSM | "Implementa una máquina de estados explícita para las transiciones que no son un DAG simple (ej. reintentos, bifurcaciones)." | `execution-orchestration/state-machine-executor/` | `transitions` (Python) | Codex |
| 41 | Conectar `task-generation` real | "Conecta la recepción de tareas de `input-layer/reception/` con la generación formal de tareas validadas contra `task-definition/`." | `execution-orchestration/task-generation/` | — | Codex |
| 42 | Implementar `deterministic-execution` guard | "Implementa una verificación previa que bloquee cualquier invocación al LLM si el score de la tarea 19 no lo justifica." | `execution-orchestration/deterministic-execution/` | — | Codex |
| 43 | Extraer `worktree-isolation` de Grok Build | "Analiza `crates/codegen/xai-grok-pager/docs/tutorial/06-worktrees.md` de xai-org/grok-build y adapta solo el mecanismo de aislamiento por git worktree, sin su bucle decisor." | `execution-engine-pool/worktree-isolation/` | xai-org/grok-build (solo esa pieza) | Grok |
| 44 | Extraer coordinación de subagentes de Grok Build | "Analiza `docs/user-guide/16-subagents.md` de xai-org/grok-build y adapta el contrato de coordinación de subagentes a `agent-fleet-parallelism`, descartando su lógica de decisión propia." | `agent-fleet-parallelism/` | xai-org/grok-build (solo esa pieza) | Grok |
| 45 | Implementar pool paralelo real | "Implementa un pool de workers donde cada worker es una copia idéntica del mismo código, diferenciada solo por el contrato de tarea que recibe." | `execution-engine-pool/` | Ray (o Celery si se prefiere más simple) | Claude Code |
| 46 | Implementar `capability-matching` | "Implementa el emparejamiento entre una tarea y la capacidad/agente del pool más adecuado, según el capability-passport de cada uno." | `execution-engine-pool/capability-matching/` | — | Codex |
| 47 | Implementar `result-normalization` | "Implementa un normalizador que reciba las salidas heterogéneas del pool y las convierta a un esquema común antes de agregarlas." | `execution-engine-pool/result-normalization/` | PydanticAI | Codex |
| 48 | Implementar `mesh-routing-collaboration` (agregador) | "Implementa el agregador final: resumen, voto por mayoría, o arbitraje por supervisor, según el tipo de tarea." | `mesh-routing-collaboration/` | Mixture-of-Agents (patrón agregador) | Grok |
| 49 | Registrar piezas de Grok Build como passport | "Documenta origen, licencia (Apache-2.0), versión y fingerprint de cada pieza extraída de grok-build en su capability-passport correspondiente." | `extension-kernel/capability-passport/` | — | MiniMax |
| 50 | Implementar `mount-guard` real | "Implementa sandbox sin red + escaneo de secretos como paso obligatorio antes de registrar cualquier capacidad externa, especialmente las de Grok Build." | `extension-kernel/mount-guard/` | gVisor / Firecracker + `detect-secrets` | Codex |
| 51 | Añadir memoria de largo plazo | "Integra un sistema de memoria persistente por agente, con bloques de identidad y memoria consultable por búsqueda." | `tools-models-memory-knowledge/memory/` | Letta (MemGPT) o Mem0 | GPT |
| 52 | Conectar memory write del reasoning-kernel | "Conecta los pasos MEMORY_WRITE (corto y largo plazo) del template Mythos a la memoria persistente de la tarea 51." | `reasoning-kernel/decision-on-demand/` | Letta/Mem0 | Codex |
| 53 | Implementar `auxiliary-role-agents` | "Define roles fijos para agentes del pool (ej. investigador, lógica/verificación, contrarian/crítico) inspirados en el patrón de 4 agentes de Grok 4.20." | `execution-engine-pool/auxiliary-role-agents/` | — | Grok |
| 54 | Tests de integración workflow→pool→agregador | "Escribe un test de integración que corra workflow-1 completo, pase por el pool, y verifique que el agregador produce una salida válida contra el esquema." | `execution-orchestration/tests/` | `pytest` | Codex |
| 55 | Cierre del Bloque 3 | "Actualiza el gap-registry marcando qué tareas 36-54 quedaron resueltas." | `control-governance/gap-registry/` | — | MiniMax |

---

## CHECKPOINTS — rellenar al cerrar cada tarea

📝 Checkpoint tarea 36 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 37 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 38 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 39 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 40 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 36-40 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 41 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 42 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 43 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 44 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 45 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 41-45 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 46 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 47 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 48 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 49 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 50 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 46-50 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 51 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 52 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 53 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 54 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 55 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 51-55 (cierre del Bloque 3) — Quién audita: ___ | Fecha: ___ | Veredicto: ___

**Criterio de cierre del Bloque 3:** workflow-1 corre de punta a punta, el pool ejecuta al menos 2 workers en paralelo con roles distintos, y toda pieza extraída de Grok Build tiene su capability-passport documentado.
