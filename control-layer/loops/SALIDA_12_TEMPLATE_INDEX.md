# Salida 12/12 — Plantilla B5 v2 + índice final

## Plantilla
`templates/uoos/B5_loop.yaml` schema_version 2.0

## Índice Loop System (Wordflow)

### Contratos (Fase 1)
- contracts/loop_context.schema.yaml + types.LoopContext
- contracts/loop_state.schema.yaml + StateMachine
- contracts/loop_command.schema.yaml
- contracts/loop_event.schema.yaml
- contracts/detector_result.schema.yaml
- contracts/policy_decision.schema.yaml
- contracts/budget.schema.yaml
- contracts/progress_result.schema.yaml
- contracts/capability_request.schema.yaml
- contracts/memory_plugin.schema.yaml · graph_plugin.schema.yaml
- plugins/base.py (NoOp)

### Engine (Fase 2)
- state_machine.py
- phases.py (9 + Sheriff)
- policy/engine.py + default_policy.yaml
- recovery.py (11 acciones)
- engine.py (LoopEngine)

### Operación (Fase 3 parcial)
- progress.py (evaluator + adaptive)
- budget_governor.py
- risk.py (RiskEngine + HumanGate)

### Diferido (Fase 4–5)
Supervisor · Registry · Lease · Heartbeat · DLQ · Strategy Memory · Result Cache · Replay

## Separación fijada
WORKFLOW → TASK → LOOP RUN → ITERATIONS
Loop = máquina reutilizable (no dueño de agente/proyecto)

## 12/12 CERRADO
