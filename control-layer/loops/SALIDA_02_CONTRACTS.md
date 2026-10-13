# Salida 2/12 — Contratos señal / policy / budget / progress

## Entregado
- `detector_result.schema.yaml` — 13 detectors · action_hint · no muta state
- `policy_decision.schema.yaml` — 15 actions incl. HUMAN_GATE
- `budget.schema.yaml` — 4 levels + multi-resource + consumed
- `progress_result.schema.yaml` — score 0-1 + confidence + kinds
- `types.py` actualizado (dataclasses + Budget.exhausted/warning_80)

## Regla
Detectar ≠ decidir. Policy decide. Progress normaliza.

## Siguiente (3/12)
CapabilityRequest · MemoryPlugin · GraphPlugin
