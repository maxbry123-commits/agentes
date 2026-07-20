# Cards — formato unificado

> "Una card = la vista normalizada y enriquecida de un entry de cualquier registry."

## ¿Por qué?
Cada uno de los 12 registries tiene su schema propio. Pero el recomendador, el panel, y el orquestador necesitan una **vista uniforme** con campos estables. Esa vista es la `card`.

## Tipos de cards (v0.1)

| tipo | fuente | campos extra |
|------|--------|--------------|
| `agent_card`  | `01-agent`     | `live_status`, `p95_latency_ms`, `last_used_at`, `success_rate_30d` |
| `skill_card`  | `02-skill`     | `usage_count_30d`, `success_rate_30d`, `avg_cost_usd`, `popularity_score` |
| `tool_card`   | `03-tool`      | `call_count_30d`, `avg_duration_ms`, `error_rate_30d` |
| `mcp_card`    | `05-mcp`       | `live_ping_ms`, `tools_count`, `last_healthcheck_at` |
| `model_card`  | `11-model`     | `quota_remaining`, `p95_latency_ms`, `cost_per_1k_input`, `cost_per_1k_output` |
| `harness_card`| `10-harness`   | `active_sessions`, `cold_start_p95_ms`, `region` |

## Schema genérico (v0.1)

```json
{
  "title": "GenericCard",
  "type": "object",
  "required": ["kind", "id", "source_registry", "fetched_at", "card"],
  "properties": {
    "kind":            { "type": "string", "enum": ["agent","skill","tool","mcp","model","harness"] },
    "id":              { "type": "string" },
    "source_registry": { "type": "string" },
    "version":         { "type": "string" },
    "fetched_at":      { "type": "string", "format": "date-time" },
    "card":            { "type": "object", "description": "el contenido del registry original" },
    "enrichments":     { "type": "object" },
    "tags":            { "type": "array", "items": { "type": "string" } }
  }
}
```

## Ejemplo mínimo (mcp_card)

```json
{
  "kind": "mcp",
  "id": "openclaw-mcp",
  "source_registry": "05-mcp",
  "version": "0.1.0",
  "fetched_at": "2026-07-20T08:00:00Z",
  "card": {
    "transport": "http",
    "endpoint": "http://127.0.0.1:18791",
    "tools": ["chat.inject","chat.load","final.load"]
  },
  "enrichments": {
    "live_ping_ms": 12,
    "last_healthcheck_at": "2026-07-20T07:55:00Z"
  },
  "tags": ["core","mcp","openclaw"]
}
```

## Tareas pendientes
- [ ] Definir `enrichments` específicos por tipo (qué se calcula y de dónde sale).
- [ ] Decidir cadencia de refresh (¿on-demand? ¿cada 5min?).
- [ ] Política de invalidación cuando el registry origen cambia.
