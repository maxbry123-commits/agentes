# SALIDA W01 — Contratos loop + schemas D1–D10

**Estado: CERRADA 100%**

## A) Loop contracts (`loops/contracts/`)

| Archivo | Rol |
|---------|-----|
| `loop_context.schema.yaml` | run/project/agent/goal/phase/budgets |
| `loop_state.schema.yaml` | FSM 12 estados + transitions |
| `loop_command.schema.yaml` | comandos supervisor |
| `loop_event.schema.yaml` | event sourcing lite |
| `detector_result.schema.yaml` | 13 tipos detector |
| `policy_decision.schema.yaml` | decisión policy DSL |
| `budget.schema.yaml` | tokens/time/iter/cost |
| `progress_result.schema.yaml` | score 0–1 |
| `capability_request.schema.yaml` | router multiagente |
| `memory_plugin.schema.yaml` | interfaz (plugin; memoria full pendiente) |
| `graph_plugin.schema.yaml` | interfaz graph |
| `types.py` | dataclasses + assert_transition |
| `capability.py` | CapabilityRequest runtime |

## B) Project schemas (`schemas/`)

| Archivo | Doc |
|---------|-----|
| `project_manifest.schema.yaml` | D1 |
| `project_state.schema.yaml` | D2 |
| `agent_node.schema.yaml` / `agent.schema.yaml` | D3 |
| `workflow_dag.schema.yaml` / `workflow.schema.yaml` | D4 |
| `council_tribunal.schema.yaml` | D6 |
| `recovery_policy.schema.yaml` | D8 |
| `execution_context.schema.yaml` | runtime |
| `project_docs.yaml` | mapa D1–D10 |
| `validate_project.py` | checker |

## Invariantes W01
1. Contratos loop **congelados** — engine solo consume types
2. Schemas proyecto = fuente declarativa; no runtime state en YAML agente
3. Capability ≠ agent_id hardcode
4. Sin secretos en schemas

## Auditoría
- Inventario completo en branch `workflow/A1-nucleo`
- Sin huecos de contrato base para capa universal

## Siguiente
**W02** — state machine + 9 phases + Sheriff
