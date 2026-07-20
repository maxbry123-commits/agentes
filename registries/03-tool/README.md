# 03 · Tool Registry

## Propósito
Catálogo de **herramientas atómicas** (no skills compuestas). Una tool = 1 capacidad simple invocable con argumentos tipados.

## Schema (v0.1)
```json
{
  "title": "ToolCard",
  "type": "object",
  "required": ["id", "name", "input_schema", "executor"],
  "properties": {
    "id":            { "type": "string" },
    "name":          { "type": "string" },
    "executor":      { "type": "string", "enum": ["bash","python","docker","http","grpc","mcp"] },
    "input_schema":  { "type": "object" },
    "output_schema": { "type": "object" },
    "side_effects":  { "type": "boolean" },
    "sandbox":       { "type": "string", "enum": ["host","docker","e2b","daytona","hf","cloudflare","none"] },
    "rate_limit":    { "type": "object" }
  }
}
```

## Catálogo base (cubierto por el prompt M3)

| id | executor | sandbox por defecto | side_effects |
|----|----------|--------------------|--------------|
| `bash`        | bash    | docker | true  |
| `docker`      | docker  | host   | true  |
| `git`         | bash    | docker | true  |
| `python`      | python  | e2b    | false |
| `node`        | bash    | e2b    | false |
| `ocr`         | http    | none   | false |
| `pdf`         | python  | none   | false |
| `sql`         | python  | none   | true  |
| `http`        | python  | none   | false |
| `filesystem`  | mcp     | none   | true  |

## Tareas pendientes
- [ ] Documentar `input_schema` exacto de cada tool (JSON Schema).
- [ ] Decidir qué tools son peligrosas y requieren `policy:elevated`.
- [ ] Definir timeout default y retry policy.
