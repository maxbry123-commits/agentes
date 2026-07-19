---
# UOOS Parte 2 v3.0 — Executor Runtime (RESUMEN)

## Activación

Al leer este documento, el ingeniero ejecutor:
1. Ejecuta BOOT (RT-00..RT-04) → emite respuesta de boot → espera GO
2. Tras GO, ejecuta RT-10..RT-45 nodo por nodo hasta completar
3. RT-90 cierra el proyecto
4. RT-80 recovery en caso de fallo

## Reglas E01-E12 (resumen)

| # | Regla | Resumen |
|---|-------|---------|
| E01 | ejecución_obligatoria | tras GO, ejecutar sin replanificar |
| E02 | preguntas_prohibidas | solo si falta dato en B1-B8 |
| E03 | alcance | ejecutar SOLO nodos del B3 |
| E04 | no_replanificar | el plan ya existe en B1-B8 |
| E05 | escalado | solo por ley violada, contrato incumplible, etc. |
| E06 | modo_ejecutor | no eres consultor ni arquitecto |
| E07 | una_tarea | objetivo único = nodo activo |
| E08 | sin_iniciativa | mejoras → BACKLOG.md, no ejecutar |
| E09 | no_detenerse | solo por fallo irrecuperable o aprobación |
| E10 | duda | buscar en B1-B8 antes de preguntar |
| E11 | congelación_documental | B1/B3/B4 inmutables durante ejecución |
| E12 | comunicación | hablar al Director solo lo crítico |

## Máquina de estados (RT-*)

```
RT-00 BOOT_VERSION
  → RT-01 INTEGRIDAD
  → RT-02 PREFLIGHT
  → RT-03 SKILLS_BOOTSTRAP
  → RT-04 RESUME_CHECK
  → [GO del Director]
  → CICLO POR NODO:
       RT-10 SELECT
       → RT-11 IDEMPOTENCIA → [reutilizar si mismo input] → RT-45
       → RT-12 CAPABILITY
       → RT-13 MEMORIA_IN
       → RT-14 VALIDAR_INPUT → [fail] → RT-80
       → RT-20 EJECUTAR
       → RT-30 TRIBUNAL (6 roles paralelo)
       → RT-31 GOAL_CHECK (LA REGLA QUE FALTABA)
       → RT-40 ARTEFACTOS
       → RT-41 CONSISTENCIA
       → RT-42 AUDITORIA
       → RT-43 MEMORIA_OUT
       → RT-44 AUTOOPTIMIZAR
       → RT-45 ENTREGAR
       → [siguiente nodo → RT-10]
  → RT-90 CIERRE_PROYECTO
Fallo en cualquier RT → RT-80 RECOVERY_GATE
```

## Eventos obligatorios (contrato de observabilidad)

| Evento | Cuándo | Por qué |
|--------|--------|---------|
| boot.version.ok | RT-00 OK | confirmar versión del paquete |
| boot.integrity.ok | RT-01 OK | B1-B8 consistentes |
| boot.preflight.ok | RT-02 OK | entorno listo |
| boot.skills.ok | RT-03 OK | skills cargadas |
| node.selected | RT-10 | elección registrada |
| node.reused | RT-11 (idempotente) | no re-ejecutar |
| node.start | RT-20 | inicio de ejecución |
| node.checkpoint | durante RT-20 | cada iteración |
| node.validate | RT-30 | scores del Tribunal |
| node.goal_gap | RT-31 (gap) | Tribunal OK pero goal incompleto |
| node.artifacts | RT-40 | archivos creados/modificados |
| node.done | RT-45 | nodo completado |
| node.failed | cualquier fallo | con causa raíz |
| loop.delta | cada iter | score_delta medido |
| loop.iter | cada iter | iteración N |
| context.compressed | RT-13 | resumen por presupuesto |
| context.cleared | RT-43 | fin de nodo |
| recovery.start | RT-80 inicio | clasificar causa |
| recovery.restore | RT-80 OK | checkpoint restaurado |
| project.completed | RT-90 | cierre total |

## Comandos del Director (únicos reconocidos)

| Comando | Significado |
|---------|-------------|
| `GO` | iniciar/continuar ejecución |
| `OK` | aprobar entrega, siguiente nodo |
| `FIX <x>` | corregir entrega (cuenta como iter con delta) |
| `PAUSA` | checkpoint + detener |
| `ESTADO` | state.json resumido |
| `SALTAR T-X` | marcar blocked (solo Director) |
| `UNLOCK <doc>` | autorizar modificar B1/B3/B4 |
| `ABORT` | checkpoint + cerrar sin completar |

## Diferencia con Parte 1

| Parte 1 (v2.0) | Parte 2 (v3.0) |
|------------------|------------------|
| **Diseño** (qué hacer) | **Ejecución** (cómo hacerlo) |
| 8 bloques B1-B8 | Runtime RT-00..RT-90 |
| Schemas y planes | Eventos y transiciones |
| Estática | Dinámica (state machine) |
| Define contrato | Ejecuta contrato |

## Boot típico (output esperado)

```
BOOT UOOS: 8/8 OK | versión: 3.0.0 | integridad: OK | preflight: OK
SKILLS: 0 instaladas | MODO: INICIO
ORDEN: T-001_orchestrator → T-002_state → T-003_sandbox → ...
PRÓXIMO: T-001_orchestrator (loop engine con 10 loops L1-L10) risk:alto
→ Esperando GO
```

## Entrega de nodo (output esperado)

```
NODO T-001_orchestrator DONE
[entregable copiable]
EVIDENCIA: §6.4 | VEREDICTO: SHERIFF 100 / CENTINELA 100 / JUEZ 100 / SUPERVISOR 100 / VALIDADOR 95 / VERIFICADOR 100 (avg 99.2) | AUDITORÍA: 0.5s, 0 tokens, 1 intento
→ PRÓXIMO: T-002_state (auto si risk≤medio | esperando OK si risk=alto)
```

## Uso programático

```python
from orchestrator.runtime import RuntimeExecutor, build_state_from_b3, RuntimeState
import json

# cargar B1, B2, B3
with open("B1_PROJECT_MANIFEST.md") as f: b1 = f.read()
with open("B2_state.json") as f: b2 = json.load(f)
# parsear B3 (simplificado)
b3 = {}  # b3_nodos_dsl_dict

state = build_state_from_b3(b1, b2, b3)
executor = RuntimeExecutor(state)

# BOOT
boot = executor.boot()
print(boot)  # {status: boot_ok, modo: INICIO, orden: [...], proximo: T-001}

# esperar GO del Director
go = input("¿GO? ")
if go == "GO":
    # ejecutar nodos
    while True:
        nodo = executor.rt_10_select()
        if nodo is None:
            break
        result = executor.execute_node(nodo, input_data={})
        print(f"{nodo.id}: {result['status']}")
    # cierre
    cierre = executor.rt_90_cierre()
    print(cierre)
```

## Archivo

El runtime vive en `orchestrator/runtime.py` y se complementa con:
- `state.py` (atomic_write_json + hash_goal)
- `sheriff.py` (gates)
- `juez.py` (3 simulaciones)
- `repair.py` (F1-F16)

Tests: `tests/test_runtime.py` (próximamente).

---

**Control de versiones:**
```
v3.0 — 2026-07-13 — Runtime completo. Añadido: boot versión, integridad
       bidireccional, reanudación, eventos obligatorios, congelación B1/B3/B4,
       control de contexto, goal_check post-Tribunal, preflight,
       capability+delegación, orden OSS→LLM, memoria in/out, costes,
       idempotencia, E01-E12, cierre, auditoría, paralelismo con locks,
       consistencia, autooptimización, skills por necesidad.
       Autoridad: Director Max.
```
