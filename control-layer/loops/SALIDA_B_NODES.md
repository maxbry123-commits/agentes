# Salida B/6 — auto-register nodes/*.yaml

## Hecho
- `nodes_loader.py` — discover · parse · register_runtime
- Stub executor por defecto (ok + meta)
- `executor_factory` para inyectar runtime real (temporal/openclaw)
- Fixtures coder + researcher · tests

## Uso
```python
loader = NodesLoader()
adapter = loader.load_project("/path/to/PROJECT")  # lee PROJECT/nodes/*.yaml
eng = LoopEngine(phase_handlers=make_default_handlers(adapter))
```

## Siguiente C/6
Supervisor: persist + metrics default
