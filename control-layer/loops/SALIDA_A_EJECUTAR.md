# Salida A/6 — ejecutar → AgentAdapter

## Hecho
- `phase_handlers.py`: make_ejecutar_handler · plan · validar · make_default_handlers
- `ejecutar` crea CapabilityRequest y `adapter.dispatch`
- Engine acepta `phase_handlers=` (ya existía)
- Tests: dispatch coder + engine close

## Uso
```python
ad = AgentAdapter()
ad.register_runtime(CallableAgent("coder", ["code_generation"], fn))
eng = LoopEngine(phase_handlers=make_default_handlers(ad))
```

## Siguiente B/6
Auto-register desde nodes/*.yaml
