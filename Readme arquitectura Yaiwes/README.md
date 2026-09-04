# README — Arquitectura fusionada YAIWES · X-Ray

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Fecha de corte:** 2026-09-01  
**Regla:** GitHub y el código ejecutable son la verdad. Una carpeta o documento no demuestra que una capacidad esté operativa.

## 1. Fuentes fusionadas y trazabilidad

1. [Índice raíz de arquitectura YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20estructura%20ra%C3%ADz%20de%20agente%20Yaiwes%20wordflow.md)
2. [PLAN_100 — árbol definitivo](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md)
3. [STRUCTURE — estructura materializada](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/STRUCTURE.md)
4. [README canónico de agente-yaiwes](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/README.md)
5. [Foto de producción y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md)
6. [Mapa de organización del código real](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md)
7. [Arquitectura Wordflow consolidada](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md)
8. [Pasada 1 — Structure](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_01_STRUCTURE.md)
9. [Pasada 2 — Connectivity](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_02_CONNECTIVITY.md)
10. [Pasada 3 — Behavior](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_03_BEHAVIOR.md)
11. [Pasada 4 — Cierre](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_04_CIERRE.md)

## 2. Leyenda X-Ray

- **REAL:** código ejecutable materializado.
- **PARCIAL:** existe una parte, espejo o cableado incompleto.
- **ESQ:** scaffold/placeholder; no equivale a capacidad.
- **REF:** puntero a la fuente canónica.
- **FALTANTE:** requerido por la arquitectura y no demostrado por código o pruebas.

- mapa de ruta lo que la ai debe de seguir la siguiente tarea el siguiente paso

- # 📂 MAPA DE RUTA — BLOQUE 1 DE 4
## Fundamentos y limpieza del Kernel TEAM (Fase 0)
**Anexo checkpoint raíz de:** Readme arquitectura Yaiwes 📂➡️
**Objetivo del bloque:** eliminar la duplicación real detectada por la auditoría (blobs SHA idénticos entre `kernel-principal` y `extensions/wordflow_kernel`) y dejar `kernel-principal` funcionando como fachada delegante desde el primer día.

**Regla para todas las tareas de este documento:** no se escribe código nuevo salvo que la tarea lo diga explícitamente. La mayoría son ensamblar, cablear, o envolver código ya existente.

---

## TABLA DE TAREAS 1-15

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso a usar | IA sugerida |
|---|---|---|---|---|---|
| 1 | Eliminar duplicación de `workflow.py`/`runtime.py` | "Compara byte a byte `kernel-principal/workflow.py` y `runtime.py` contra sus equivalentes en `extensions/wordflow_kernel/`. Si son idénticos, borra los de `kernel-principal` y sustitúyelos por un import directo." | `kernel-principal/` | — (solo Git) | Claude Code |
| 2 | Generar manifest SBOM del repo completo | "Genera un SBOM en formato CycloneDX de todo el repositorio `agentes`." | raíz del repo, `MANIFEST.sbom.json` | `cyclonedx-python` o `syft` | Codex |
| 3 | Crear entrypoint canónico CLI | "Crea un CLI con Typer que exponga `python -m agente` y delegue en `extensions/wordflow_kernel/runtime.py`." | `input-layer/cli-entry/` | `Typer` | Codex |
| 4 | Activar tipado estricto sobre `kernel-principal` | "Configura `mypy --strict` (o `pyright`) solo sobre `kernel-principal/` y lista todos los errores/placeholders que aparezcan." | `kernel-principal/mypy.ini` | `mypy` / `pyright` | Codex |
| 5 | Definir contratos vacíos de las 8 primitivas | "Crea 8 archivos de interfaz (Protocol o clase abstracta) para: Event Loop, DSL Engine, Scheduler, Runtime, Registry, Router, Policy Engine, State Manager. Sin lógica, solo firmas." | `kernel-principal/contracts/` | `typing.Protocol` + Pydantic | GPT |
| 6 | Wrapper delegante — Event Loop | "Implementa la interfaz Event Loop llamando internamente al bucle equivalente de `wordflow_kernel/runtime.py`." | `kernel-principal/event_loop.py` | — | Claude Code |
| 7 | Wrapper delegante — DSL Engine | "Implementa la interfaz DSL Engine delegando en el parser de `wordflow_kernel` si existe; si no existe, márcalo como `nativo pendiente`." | `kernel-principal/dsl_engine.py` | — | Claude Code |
| 8 | Wrapper delegante — Scheduler | "Implementa la interfaz Scheduler delegando en la lógica de orden/ejecución de `wordflow_kernel`." | `kernel-principal/scheduler.py` | — | Claude Code |
| 9 | Wrapper delegante — Runtime | "Implementa la interfaz Runtime delegando en `wordflow_kernel/runtime.py`." | `kernel-principal/runtime.py` (reescrito como fachada) | — | Claude Code |
| 10 | Wrapper delegante — Registry | "Implementa la interfaz Registry delegando en `engine_registry.py` de `wordflow_kernel`." | `kernel-principal/registry.py` | — | Claude Code |
| 11 | Wrapper delegante — Router | "Implementa la interfaz Router delegando en `gateway/router_http.py` de `wordflow_kernel`." | `kernel-principal/kernel-router/` | — | Claude Code |
| 12 | Wrapper delegante — Policy Engine | "Implementa la interfaz Policy Engine delegando en `fail_closed.py`/`preflight.py` de `wordflow_kernel`." | `kernel-principal/policy_engine.py` | — | Claude Code |
| 13 | Wrapper delegante — State Manager | "Implementa la interfaz State Manager delegando en `instance_store.py`/`ledger.py`/`checkpoint.py` de `wordflow_kernel`." | `kernel-principal/state_manager.py` | — | Claude Code |
| 14 | Manifest de estado de migración | "Crea un archivo YAML/JSON con las 8 primitivas y un campo `estado: delegado \| nativo` por cada una." | `kernel-principal/MIGRATION_MANIFEST.yaml` | — | GPT |
| 15 | Regresión contra los 27 tests existentes | "Ejecuta la suite de 27 tests de `extensions/wordflow_kernel/` contra las 8 wrappers nuevas de `kernel-principal`. Ningún test puede fallar." | `kernel-principal/tests/test_regresion_wrappers.py` | `pytest` | Codex |

---

## CHECKPOINTS — rellenar al cerrar cada tarea

📝 Checkpoint tarea 1 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 2 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 3 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 4 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 5 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 1-5 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 6 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 7 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 8 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 9 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 10 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 6-10 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 11 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 12 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 13 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 14 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 15 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 11-15 (cierre del Bloque 1) — Quién audita: ___ | Fecha: ___ | Veredicto: ___

**Criterio de cierre del Bloque 1:** las 8 primitivas existen como archivo real en `kernel-principal/`, ninguna es un placeholder vacío, el manifest de migración está creado, y los 27 tests heredados siguen en verde.


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


# 📂 MAPA DE RUTA — BLOQUE 4 DE 4
## Observabilidad, testing y cierre de la primera versión completa (Fase 5)
**Depende de:** cierre del Bloque 3 (workflow + pool funcionando de punta a punta)
**Objetivo del bloque:** que la próxima auditoría X-Ray pueda cambiar el veredicto de `FAIL-CLOSED / PARCIAL` a `PASS / COMPLETO`.

---

## TABLA DE TAREAS 56-70

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso a usar | IA sugerida |
|---|---|---|---|---|---|
| 56 | Implementar `observability/trace-history` | "Instrumenta cada llamada del kernel con trazas distribuidas estándar." | `observability/trace-history/` | OpenTelemetry | Codex |
| 57 | Hacer obligatorio mission_id/trace/ledger | "Modifica el Event Loop para que ninguna ejecución pueda iniciar sin un mission_id, trace_id y entrada de ledger asociados." | `kernel-principal/event_loop.py` | — | Claude Code |
| 58 | Implementar ledger/checkpoint durable | "Envuelve la ejecución de workflows críticos en un motor de ejecución durable que sobreviva reinicios." | `state-events-durability/` | Temporal (o LangGraph checkpointer si se prefiere más ligero) | Claude Code |
| 59 | Implementar `retry-policy` con reintentos deterministas | "Implementa reintentos con backoff exponencial conectados al circuit-breaker." | `resource-governance/retry-policy/` | Tenacity | Codex |
| 60 | Implementar `circuit-breaker` real | "Implementa un breaker que abra el circuito tras N fallos consecutivos de una capacidad y la marque como no disponible temporalmente." | `resource-governance/circuit-breaker/` | Tenacity / `pybreaker` | Codex |
| 61 | Implementar `resource-broker-gate` + `lease-management` | "Implementa un control de cuántas ejecuciones concurrentes puede sostener el sistema, con préstamo (lease) de recursos por tarea." | `resource-governance/resource-broker-gate/` | — | Codex |
| 62 | Implementar `watchdog` | "Implementa un proceso que detecte tareas colgadas más allá de su deadline (tarea 26) y las cancele forzosamente." | `resource-governance/watchdog/` | — | Codex |
| 63 | Reemplazar Fake/Stub por contract-testing real | "Sustituye los stubs de prueba detectados por la auditoría por tests de contrato reales contra los esquemas de `schema-contracts/`." | ubicación original de cada stub detectado | Schemathesis o Pact | Codex |
| 64 | Generar Estado Merkle global | "Genera una prueba verificable del estado del ledger completo." | `state-events-durability/merkle/` | `pymerkle` (o usar Git como Merkle DAG) | MiniMax |
| 65 | Prueba E2E completa | "Escribe y ejecuta una prueba que cubra: reception → mission → decision → execution → evidence → closure, de principio a fin, sin mocks en los puntos críticos." | `execution-orchestration/tests/test_e2e_completo.py` | `pytest` + utilidades de testing de Temporal | Claude Code |
| 66 | SBOM + secret scan final de todo el repo | "Ejecuta un escaneo de secretos y dependencias sobre el repositorio completo antes de declarar cerrada la v1." | raíz del repo | `detect-secrets` + `syft` | MiniMax |
| 67 | Consolidar manifest final de las 8 primitivas | "Verifica que las 8 primitivas del manifest de la tarea 14 digan `nativo` o `delegado documentado` — ninguna puede quedar sin estado." | `kernel-principal/MIGRATION_MANIFEST.yaml` | — | GPT |
| 68 | Cerrar los 18 placeholders restantes | "Vuelve a correr `mypy --strict` sobre `kernel-principal/` y confirma cero placeholders restantes." | `kernel-principal/` | `mypy` | Codex |
| 69 | Auditoría final completa | "Repite exactamente el mismo formato de la Auditoría X-Ray original (conteo de archivos, Python, tests, placeholders) sobre todo `agente-yaiwes/`." | raíz del repo, nuevo documento de auditoría | — | MiniMax |
| 70 | Redactar veredicto de cierre v1 | "Compara la auditoría de la tarea 69 contra la original y redacta el veredicto final: qué cambió de PARCIAL a COMPLETO, con evidencia de cada cambio." | raíz del repo, `VEREDICTO_CIERRE_V1.md` | — | GPT |

---

## CHECKPOINTS — rellenar al cerrar cada tarea

📝 Checkpoint tarea 56 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 57 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 58 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 59 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 60 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 56-60 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 61 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 62 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 63 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 64 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 65 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 61-65 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 66 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 67 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 68 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 69 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 70 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 66-70 (CIERRE DE LA V1 COMPLETA) — Quién audita: ___ | Fecha: ___ | Veredicto: ___

---

## Criterio final de "primera versión completa"

La v1 está cerrada solo si las 4 condiciones siguientes son verdaderas al mismo tiempo:

1. El manifest de las 8 primitivas del Kernel TEAM no tiene ningún estado vacío.
2. Existe al menos un workflow real, probado E2E, que pasa por reception→mission→decision→execution→evidence→closure sin usar stubs.
3. El pool paralelo ejecuta al menos 2 agentes/workers reales con roles distintos y un agregador que produce una decisión final.
4. La auditoría X-Ray repetida (tarea 69) muestra cero placeholders en `kernel-principal/` y cobertura de tests en `reasoning-kernel/` y `extension-kernel/` (hoy en 0).

Si alguna de las 4 no se cumple, el veredicto sigue siendo `FAIL-CLOSED / PARCIAL` — no se declara v1 completa a medias.



## 3. Arquitectura completa fusionada — cuatro niveles

```text
main/
└── agente-yaiwes/
    ├── code-programming-engine/                         [PARCIAL/REF]
    │   ├── engine-modules/
    │   │   ├── code_path_runner.py                     [REF al hot path]
    │   │   ├── programming_pipeline.py                 [REF al hot path]
    │   │   └── cognitive_loop.py                       [REF/PARCIAL]
    │   ├── code-path-execution/
    │   │   ├── programming-modular-v1/
    │   │   ├── p01...p12                               [FALTANTE en main]
    │   │   └── evidence/                               [PARCIAL]
    │   ├── standards-forensic/
    │   ├── schema-contracts-io/
    │   ├── external-motor-bridge/
    │   ├── multi-account-bridge/
    │   ├── inbox-normalization/
    │   └── module-tests/
    ├── kernel-principal/
    │   ├── control-layer/
    │   │   └── SOURCE.md                               [REF]
    │   ├── extension-kernel/
    │   │   ├── abi-mount/
    │   │   ├── capability-registry/
    │   │   ├── capability-passport/
    │   │   ├── native-learning/
    │   │   └── mount-guard/
    │   ├── reasoning-kernel/
    │   │   ├── decision-on-demand/
    │   │   ├── expert-panel-router/
    │   │   ├── consensus-trigger/
    │   │   ├── goal-dual-driver/
    │   │   └── workflow-capacity/
    │   ├── resource-governance/
    │   │   ├── resource-broker-gate/
    │   │   ├── lease-management/
    │   │   ├── watchdog/
    │   │   ├── circuit-breaker/
    │   │   └── retry-policy/
    │   ├── internal-bus/
    │   └── execution-manifest/
    ├── input-layer/
    │   ├── cli-entry/
    │   ├── route-entry/
    │   ├── cross-tool-session-import/
    │   └── reception/
    ├── definition-registry/
    │   ├── workflow-definition/
    │   │   ├── yaml-dag/
    │   │   ├── step-template/
    │   │   └── source-hierarchy/
    │   ├── agent-definition/
    │   ├── task-definition/
    │   ├── tool-definition/
    │   ├── skill-definition/
    │   ├── schema-contracts/
    │   ├── domain-specific-contracts/
    │   ├── declared-dependency-catalog/
    │   └── authorization-model/
    ├── control-governance/
    │   ├── contracts-and-gates/
    │   ├── sheriff-sentinel-council/
    │   ├── forensic-verdict/
    │   ├── symbol-test-requirement-index/
    │   ├── policy-guardrails-permissions/
    │   ├── refute-repair/
    │   ├── pre-post-closure-gates/
    │   └── gap-registry-and-tasks/
    ├── multi-workflow-engine/
    │   ├── shared-services/
    │   │   ├── workflow-registry/
    │   │   ├── runner-host/
    │   │   ├── dashboard-budget/
    │   │   └── control-ops/
    │   └── instances/
    │       ├── workflow-1/
    │       ├── workflow-2/
    │       ├── workflow-3/
    │       └── workflow-N/
    ├── execution-orchestration/
    │   ├── state-machine-executor/
    │   ├── dag-executor/
    │   ├── sequential-parallel-loop-route/
    │   ├── container-pod-isolation/
    │   ├── task-generation/
    │   ├── deterministic-execution/
    │   ├── mission-planning-goal-lock/
    │   ├── classifier-scheduler/
    │   ├── dependency-injection-context/
    │   └── programming-pipeline/
    ├── agent-fleet-parallelism/
    ├── execution-engine-pool/
    │   ├── adapter-layer/                              [PARCIAL]
    │   ├── capability-matching/
    │   ├── parallel-dispatch/
    │   ├── worktree-isolation/
    │   ├── result-normalization/
    │   └── auxiliary-role-agents/                      [STUBS]
    ├── mesh-routing-collaboration/
    ├── pipeline-runtime/
    ├── codebase-intelligence/
    ├── session-resilience/
    ├── identity-config/
    ├── human-in-the-loop/
    ├── communication-notifications/
    ├── control-plane-ui/
    ├── state-events-durability/
    │   └── dead-letter-handling/
    ├── tools-models-memory-knowledge/
    │   └── mcp-transport/
    ├── research-evidence/
    ├── security-auth/
    ├── observability/
    │   └── trace-history/
    ├── multi-project-orchestration/
    ├── artifact-output-storage/
    ├── deploy-publish/
    │   ├── multi-account-registry/
    │   ├── push-injection/
    │   ├── publish-schema-layer/
    │   ├── remote-crud-ops/
    │   └── deployment-target-selector/
    ├── extensions/                                    [REF]
    ├── PIPELINE/                                      [REF]
    ├── agents/                                        [REF]
    └── .github-workflows-refs/                        [REF]
```

## 4. Código operativo real y Wordflow actual

La arquitectura nueva no sustituyó por completo el runtime anterior. El flujo ejecutable principal permanece aquí:

```text
main/
└── extensions/
    ├── wordflow/
    │   ├── reception/
    │   │   └── convert / normalización
    │   ├── planner/
    │   │   └── misión / tareas / clasificación
    │   ├── engine/
    │   │   ├── code_path_runner.py                    [HOT PATH REAL]
    │   │   ├── programming_pipeline.py                [REAL]
    │   │   ├── programming_kwargs.py                  [REAL]
    │   │   ├── input_quality_bar.py                   [REAL]
    │   │   ├── skill_native_compiler.py               [REAL]
    │   │   ├── goal_lock.py                           [REAL]
    │   │   └── cognitive_loop.py                      [REAL/PARCIAL]
    │   ├── motors/
    │   ├── codegen/
    │   ├── connectors/
    │   ├── contracts/
    │   ├── schemas/
    │   ├── standards/
    │   ├── state/
    │   ├── store/
    │   ├── policies/
    │   ├── accounts/
    │   └── tests/
    └── wordflow_kernel/
        ├── gateway/
        │   ├── intelligence.py                        [PUNTO DE ENCHUFE]
        │   └── router_http.py                         [ADAPTADOR HTTP]
        ├── runtime/
        ├── contracts/
        └── auxiliary/
            ├── openclaw_stub.py                       [STUB]
            └── hermes_stub.py                         [STUB]
```

### Flujo transversal

```text
Entrada
→ reception.convert
→ goals / goal_lock
→ mission + planner
→ task_classifier
→ programming_pipeline
→ code_path_runner
→ motors / tools / adapters
→ evidence
→ gates forenses
→ artefacto / despliegue
```


He revisado los puntos clave de tus documentos (especialmente el diseño "Kernel TEAM" de la Ley Principal, línea 4092 en adelante). Tengo buenas noticias: **Fables ya diseñó un microkernel real y coherente, con nombre y filosofía correctos** — lo compara explícitamente con QNX/Minix. Esto es lo que encontré exactamente.

## Las 8 capas de decisión que ya tienes definidas (esto es lo que hace que sea "avanzado")

Según tu propio documento, el `Kernel TEAM` (2.000–5.000 LOC) contiene exactamente 8 primitivas, y **no tiene** navegador, OCR, Git, Docker, ni IA — solo decide *qué* se ejecuta, *quién* lo ejecuta y *cuándo*:

1. **Event Loop** — el ciclo que nunca duerme, recibe eventos y los despacha.
2. **DSL Engine** — interpreta el lenguaje declarativo (nada de prompts en texto libre).
3. **Scheduler** — decide el orden y el momento de ejecución.
4. **Runtime** — el entorno que efectivamente corre una capacidad.
5. **Registry** — el catálogo de qué existe (capacidades, workflows, agentes de pool).
6. **Router** — decide a cuál capacidad/workflow/agente enviar cada tarea.
7. **Policy Engine** — aplica reglas duras antes de dejar pasar nada.
8. **State Manager** — la única fuente de verdad del estado del sistema.

Esto **sí es lo que hace avanzado a un sistema de agentes**: la mayoría de "agentes" que existen en GitHub mezclan estas 8 funciones dentro del propio bucle del LLM. Que tú las tengas separadas, nombradas, y con el LLM completamente fuera de las 8, ya te pone por encima del diseño típico.

## Diagrama: qué hace falta para decir "el core está completo"

## Cuántas líneas de código — y por qué esa cifra es correcta

Tus documentos ya calculan bien esto: **2.000–5.000 LOC para el Kernel TEAM**, separado de las **120.000 LOC** del proyecto completo (con todos los servicios/capacidades/workflows). Esa proporción es la correcta, y aquí está el porqué con referencias reales:

- Con 8 primitivas, a razón de 300-800 LOC bien escritas por primitiva (sin lógica de negocio, solo coordinación), te da exactamente ese rango de 2.500-6.000 LOC.
- Como comparación real: el **núcleo Raft de etcd** (la fuente de verdad de todo Kubernetes) son unas ~15.000 LOC — y eso que gestiona consenso distribuido, mucho más complejo que lo que tú necesitas para un solo nodo. Tu kernel siendo más simple (sin consenso distribuido todavía) cabe perfectamente en la mitad de eso.
- **La señal de alarma que debes vigilar:** si tu Kernel TEAM empieza a superar 8.000-10.000 LOC, es la prueba de que algo que debería ser un servicio (Nivel 2) se está colando dentro del kernel. Esa es literalmente la filosofía de Minix/QNX que tú mismo citaste: *"si puede fallar sin tumbar todo el sistema, no pertenece al kernel."*

## Qué otro sistema de core kernel recomiendo estudiar (no copiar entero, solo el patrón)

1. **Kubernetes control plane** (o su versión ligera **k3s**, mucho más fácil de leer) — es exactamente tu arquitectura ya probada a escala masiva: `kube-apiserver` = tu Registry+Router, `kube-scheduler` = tu Scheduler, `controller-manager` = tu Event Loop, `etcd` = tu State Manager.
2. **HashiCorp Nomad** — si Kubernetes te parece demasiado grande para leer el código fuente, Nomad hace lo mismo con muchísimo menos código y es más legible para un proyecto de una persona.
3. **Erlang/OTP (supervisor trees)** — es el origen real del patrón "Sheriff/Supervisor/Guardián" que ya nombras. Vale la pena leer cómo OTP reinicia procesos hijos automáticamente sin que el padre sepa los detalles — es exactamente tu Policy Engine + Runtime.
4. **Ray** (Anyscale) — implementa el patrón de actores/workers replicados que necesitas para tu idea de "fotocopia del mismo code" (ver siguiente sección).
5. **seL4** — si algún día quieres el estándar máximo de "kernel mínimo verificado formalmente", es la referencia académica de microkernel más citada que existe; no es práctico copiarlo, pero es la vara con la que se mide "qué tan pequeño puede ser un kernel de verdad".

## Sobre tu idea de auto-replicación (fotocopia, no agentes fantasma)

Esto que pides ya tiene nombre en ingeniería de sistemas — y de hecho **ya está en tu propio documento** (línea ~11685, "la clave: espejo, pero no clones ciegos"): se llama **Actor Model con inyección de rol por contrato**. La regla es exactamente la que describes: el código que se replica es **idéntico byte por byte**; lo único que cambia entre una copia y otra es el **contrato de tarea** (`TASK CONTRACT`) que recibe al arrancar — nunca un prompt que "invente" quién es.

Ejemplos reales de este patrón, listos para usar sin escribirlo desde cero:

1. **Ray Actors** — creas N instancias de la misma clase Python; cada una recibe parámetros distintos al construirse, no un prompt.
2. **Kubernetes ReplicaSet/Job con `parallelism: N`** — la forma más probada de "misma imagen de contenedor, N copias, cada una con variables de entorno distintas".
3. **Erlang/OTP `supervisor:start_child/2`** — arranca hijos idénticos bajo un supervisor que los reinicia si mueren, sin que el hijo "decida" quién es.
4. **Python `concurrent.futures.ProcessPoolExecutor` / `multiprocessing.Pool`** — la versión más simple posible si aún no necesitas distribuirlo entre máquinas.
5. **Celery workers** — si ya vas a usar colas de tareas (que además necesitas para tu Scheduler), sus workers son precisamente copias idénticas del mismo código, diferenciadas solo por la tarea que consumen de la cola.

**Confirmación directa a tu pregunta final:** tus documentos **sí cubren la base central del core kernel** (las 8 primitivas + la filosofía correcta de microkernel + el patrón de réplica por contrato ya está mencionado). Lo que falta no es arquitectura nueva — son **4 detalles de robustez dentro de las primitivas que ya tienes** (idempotencia, deadlines, un validador de contrato explícito, y concurrencia segura para cuando varias réplicas escriban al State Manager al mismo tiempo), que es exactamente lo que suele salir en una auditoría de este tipo de sistemas antes de ponerlos en producción real.



Sí existen — y hay dos que se parecen sorprendentemente en escala y estructura al "Mythos 40 pasos" de Fables. No vas a encontrar uno que calce al 100%, pero puedes armar el 80% del esqueleto tomando piezas de 3-4 repos reales en vez de escribir las 12-20k LOC desde cero.

## Los dos "root" más parecidos en escala y forma

**1. Sakana AI — "The AI Scientist"** (`github.com/SakanaAI/AI-Scientist`)
Es el que más se parece en *cantidad de fases y espíritu*: automatiza el ciclo completo de investigación científica — generación de ideas, revisión de literatura, diseño de experimentos, ejecución, escritura del paper, y **una fase de revisión por pares automatizada que critica y rechaza su propio trabajo** (equivalente casi literal a tu FASE 4 de Validación y al CRITIC SWARM del paso 20). Decenas de miles de líneas de código, en Python, con fases claramente separadas en carpetas — es de los pocos repos donde vas a encontrar algo tan largo y modular como lo que describes.

**2. CodiumAI — AlphaCodium** (`github.com/Codium-ai/AlphaCodium`)
Menos líneas que el anterior, pero es la implementación open source más citada del concepto que ustedes llaman "flow engineering" — que es exactamente lo que Fables llama MYTHOS: **no es prompting, es un flujo de pasos obligatorios** (auto-reflexión del problema → generar y rankear soluciones candidatas → generar tests adicionales → iterar código contra esos tests → corregir). Encaja casi 1 a 1 con tus fases 3 y 4 (Exploración + Validación).

## Mapa: qué fase de Mythos toma piezas de cuál repo

| Grupo de pasos Mythos (tus docs) | Repo real que ya lo implementa | Qué extraer |
|---|---|---|
| Pasos 1-10 (comprensión, framing, descomposición) | **DSPy** (Stanford) | Sus "Signatures" y módulos `ChainOfThought`/`ProgramOfThought` — convierten cada paso en una función tipada, no en texto de prompt |
| Pasos 11-20 (hipótesis múltiples, reasoning swarm, critic swarm) | **Tree of Thoughts (ToT)** + **Mixture-of-Agents** (Together AI, `github.com/togethercomputer/MoA`) | ToT para generar y podar ramas de hipótesis; MoA para el patrón exacto "varios proponentes en paralelo → un agregador" |
| Pasos 21-30 (auto-reflexión, simulación, memoria corto/largo plazo) | **Reflexion** (`github.com/noahshinn/reflexion`) + **Voyager** (NVIDIA/MineDojo) | Reflexion tiene literalmente el bucle self-reflection→memoria episódica→reintento; Voyager tiene la "librería de skills" que se guarda como memoria de largo plazo reutilizable |
| Pasos 31-40 (decisión, ranking, fusión, síntesis final) | **AlphaCodium** + **Mixture-of-Agents** (capa agregadora) | El ranking de soluciones candidatas de AlphaCodium + el paso final de fusión de MoA |
| Todo el pipeline completo como referencia de escala | **Sakana AI-Scientist** | La forma de organizar carpetas por fase y el paso de "auto-revisión que puede rechazar el propio trabajo" |

## Cómo armarlo sin escribir 12-20k LOC desde cero

1. Usa **Sakana AI-Scientist** como plantilla de *organización de carpetas por fase* (no copies su dominio científico, copia su esqueleto de directorios).
2. Reemplaza su fase de "diseño de experimentos" por el flujo de **AlphaCodium** (generar→testear→corregir), que es más relevante si tu output final es código.
3. Inserta **DSPy** como el motor que convierte cada paso en un módulo verificable, en vez de texto de prompt suelto — esto resuelve directamente tu preocupación de "aquí no hay prompt, solo DSL/schema".
4. Cuelga **Reflexion** en los pasos de auto-crítica, y **Mixture-of-Agents** en los pasos donde necesitas que varias hipótesis compitan y se fusionen.
5. Todo esto entra como **capacidades** dentro de tu `extension-kernel/`, nunca como el propio Kernel TEAM — el Kernel TEAM solo decide cuándo llamar a cada uno de estos módulos, con el `classifier-scheduler` eligiendo según tu score de complejidad, tal como ya definiste.

Con estos 5 repos combinados ya tienes, de forma realista, entre el 60% y 80% del código de "Mythos 40 pasos" escrito y probado por otros — lo que te toca escribir de cero es principalmente el **cableado** (las conexiones entre estas piezas y tu State Manager/Registry), que es justo el trabajo que tu Kernel TEAM está diseñado para hacer con poco código.



He confirmado un dato importante para tu pregunta de Grok: **Grok Build (el agente de código de xAI) se abrió como open source en julio de 2026, bajo Apache 2.0**, en `github.com/xai-org/grok-build` — un workspace en Rust con el bucle del agente, la capa de herramientas (editar archivos, ejecutar shell), la UI de terminal, un sistema de skills, y capacidad de lanzar hasta 8 sub-agentes en *git worktrees* aislados. Esto sí lo puedes "podar" de verdad, con código real. (Dato relevante para tu última pregunta: en julio-agosto 2026 se descubrió que Grok Build subía silenciosamente repos completos, claves SSH y credenciales a un bucket de Google Cloud sin consentimiento — vuelvo a esto en la lista de criterios de abajo, porque es el ejemplo perfecto de "basura" que puede venir escondida dentro de un agente que funciona muy bien.)

## Árbol de decisión: ¿dónde va una pieza nueva?

## La regla de las tres preguntas (para "capa de objetivos" y "procesamiento de tareas nuevas")

Aplícale esto a cada pieza nueva que quieras agregar:

1. **¿Da siempre el mismo resultado con el mismo input, sin necesitar juicio?** → Es una **capacidad**. Va a `extension-kernel/capability-registry/`.
2. **¿Es una secuencia fija de pasos que usa varias capacidades para llegar a un objetivo?** → Es un **workflow**. Va a `multi-workflow-engine/instances/workflow-N/`.
3. **¿Necesita razonar, decidir con juicio, o mantiene su propio modelo/memoria que no quieres desmontar?** → Es un **agente de pool**. Va a `execution-engine-pool/agent-fleet-parallelism/`.

Con esa regla, tus dos ejemplos ya tienen casa exacta en tu propio árbol (no necesitas inventar carpetas nuevas):

- **"Capa de objetivos"** → ya existe: `kernel-principal/reasoning-kernel/goal-dual-driver/`. Ahí defines el objetivo primario y los secundarios (exactamente los pasos 1-2 de tu documento "35 pasos": *fijar GOAL primario / fijar GOALs secundarios*). No es una capa nueva, es llenar una carpeta que ya tenías vacía.
- **"Procesamiento de tareas nuevas"** → se reparte en dos lugares que también ya existen: `input-layer/reception/` (la entrada cruda) → `execution-orchestration/task-generation/` (la convierte en una tarea formal con esquema). El puente entre ambas es `definition-registry/task-definition/`, que define qué campos debe tener una "tarea válida" antes de que el kernel la acepte.

## Qué va exactamente en `extension-kernel/` (tus "plugins")

Piensa en esta carpeta como **drivers de sistema operativo**, no como herramientas que el LLM "elige usar". Cada subcarpeta que ya tienes cumple un rol muy específico:

- **`capability-registry/`** — el catálogo: qué capacidades existen, sin importar de qué repo vinieron.
- **`capability-passport/`** — la ficha de cada capacidad: licencia, huella (fingerprint), fuente de origen, versión. Esto es literalmente la "trazabilidad completa" que ya definiste en tu SDPA.
- **`abi-mount/`** — el contrato técnico (el "puerto" del patrón Ports & Adapters): la firma exacta que el kernel espera, sin importar el lenguaje de origen.
- **`mount-guard/`** — el portero: verifica el pasaporte y el contrato antes de dejar que la capacidad se monte. Aquí es donde deberías correr el chequeo de seguridad que menciono abajo para el caso de Grok Build.
- **`native-learning/`** — registra qué capacidades han sido confiables con el tiempo (esto es lo que en tus documentos llamas "el kernel aprende qué componentes son fiables").

**Regla dura:** nada en `extension-kernel/` debería importar directamente el código de un repo externo. Solo importa el `abi-mount` (el contrato). El código extraído vive en un módulo separado que el `abi-mount` envuelve — así el día que reemplaces esa pieza, el kernel no se entera.

## Qué va en un `workflow` — y cómo el kernel elige entre varios

Un workflow (`multi-workflow-engine/instances/workflow-N/`) es una **receta**: un DAG en `yaml-dag/` que dice "primero llama a esta capacidad, luego a esta otra, si falla usa este fallback". Nunca contiene razonamiento propio — cuando llega a un punto donde de verdad hay que decidir con juicio, hace una llamada hacia `reasoning-kernel/decision-on-demand/` y espera la respuesta como cualquier otra capacidad.

Cómo decide el kernel **cuál workflow usar** para una tarea nueva:

1. La tarea entra por `input-layer/` con su ficha de `task-definition/`.
2. `execution-orchestration/classifier-scheduler/` calcula un score (el mismo tipo de fórmula que ya tenías: dependencias, ambigüedad, riesgo).
3. Con ese score, `reasoning-kernel/expert-panel-router/` compara la tarea contra la lista de workflows ya registrados en `workflow-definition/`. Si hay un match con alta confianza (score por encima de tu umbral), **ejecuta ese workflow directamente — sin llamar al LLM**. Esto es el 90% determinista que quieres.
4. Solo si **ningún workflow existente encaja bien**, `consensus-trigger/` llama al LLM para que sintetice uno nuevo sobre la marcha (o para que elija entre dos candidatos ambiguos). Esta es la única puerta legítima donde el razonamiento probabilístico entra al sistema.

## Dónde va el sistema Mythos/EURS/DRE de Fables

Como ya vimos: no es una capa, es **contenido versionado que vive dentro de `decision-on-demand/`**, no código de control. Concretamente:

- Guárdalo como archivos de plantilla (`decision-on-demand/prompts/mythos_40.md`, `eurs_standard.md`, `eurs_turbo.md`, `dre_by_score.md`), no como lógica hardcodeada.
- El `classifier-scheduler` elige **cuál plantilla usar** según el score de complejidad (exactamente tus niveles LOW/MEDIUM/HIGH/EXTREME) — así tu propio código, no el LLM, decide si vale la pena gastar 40 pasos de razonamiento o solo 9.
- Nunca dejes que el propio Mythos decida cuándo usarse a sí mismo — esa decisión es del kernel determinista, no del prompt.

## Lista: cómo buscar y qué extraer para nutrir el kernel

**Metodología de búsqueda (repite por cada capacidad que te falte):**
1. Busca por la **responsabilidad única**, no por el nombre del proyecto: "browser automation library", "DAG scheduler python", "state machine library", no "quiero como n8n".
2. Filtra por **licencia permisiva primero** (MIT/Apache-2.0/BSD) — evita AGPL/GPL si no quieres obligaciones de licencia que se propaguen a tu propio kernel.
3. Revisa **actividad reciente** (commits últimos 3 meses) y **tamaño del árbol de dependencias transitivas** — entre más dependencias arrastra, más difícil de aislar limpiamente.
4. Busca si el proyecto ya expone una **interfaz pública clara** (API/CLI documentada) — si no la tiene, vas a tener que escribirla tú, lo cual encarece la extracción.
5. Revisa **issues cerrados por seguridad** en su repo — es la señal más barata de si el proyecto tiene historial de fugas de datos, como pasó con Grok Build.

**Categorías concretas que probablemente aún te faltan, con qué buscar:**
- Automatización de navegador → "Playwright" / "Puppeteer" (para tu `browser-engine`)
- Extracción de PDFs/documentos → "pdf.js" / "PyMuPDF" / "unstructured.io"
- Programación de tareas (cron interno) → "APScheduler"
- Motor de reglas para el Sheriff → "durable_rules" / "Zen Engine (GoRules)"
- Grafo de memoria/conocimiento → "Graphiti" (temporal knowledge graph, mencionado en tus propios documentos)
- Sandbox de ejecución aislado → "E2B" / "gVisor" / "Firecracker microVMs"

## Cómo podarías Grok Build (ejemplo real, con el repo que ya existe)

**Te quedas con (el "cuerpo"):**
- La capa de herramientas: lectura/edición de archivos y ejecución de shell — va directo a `extension-kernel/capability-registry/`.
- El mecanismo de sub-agentes en *git worktrees* aislados — es prácticamente idéntico a lo que necesitas en `execution-engine-pool/worktree-isolation/`, que ya tienes como carpeta en tu árbol.
- La UI de terminal, si te sirve — es cosmética, bajo riesgo.

**Le cortas la cabeza (descartas):**
- El bucle del agente que decide qué herramienta llamar a continuación — eso es exactamente el razonamiento que tu `reasoning-kernel` ya hace; si lo dejas, tendrías dos cerebros compitiendo.
- Cualquier canal de red que el bucle abra por su cuenta — y aquí es donde el incidente real importa: **antes de montar nada de Grok Build, tu `mount-guard` debe correr en un sandbox sin salida a internet y auditar cada conexión saliente**, porque ese proyecto específico ya demostró que puede enviar datos a un bucket propio sin avisar.

## Parámetros para decidir "pool" en vez de "extracción" (para no adquirir basura)

Usa esto como un scorecard antes de aceptar un agente completo como miembro del pool en paralelo:

1. **Aislamiento real posible** — ¿puede correr en un contenedor/sandbox sin acceso directo a tu filesystem o secretos?
2. **Contrato de entrada/salida claro** — ¿tiene una API o CLI estable que puedas tratar como caja negra, sin necesitar leer su código interno?
3. **Comportamiento de red auditado** — ¿sabes exactamente a dónde llama y qué envía? (el caso Grok Build es la advertencia exacta aquí)
4. **Licencia compatible** con lo que planeas hacer con el resultado (comercial o no).
5. **Costo por llamada** — latencia y tokens/cómputo que consume cada vez que lo invocas.
6. **Reproducibilidad** — ¿dado el mismo input, produce resultados consistentes, o es tan errático que no puedes confiar en su output para una decisión automática?
7. **No redundante** — ¿ya tienes otro agente en el pool que cubre la misma capacidad? Si sí, es candidato a descartar, no a sumar.
8. **Observabilidad exportable** — ¿puedes sacarle logs/trazas hacia tu propia capa de `observability/`, o es una caja completamente opaca?
9. **Modo de fallo limpio** — si falla, ¿lo hace de forma ruidosa y clara, o se cuelga/produce basura silenciosa que contamina el resultado agregado?
10. **Procedencia confiable** — mantenedor activo, sin historial de incidentes de seguridad no resueltos.

Si una pieza falla en 3 o más de estos puntos, es mejor **extraer solo la parte que necesitas** (método de poda) en vez de aceptarla completa como agente de pool — menos superficie de riesgo, aunque cueste más trabajo de ingeniería inicial.


Voy a revisar los documentos que subiste para entender bien tu diseño antes de armar las capas.

He revisado los 10 documentos. Tienen mucha coherencia entre sí — el "TEAM Kernel" que diseñaste con Fables, el SDPA de 7/12 capas, y el árbol de carpetas de YAIWES son, en el fondo, **la misma idea contada tres veces con vocabulario distinto**. Eso es bueno: significa que no tienes que reconciliar tres arquitecturas, solo etiquetar una vez y mapear tus carpetas reales a ella.

## 1. El mapa de 5 fases, aplicado a TU árbol real (no uno inventado)

**Nota importante sobre `execution-engine-pool/adapter-layer/` [PARCIAL] y `auxiliary-role-agents/` [STUBS]:** esas dos carpetas son exactamente la **Fase 4** de tu propio diagrama (el pool de kernels A/B/C que se agregan). Que estén marcadas parcial/stub en tu árbol confirma lo que sospecho de la auditoría: **el kernel de decisión de Fase 2 probablemente sí está bastante completo (tienes `decision-on-demand`, `expert-panel-router`, `consensus-trigger`), pero el pool de Fase 4 que debería consumir esas decisiones no está terminado** — por eso "el kernel está incompleto": no es que falte razonamiento, es que falta el tejido que conecta el kernel con los motores paralelos.

## 2. Cómo debería funcionar la parte de decisiones del kernel — y cómo "podar" segmentos de otro kernel

Lo que Fables te explicó tiene nombre real en ingeniería de software — no es una técnica exclusiva de tu proyecto, y eso es una ventaja: puedes buscar documentación real en vez de depender de que alguien te la vuelva a explicar.

**Los 3 patrones exactos que Fables estaba describiendo (búscalos así, tal cual, para encontrar más material):**

1. **Anti-Corruption Layer (ACL)** — patrón de Domain-Driven Design. Es literalmente "usa una pieza de un sistema ajeno sin dejar que su forma de pensar contamine la tuya". Es el nombre correcto de lo que en tu documento se describe como "extraer capacidades sin copiar el razonamiento".
2. **Ports & Adapters / Arquitectura Hexagonal** — define un contrato (puerto) que tu kernel entiende, y un adaptador que traduce ese contrato al código ajeno. Así el kernel nunca sabe que "por dentro" hay Playwright o n8n — solo ve `browser.click()`.
3. **Strangler Fig Pattern** — la técnica para reemplazar gradualmente un sistema grande sin reescribirlo de golpe: envuelves lo viejo con el adaptador, migras pieza por pieza, y al final "estrangulas" (eliminas) el original. Es exactamente el "Transformers que se integran piezas" que mencionas.

**Método concreto para podar un segmento de kernel ajeno (paso a paso, sin necesitar a Fables):**

1. **Localiza la carpeta, no el repo completo.** En el repo de origen busca las carpetas que correspondan a *una sola responsabilidad* — igual que hiciste con n8n en tu documento (`workflow/`, `nodes/`, `execution/`, `triggers/`). Si una carpeta mezcla razonamiento y ejecución, es señal de que no es un buen candidato para extraer aún.
2. **Separa "decide" de "hace".** Dentro de esa carpeta, busca las funciones que **deciden qué hacer a continuación** (esas se descartan — es lo que tu propio kernel ya hace) frente a las que **ejecutan una acción concreta** (esas sí se quedan). En Temporal, por ejemplo, el 100% de lo que te interesa es "hace" (durabilidad); no tiene nada de "decide" que puedas confundir con razonamiento, por eso es un buen primer trasplante — bajo riesgo.
3. **Escribe el puerto antes de tocar el código ajeno.** Define la interfaz que tu TEAM Kernel espera (ej. `execute(action) -> result`), completamente independiente del código de origen.
4. **Escribe el adaptador.** Aquí sí entra el código extraído (transpilado o llamado vía subproceso/FFI si el lenguaje no coincide) — su única función es traducir tu puerto a las llamadas internas del proyecto de origen.
5. **El kernel nunca importa el proyecto de origen directamente** — solo importa el puerto. Así, si mañana cambias Playwright por otra librería de navegador, tu kernel no se entera.
6. **Verifica con el mismo criterio que ya tienes en tu SDPA:** ¿el segmento extraído pasa por Simulation/Sandbox antes de tocar el kernel real? Si sí, ya tienes tu propio "Verification Engine" haciendo justo ese trabajo de guardián — no necesitas inventarlo de nuevo.

**Lo mínimo que el kernel de decisión (Fase 2) debe cubrir, para que la auditoría no lo marque incompleto** (esto complementa lo que ya tienes en `reasoning-kernel/`):

- `decision-on-demand` ✅ ya lo tienes — verifica que **nunca** llame al LLM sin que antes pase por `expert-panel-router`.
- Un **registro de contratos** por segmento extraído (qué puerto expone, qué garantiza, qué versión) — esto es lo que le falta a la mayoría de kernels caseros y es la causa número uno de "incompleto" en auditorías: nadie versiona los adaptadores.
- Una **política de fallback determinista** — si el segmento extraído falla, ¿qué hace el kernel? (reintenta, usa otro segmento equivalente, o escala a humano) — esto debería vivir en `resource-governance/circuit-breaker/`, que ya está en tu árbol pero probablemente vacío.
- **Idempotencia** — que ejecutar la misma decisión dos veces (por un reintento) no duplique efectos. Es el problema más común al fusionar motores de distintos orígenes.

Cuando tengas la auditoría, la pregunta más útil que puedes hacerle a quien te la revise (o a mí) es: **"¿qué carpetas de `reasoning-kernel/` tienen función pero no tienen puerto/adaptador documentado?"** — esas son exactamente los segmentos a los que les falta el paso 3-4 de arriba.





## 1. Las otras nombres/capas que faltan en tu captura

En la pantalla donde se corta ("Orchestrator", "Agent Framework", "Cognitive Layer"...), los términos que la industria usa para nombrar esa "capa externa de código encima del LLM" son, además de **Orchestrator**:

- **Agent Framework** (el más común en la comunidad, ej. LangChain, CrewAI)
- **Cognitive Layer** (más usado en papers académicos)
- **Control Plane** (término tomado de infraestructura/redes — es como Kubernetes llama a su capa de decisiones)
- **Agent Runtime** (como lo llama Anthropic/OpenAI para el proceso que ejecuta el bucle)

Tu stack de la imagen 3 (MYTHOS → FSM → ROUTER → SHERIFF → SENTINEL → VERIFIER → CRITIC → JUDGE → POLICY ENGINE → PYDANTICAI → RETRY ENGINE → LLM) **ya es, en sí mismo, un "Control Plane"** — cada nombre ahí es una función real que existe en librerías reales, aunque con nombre distinto.

## 2. Dónde va la "cadena de 35 pasos" (imágenes 7-8)

Esa cadena **no es una capa de control** — vive **dentro del LLM**, en el nodo final de tu stack (donde dice "LLM"). Es una plantilla de razonamiento inyectada en el prompt para forzar al modelo a verbalizar pasos antes de responder. No es determinista (nada te garantiza que el modelo realmente siga los 35 pasos en orden — solo que *diga* que los siguió), así que su lugar correcto en tu diagrama de razonamiento vs. control es el lado del 10% probabilístico, no el 90% de código.

**5 alternativas open source para implementarla de forma más robusta que "pegarla en el prompt":**
1. **DSPy** (Stanford) — compila y *optimiza* cadenas de razonamiento como programas, no como texto fijo.
2. **LangGraph** — convierte cada uno de tus 35 pasos en un nodo real de un grafo con estado, en vez de una sugerencia dentro del texto.
3. **Guidance** (Microsoft) — generación *restringida* paso a paso, obliga al modelo a completar cada campo en el orden que definas.
4. **Instructor** — fuerza salida estructurada (Pydantic) en cada paso, para poder verificar que el paso 14 realmente ocurrió.
5. **LMQL** — lenguaje de consulta que entrelaza control de flujo de Python con generación del modelo, ideal para forzar secuencias como la tuya.

## 3. Sobre "OpenMythos" (Prelude → Recurrent Block → Coda)

Esto vale la pena aclararlo con precisión: esa estructura de tres partes **no es una invención del documento — es una copia casi literal de una arquitectura de modelo real**, llamada **"Recurrent Depth" / Huginn** (Geiping et al., 2025, Universidad de Maryland), código abierto en `github.com/seal-rg/recurrent-pretraining` y pesos en `huggingface.co/tomg-group-umd/huginn-0125`.

La diferencia importante: en el paper real, el "Prelude/Recurrent/Coda" ocurre **dentro de los pesos del modelo durante el entrenamiento** — el modelo literalmente repite un bloque de la red neuronal en espacio latente antes de decodificar texto. **No es algo que puedas montar como capa de prompt sobre un LLM ya entrenado** — necesitarías entrenar tu propio modelo desde cero para tenerlo de verdad. Si tu documento lo presenta como una técnica de orquestación de prompts, es una mala interpretación del concepto.

**5 alternativas open source que sí puedes usar sobre un LLM ya entrenado (el equivalente práctico, a nivel de agente, no de pesos):**
1. **Self-Refine** (implementación OSS del paper) — bucle iterativo de generar→criticar→regenerar.
2. **Reflexion** — igual, pero guarda la autocrítica en memoria episódica entre intentos.
3. **Tree of Thoughts (ToT)** — explora varias ramas de razonamiento y poda las peores.
4. **Graph of Thoughts (GoT)** — generaliza ToT a un grafo, permite fusionar ramas.
5. **LangGraph con un ciclo condicional** — la forma más simple: un mismo subgrafo se llama N veces con una condición de salida, imitando el "recurrent block" sin necesitar entrenar nada.

## 4. Complementos open source para cada capa que ya nombraste

| Tu capa | Qué hace | Opciones open source |
|---|---|---|
| FSM | Máquina de estados | `transitions` (Python), XState (JS/TS) |
| Router | Enruta la petición | semantic-router, RouteLLM, NeMo Guardrails (topical rails) |
| Sheriff / Policy Engine | Aplica reglas duras | Open Policy Agent (OPA), Cerbos, Casbin |
| Sentinel | Vigila anomalías/contenido | Guardrails AI, NeMo Guardrails, Llama Guard, Microsoft Presidio |
| Verifier | Valida output vs. spec | PydanticAI (ya la tienes), Guardrails AI, `jsonschema` |
| Critic | Crítica adversarial | Self-Refine, Reflexion, CRITIC (tool-augmented) |
| Judge | Elige entre alternativas | TruLens, DeepEval, Ragas, Prometheus (modelo juez open source) |
| Retry Engine | Reintentos | Tenacity, `backoff`, Stamina |

## Lista enumerada — componentes open source para completar el kernel (8–12 puntos + 5 adicionales)

1. **transitions** (Python) o **XState** — máquina de estados (FSM)
2. **semantic-router** o **RouteLLM** — enrutador de intención/modelo
3. **Open Policy Agent (OPA)** o **Casbin** — Sheriff/Policy Engine
4. **Guardrails AI** o **NeMo Guardrails** — Sentinel (detección de anomalías/contenido)
5. **PydanticAI** — Verifier (validación de esquemas)
6. **Self-Refine** o **Reflexion** — Critic (crítica adversarial iterativa)
7. **Prometheus** o **TruLens/DeepEval** — Judge (evaluación entre alternativas)
8. **Tenacity** o **Stamina** — Retry Engine
9. **LangGraph** — FSM + orquestador de pasos con estado persistente (une varias capas de arriba en una sola)
10. **DSPy** — compilador/optimizador de cadenas de razonamiento (reemplaza prompts de "35 pasos" fijos)
11. **Letta (MemGPT)** o **Mem0** — memoria de largo plazo persistente del kernel
12. **Temporal** o **Dagu** — durabilidad/checkpoint (sobrevive caídas a mitad del pipeline)
13. **Langfuse** — observabilidad y trazabilidad de cada paso del kernel (open source, alternativa a LangSmith)
14. **E2B** o sandbox con **gVisor/Firecracker** — ejecución segura del código que el agente genera
15. **LiteLLM (proxy)** — control de costo, rate-limit y enrutamiento entre múltiples LLMs (Kimi K2, Claude, GPT, etc.)


## Recomendaciones open source, mapeadas a cada mecanismo específico de OpenClaw/Hermes

No hay un solo proyecto que replique las dos cosas completas — pero cada pieza que discutimos (identidad, memoria, delegación, canal múltiple, heartbeat, skills instalables) tiene un equivalente open source maduro. Te los doy por componente, con la justificación de por qué ese y no otro:

| Componente de OpenClaw/Hermes | Qué hace | Recomiendo | Por qué |
|---|---|---|---|
| Identidad (`SOUL.md`) + memoria propia (`memory_store.db`) | Persona persistente + hechos recordables | **Letta** (ex MemGPT) | Tiene el patrón nativo: "core memory" = bloque de persona editable por el propio agente, "archival memory" = base vectorial buscable. Es literalmente la misma arquitectura, no una aproximación. |
| Memoria conversacional más ligera (si Letta te parece pesado) | Recuerdo episódico entre sesiones | **Mem0** o **Zep** | Se enchufan como capa de memoria a *cualquier* loop de agente sin adoptar todo un framework. Zep además da un grafo de conocimiento temporal, útil si quieres razonar sobre *cuándo* pasó algo, no solo *qué* pasó. |
| Delegación entre profiles ("¿lo hago yo o se lo paso a otro?") | Multi-agente con roles y paso de mensajes | **CrewAI** o **AutoGen/AG2** | Ambos están diseñados exactamente para eso: agentes con rol fijo que se pasan tareas entre sí. CrewAI es más simple de declarar (roles + tareas); AutoGen da más control fino sobre el protocolo de conversación entre agentes. |
| Razonamiento con estado durable y reintentos (el "¿qué pasa si se cae a mitad del ciclo?") | Grafo de pasos con checkpoint | **LangGraph** | Cada nodo del grafo es un paso de razonamiento, y trae *checkpointer* nativo — puedes pausar, inspeccionar y retomar exactamente donde se quedó, sin necesitar Temporal si tu escala no lo justifica todavía. |
| Gateway multi-canal (WhatsApp, Telegram, Slack, Discord → un mismo agente) | Enruta mensajes de distintos canales a la misma sesión | **n8n** | Tiene triggers nativos para cada canal y un nodo de "AI Agent" — replicas el Gateway de OpenClaw de forma visual, sin escribir el enrutador tú mismo. |
| Skills instalables en tiempo real (ClawHub) | El agente amplía su propio repertorio de herramientas a mitad de tarea | **Protocolo MCP + un registro de servidores MCP** | Es el estándar abierto equivalente: el agente descubre e invoca nuevas herramientas sin que tú las hayas precableado. Es más portable que un marketplace propietario porque cualquier cliente compatible con MCP (incluido Claude) lo entiende. |
| Heartbeat / iniciativa propia sin mensaje del usuario | El agente se despierta solo | **APScheduler** (si es simple) o **cron + Temporal/Dagu** por debajo (si necesita sobrevivir caídas) | APScheduler es suficiente para "revisa esto cada hora"; si esa tarea es crítica y larga, envolverla en Temporal le da la durabilidad que discutimos antes. |
| Framework "todo en uno" más cercano al espíritu completo | Memoria + equipos de agentes + herramientas + conocimiento, en un solo paquete | **Agno** (antes Phidata) | Es el que más se acerca a "OpenClaw/Hermes pero genérico": trae memoria persistente, *teams* de agentes colaborando, RAG, y está pensado para producción — menos ensamblaje manual que combinar Letta+CrewAI+n8n por separado. |

## Receta sugerida según qué quieras replicar

**Justificación de por qué esta combinación y no otra:**

- **n8n arriba** porque el mensaje siempre entra por un canal externo primero — es el rol que cumple el Gateway en OpenClaw.
- **CrewAI/AutoGen en medio** porque ahí es donde se decide "quién de mis agentes atiende esto" — el mismo punto de bifurcación que vimos en el ciclo de Hermes.
- **Letta debajo de eso** porque cada agente de la capa anterior necesita su propia identidad y memoria persistente — si no la tiene, cada delegación pierde contexto.
- **Temporal/Dagu como base opcional** — solo lo agregas si alguna de esas delegaciones es una tarea larga que no puede perderse si el servidor se reinicia; para la mayoría de casos personales/pequeños, no lo necesitas todavía.

Si tu objetivo es algo simple (un agente, una identidad, memoria persistente), con **solo Letta** ya replicas el 80% de lo interesante de Hermes sin montar las otras tres capas.





## 5. Qué existe y qué falta

| Área | Evidencia actual | Estado | Falta demostrable |
|---|---|---:|---|
| Árbol PLAN_100 | Scaffold materializado | PARCIAL | Sustituir ESQ por cuerpos reales y probarlos |
| Hot path de programación | `extensions/wordflow/engine/code_path_runner.py` | REAL | Mantener hasta paridad de tests |
| Pipeline de programación | `programming_pipeline.py` y módulos asociados | REAL/PARCIAL | Cadena integral verificada |
| Kernel Wordflow | `extensions/wordflow_kernel/` | PARCIAL | Adaptadores reales y pruebas E2E |
| Router de inteligencia | `gateway/intelligence.py`, `router_http.py` | PARCIAL | Providers reales y failover probado |
| Motor modular p01–p12 | Declarado/documentado | FALTANTE | Archivos ejecutables p01–p12 |
| OpenClaw/Hermes auxiliares | Archivos stub | ESQ | Adaptadores funcionales |
| Índice de símbolos | Referenciado | FALTANTE | Export Markdown verificable |
| Esquemas por etapa | Parciales/globales | FALTANTE | Contratos input/output por etapa |
| Índice test→assert | No demostrado | FALTANTE | Trazabilidad requisito→test→assert |
| Evidencia CI en observabilidad | Dispersa | PARCIAL | Ingesta en `trace-history` |
| Estado global persistente | Fragmentado | PARCIAL | Máquina durable única |
| GapRegistry persistente | Parcial | PARCIAL | Persistencia y transición probada |
| FourPassController global | Documentos/piezas | PARCIAL | Controlador único ejecutable |
| Recepción y handoff | Parcial | PARCIAL | Auto-load y handoff verificable |
| Cadena DOC→OUTPUT | No cerrada E2E | FALTANTE | DOC→REQ→CODE→TEST→EVIDENCE→OUTPUT_CONSUMED |
| Historial append-only | Ledger parcial | PARCIAL | Garantía y prueba de inmutabilidad |
| Protección post-verify | No cerrada | PARCIAL | Sin bypass y defaults seguros |

## 6. Veredicto de cuatro pasadas

1. **STRUCTURE:** el árbol objetivo está descrito y materializado, pero contiene referencias y placeholders; no prueba implementación completa.
2. **CONNECTIVITY:** hay puntos de conexión reales, pero quedan catálogos desactualizados, rutas fantasma, dual homes y dependencias externas.
3. **BEHAVIOR:** el hot path es real; no existe evidencia suficiente para afirmar que toda la arquitectura nueva impone el comportamiento declarado.
4. **FORENSIC_CLOSURE:** **FAIL-CLOSED / PARCIAL**. Los PASS de descargas, carpetas o GitHub Actions no cierran los GAPS del runtime.

## 7. Regla de evolución

No mover ni reescribir `extensions/wordflow/engine/code_path_runner.py` hasta alcanzar paridad de imports, contratos, tests y evidencia. La ruta segura es **REUSE → COPY con SHA → ADAPT → TEST → CUTOVER**, manteniendo trazabilidad origen→destino.


---

## 8. Auditoría forense TEAM/SDPA — fuentes, cableado y GAPS

Esta ampliación cruza la arquitectura YAIWES con los documentos TEAM y SDPA aportados. Las pasadas están separadas para conservar trazabilidad:

1. [Auditoría 01 — Estructura](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-01-ESTRUCTURA-XRAY-2026-09-01.md)
2. [Auditoría 02 — Conectividad](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-02-CONECTIVIDAD-XRAY-2026-09-01.md)
3. [Auditoría 03 — Comportamiento](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-03-COMPORTAMIENTO-XRAY-2026-09-01.md)
4. [Auditoría 04 — Cierre y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-04-CIERRE-GAPS-XRAY-2026-09-01.md)

### Fuentes SDPA preservadas

- [SDPA Architecture Document](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/SDPA_Architecture_Document.md)
- [Resumen de la propuesta SDPA](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/RESUMEN-PROPUESTA-SDPA.md)

### Localización del código TEAM

No existe una raíz ejecutable única llamada `Agente TEAM`. La evidencia se distribuye así:

```text
PIPELINE/03_TEAM_KERNEL_PARTE1.md                  diseño TEAM v3
PIPELINE/06_PERFIL_MAESTRO_TEAM_SEALS.md           perfil maestro
PIPELINE/10_KERNEL_THOUGHT_PROTOCOL.md              protocolo de pensamiento
extensions/wordflow_kernel/                         kernel de control real/parcial
extensions/wordflow/                                runtime y hot path real
agente-yaiwes/kernel-principal/                     espejo/scaffold parcial
control-layer/                                      contratos, council y evolution
Agente core kernel Yaiwes principal/                ZIP de componentes; no runtime
```

### Resultado fusionado

- TEAM tiene diseño documental y piezas funcionales, pero no existe como paquete/runtime autónomo completo.
- `extensions/wordflow_kernel/`: 94 Python, 27 tests, base reutilizable.
- `agente-yaiwes/kernel-principal/`: 49 Python, 18 placeholders, 0 tests propios.
- `Agente core kernel Yaiwes principal/`: 502 ZIP; inventario, no kernel instalado.
- OpenClaw y Hermes continúan como stubs.
- Los defaults Fake/Mock demuestran interfaces, no producción.
- SDPA está incompleto: faltan DecisionEngine único, Ask-Consil 12 ejecutable, Merkle State global, AST universal, Inventory unificado, merge semántico y verificación integral.

**Veredicto TEAM/SDPA:** `FAIL-CLOSED / PARCIAL`. No se declara 100% PASS.


---

## 9. Auditoría corregida por cada raíz del Crazy Wall

La auditoría operativa se separa por **raíces**, no por pasadas generales. El punto de entrada actualizado es:

- [Índice maestro — seis raíces YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)

Auditorías enlazadas:

1. [R1 — Desplegar](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R1-DESPLEGAR-XRAY-2026-09-01.md)
2. [R2 — PIPELINE](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R2-PIPELINE-XRAY-2026-09-01.md)
3. [R3 — Método de trabajo](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R3-METODO-TRABAJO-XRAY-2026-09-01.md)
4. [R4 — Refactoria](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R4-REFACTORIA-XRAY-2026-09-01.md)
5. [R5 — YAIWES / Agente TEAM / Kernel](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R5-YAIWES-TEAM-KERNEL-XRAY-2026-09-01.md)
6. [R6 — Wordflow Code](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R6-WORDFLOW-CODE-XRAY-2026-09-01.md)

Los HTML originales utilizados como mapa también quedaron preservados y enlazados desde el índice.
