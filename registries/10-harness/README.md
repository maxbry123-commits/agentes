# 10 · Harness Registry

## Propósito
Catálogo de **dónde se ejecuta cada skill/agent/workflow**. Mapea tipo de tarea → harness óptimo.

## Schema (v0.1)
```json
{
  "title": "Harness",
  "type": "object",
  "required": ["id", "name", "kind"],
  "properties": {
    "id":            { "type": "string" },
    "name":          { "type": "string" },
    "kind":          { "type": "string", "enum": ["cloud-ide","microvm","container","serverless","gpu-space","edge"] },
    "provider":      { "type": "string" },
    "endpoint":      { "type": "string" },
    "auth":          { "type": "object" },
    "supports":      { "type": "array", "items": { "type": "string" } },
    "cold_start_ms": { "type": "integer" },
    "timeout_s":     { "type": "integer" }
  }
}
```

## Catálogo (prompt M3)

| id | provider | kind | uso recomendado |
|----|----------|------|-----------------|
| `daytona`    | Daytona | cloud-ide  | Programación |
| `e2b`        | E2B     | microvm    | Skill aislada |
| `sandbank`   | Sandbank | contenedor | Capa unificada (rutea a Daytona/E2B/HF) |
| `mellona-hive` | Mellona | multi-tenant | Agent Hive / Mellona Hive |
| `hf-space`   | HF      | gpu-space  | GPU / inferencia |
| `cloudflare-sb` | Cloudflare | edge  | Rápida en borde |

## Routing rules (prompt M3 K)
- **Programación** → Daytona
- **Skill aislada** → E2B
- **GPU/inferencia** → HF Space
- **Rápida en borde** → Cloudflare Sandbox
- **Por defecto** → Sandbank (capa unificada)

## Tareas pendientes
- [ ] Confirmar credenciales y endpoints reales de cada harness.
- [ ] Medir cold_start_ms real de cada uno.
- [ ] Implementar router (`ai-registry/recommender/`) que elija harness.
