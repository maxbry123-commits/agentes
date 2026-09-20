# SALIDA W02 — State machine + 9 phases + Sheriff

**Estado: CERRADA 100%**

## Entregables

| Módulo | Path | Función |
|--------|------|--------|
| StateMachine | `loops/state_machine.py` | transitions + invariantes + hash events |
| PhaseRunner | `loops/phases.py` | 9 fases orden fijo |
| Sheriff (loop) | `loops/phases.py::Sheriff` | frena required faltantes/fallidas |
| Sheriff (capa) | `sheriff/gate.py` · `states.py` · `agent_validate.py` | gates DAG/agente |

## FSM (tipos en contracts)
- Transiciones vía `assert_transition` / `can_transition`
- Inmutables: `run_id`, `project_id`, `agent_id`; `goal_id` post-CREATED
- `CLOSED` terminal; REOPEN solo FAILED/ESCALATED → LOCKED
- Eventos con hash chain (`prev_hash`)

## 9 fases (orden estricto)
```
leer_anclas → plan → ejecutar → medir → validar → reparar → evidencia → checkpoint → decidir
```
**Required:** leer_anclas · ejecutar · validar · evidencia · decidir  
**IA allowed:** plan · ejecutar · reparar  
Required skip/fail → `SheriffVerdict.ok=False`

## Sheriff doble
1. **Loop Sheriff** — integridad de fases de una iteración
2. **Capa sheriff/** — gate workflow + validación agent YAML + anti_escalation

## Siguiente
**W03** — Policy DSL + Recovery 11
