---
# INPUT BLOCK — Instrucciones del Director (Max) — acumulativo

Registro literal de todas las instrucciones entregadas por el Director. Acumulativo.

---

## PLANTILLA OFICIAL (Max)

El Director entrega el objetivo en esta plantilla. El Orquestador la parsea y la ejecuta.

```
OBJETIVO: <1 línea, qué querés lograr>
PLANIFICAR: <pasos macro en orden, separados por | o números>
ORGANIZAR: <asignar cada paso a: Orquestador | Router | Sandbox-X | Juez>
TAREAS: <lista atómica, una acción cada una>
METAS: <métricas de éxito, medibles>
PROPÓSITO: <por qué importa, qué habilita>
REFUTACIONES: <3-5 formas en que esto puede fallar>
```

### Ejemplo real (Director)

```
OBJETIVO: "construir API REST de tareas en FastAPI con tests"
LOOP_AGENTES:
  - claude_code → objetivo (escribe el código)
  - mimo_code → verifica (corre tests) + valida (lint/format) + repara (patches)
LOOPS: 10 (1 goal + 3 verify + 3 repair + 3 consensus)
PLANIFICAR:
  1. Goal Lock
  2. Plan consenso
  3. Asignar sandboxes
  4. Claude escribe models/routes/tests
  5. Mimo verifica (pytest)
  6. Mimo repara si falla
  7. Mimo valida (ruff/black/mypy)
  8. Loop repair max 2
  9. Sentinel
  10. Juez 3 simulaciones
ORGANIZAR:
  L1 → Orquestador
  L2 → 3 sandboxes paralelos (consensus)
  L3 → Router
  L4 → Sandbox Claude
  L5-L8 → Sandbox Mimo
  L9 → Sentinel
  L10 → Juez
TAREAS:
  - escribir models.py
  - escribir routes/tasks.py
  - escribir tests/test_tasks.py
  - ejecutar pytest
  - ejecutar ruff/black/mypy
  - persistir baseline
METAS:
  - pytest pasa 100%
  - ruff 0 errores
  - mypy 0 errores
  - coverage >= 80%
PROPÓSITO:
  - habilitar API base para el módulo de tareas del proyecto
  - servir como plantilla para futuros endpoints
REFUTACIONES:
  - R1: Claude puede proponer código que rompe imports
  - R2: Mimo puede entrar en loop infinito reparando
  - R3: tests pueden pasar pero la app crashea en runtime
  - R4: baseline puede no existir en primera ejecución
  - R5: sandbox puede colgarse sin respuesta
```

---

## Bloque 1-8 (sesión anterior — intocados)

Sesión 2026-07-08: reglas de trabajo vigentes, Execution Pipeline DSL v2.0, PIPELINE_MASTER.md, INPUT_BLOCK.md bloques 1-8, execution_pipeline_dsl.py.

---

## Bloque 9 — Arquitectura universal con sandboxes (2026-07-13)

Director: "necesito un orquestador universal para conectar el chat a cualquier agente; cada agente usa su propio sandbox. El orquestador NO toca código interno de los agentes. Implementar 10 goals, 16 pasos de razonamiento, 16 pasos de recuperación. Componentes: DSL, DAG, Sheriff, Sentinel, Juez, Supervisor, Validador, Verificador. Goal Lock + Scope Lock + Loop Engine."

Actualización: diseño completo definido. Estructura:
- /workspace/orchestrator-universal/
  - docs/ (5 MD)
  - orchestrator/ (10 archivos .py)
  - orchestrator/agents/ (3 wrappers)
  - tests/test_mvp.py
  - main.py

10 GOALS definidos en ARCHITECTURE.md §10 GOALS.
16 PASOS DE RAZONAMIENTO R1-R16 en LOOP_ENGINE.md.
16 PASOS DE RECUPERACIÓN F1-F16 en LOOP_ENGINE.md.
Componentes: DSL Engine, DAG Engine, State Machine, Sheriff, Sentinel, Juez, Supervisor, Validador, Verificador, Router.

---

## Bloque 10 — Planificación + Consenso (2026-07-13)

Director: "agregar planificación y consenso al orquestador. Plantilla con objetivo/planificar/organizar/tareas/metas/propósito/refutaciones. 3 modelos proponen plan, Juez elige. Consenso 2-de-3 al final."

Actualización:
- Plantilla oficial definida (arriba).
- 2 nuevos pasos en Loop Engine: R0a (descomponer plan) + R0b (consenso 3 modelos).
- Consenso 2-de-3 implementado en `consensus.py`.
- Juez final también aplica 2-de-3 (no solo el inicial).

---

## Bloque 11 — Mínimo 10 loops + multi-agente (2026-07-13)

Director: "necesito mínimo 10 loops, que puedan involucrar varios agentes. Ejemplo: claude_code objetivo, mimo_code verifica/valida/repara. Cómo se hace. Cuál es el total de código de esto, lo necesito MVP funcional."

Actualización:
- 10 loops definidos en LOOP_ENGINE.md §10 LOOPS.
- Multi-agente: L2 consensus (3 paralelos), L3 asignación, L4-L8 secuencial con paralelo parcial.
- Total código MVP: ~2230 líneas (12 archivos .py).
- Tiempo MVP: 5-7h código + 1-2h tests.
- Orden de entrega: docs → código → tests → main.

---

## Estado de cumplimiento

| Tarea | Estado |
|-------|--------|
| Arquitectura con sandboxes definida | ✓ |
| 10 GOALS documentados | ✓ |
| 10 LOOPS documentados | ✓ |
| 16 Razonamiento documentados | ✓ |
| 16 Recuperación documentados | ✓ |
| Plantilla oficial definida | ✓ |
| Consenso 2-de-3 diseñado | ✓ |
| Multi-agente diseñado | ✓ |
| Código .py MVP escrito | ⏳ en curso |
| Tests MVP escritos | ⏳ |
| Memoria actualizada | ⏳ |

---

STOP
