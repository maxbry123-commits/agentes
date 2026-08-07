# Loop Engine (Wordflow control-layer)

Máquina de ejecución **determinista** multiagente/multiproyecto.

```
Control → Router → LoopEngine
              ↓
         LoopContext + StateMachine
              ↓
         9 phases + Sheriff
              ↓
         Detectors → Policy → Recovery
              ↓
         Events → Memory/Graph plugins
```

## Quick use

```python
from loops import LoopEngine
from loops.contracts.types import LoopContext

eng = LoopEngine.with_default_policy()
ctx = LoopContext(run_id="R1", loop_id="L01", project_id="P", agent_id="A",
                  task_id="T", goal_id="G", created_at="...", updated_at="...")
result = eng.run_iteration(ctx, goal_complete=True)
```

## Docs por salida
SALIDA_01..12_*.md en este directorio.
