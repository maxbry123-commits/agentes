# Salida 1/12 — Contratos base congelados

## Entregado
- `contracts/loop_context.schema.yaml`
- `contracts/loop_state.schema.yaml` + transitions
- `contracts/loop_command.schema.yaml`
- `contracts/loop_event.schema.yaml`
- `contracts/types.py` (dataclasses + assert_transition)

## Invariantes clave
- project_id / agent_id inmutables post-CREATED
- goal_id inmutable post-LOCKED
- CLOSED no vuelve a RUNNING
- Engine solo emite eventos (no llama memory/graph)

## Siguiente (2/12)
DetectorResult · PolicyDecision · Budget · ProgressResult
