# SALIDA W08 — runtime_factory

**Estado: CERRADA 100%** (capa universal; bin real = fuera de alcance)

## Path
`loops/runtime_factory.py`

## adapter.id
| id | Comportamiento |
|----|----------------|
| `generic` | entrypoint archivo o stub |
| `stub` | siempre stub ok |
| `temporal` | bin TEMPORAL_BIN / orquestador-temporal; **si falta → stub marked** |
| `openclaw` | OPENCLAW_BIN / openclaw run |
| `hermes` | generic path |

## API
```python
from loops.runtime_factory import build_adapter_from_project, executor_for_spec
ad = build_adapter_from_project("/PROJECT", stub_ok=True)
```

Sin binario no rompe el loop (stub). Binario real = pendiente acordado.

## Siguiente
**W09** — Plantillas D1–D10 + pipeline guía
