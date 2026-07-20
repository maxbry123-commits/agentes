# 05 · MCP Registry

## Propósito
Catálogo de **servidores MCP (Model Context Protocol)** disponibles. Cada MCP expone tools, resources y prompts vía JSON-RPC.

## Schema (v0.1)
```json
{
  "title": "McpServerCard",
  "type": "object",
  "required": ["id", "transport", "endpoint"],
  "properties": {
    "id":         { "type": "string" },
    "name":       { "type": "string" },
    "transport":  { "type": "string", "enum": ["stdio","sse","ws","http"] },
    "endpoint":   { "type": "string" },
    "command":    { "type": "string", "description": "solo si transport=stdio" },
    "args":       { "type": "array", "items": { "type": "string" } },
    "tools":      { "type": "array", "items": { "type": "string" } },
    "auth":       { "type": "object", "properties": { "type": { "type": "string" }, "token_env": { "type": "string" } } },
    "version":    { "type": "string" }
  }
}
```

## Catálogo objetivo (prompt M3)

| id | transporte | propósito | dónde |
|----|------------|-----------|-------|
| `github`      | stdio / http | PRs, issues, repos | `mcp-servers/github/` |
| `filesystem`  | stdio | Leer/escribir archivos | `mcp-servers/filesystem/` |
| `postgresql`  | stdio | SQL sobre PG | `mcp-servers/postgresql/` |
| `browser`     | ws    | Playwright headless | `mcp-servers/browser/` |
| `slack`       | http  | Mensajería | `mcp-servers/slack/` |
| `gmail`       | http  | Mail | `mcp-servers/gmail/` |
| `openclaw-mcp`| stdio | Ya en `openclaw/mcp_bridge.py` | `openclaw/` (puerto 18791) |

## Tareas pendientes
- [ ] Listar tools reales que expone cada MCP (no asumir).
- [ ] Test de smoke: `ping` / `list_tools` en cada uno.
- [ ] Política de auth: qué MCPs requieren token humano vs service-account.
