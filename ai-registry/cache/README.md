# Caché del AI Registry

## Política (v0.1)

| tipo de entry | TTL | invalidación |
|---------------|-----|--------------|
| `agent_card`   | 5 min  | si `live_status != ok` |
| `skill_card`   | 1 h    | si cambia `version` |
| `tool_card`    | 1 h    | — |
| `mcp_card`     | 1 min  | si `live_ping_ms` cambia >50% |
| `model_card`   | 10 min | si `quota_remaining` cambia |
| `harness_card` | 30 s   | — |
| `recommendation` | 10 min | si TTL expira o contexto cambia |

## Backends posibles
- En proceso (in-memory, LRU, 10k entries) — default.
- Redis (cuando se escale a multi-instancia).
- SQLite local (persistencia cross-restart).

## Tareas pendientes
- [ ] Implementar wrapper `cache.py` (no instalable en este turno).
- [ ] Métricas: hit-rate, miss-rate, eviction-rate.
- [ ] Política de warm-up: ¿qué se precarga al arrancar?
