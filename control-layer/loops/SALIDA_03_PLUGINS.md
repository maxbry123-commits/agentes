# Salida 3/12 — Capability + Plugins

## Entregado
- `capability_request.schema.yaml` + `capability.py`
- `memory_plugin.schema.yaml` — scopes loop|task|agent|project|strategy
- `graph_plugin.schema.yaml` — nodes/edges/query_similar/on_event
- `plugins/base.py` — ABC + NoOpMemoryPlugin + NoOpGraphPlugin

## Regla
Engine emite eventos → plugins consumen. No acoplamiento.

## Siguiente (4/12)
State machine ejecutable + invariantes checker
