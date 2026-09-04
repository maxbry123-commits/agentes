# 📂 MAPA DE RUTA — BLOQUE 1 DE 4
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
