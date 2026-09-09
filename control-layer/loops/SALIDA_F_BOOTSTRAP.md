# Salida F/6 — Boot hydrate + resume

## Hecho
- `bootstrap.py` — PersistenceStore → registry/dlq/contexts
- EventReplayer opcional por run
- `resume_all` continúa activos no terminales
- Test hydrate tras create+run_once

## Uso
```python
boot = Bootstrap("loop_data")
sup, report = boot.hydrate_supervisor()
boot.resume_all(sup, goal_complete=False)
```

## A–F CERRADO → score objetivo ~10 usable
