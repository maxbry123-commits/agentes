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

## Catálogo de servidores — **verificados con research 2026-07-20**

> **Fuente**: `github.com/modelcontextprotocol/servers` (oficial, mantenido por Anthropic + comunidad).
> Todos open-source, **MIT-licensed**.

### Servidores oficiales (referencia)

| id | nombre | transport | install | tools clave | auth |
|----|--------|-----------|---------|-------------|------|
| `filesystem` | Filesystem | stdio | `npx -y @modelcontextprotocol/server-filesystem <path>` | `list_directory`, `read_file`, `write_file`, `create_directory` | none (path-scoped) |
| `github`     | GitHub     | stdio | `npx -y @modelcontextprotocol/server-github` | `create_issue`, `create_pr`, `list_pull_requests`, `search_repositories` | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `postgres`   | PostgreSQL | stdio | `npx -y @modelcontextprotocol/server-postgres <connstr>` | `execute_query`, `list_tables`, `describe_table` | conn string |
| `sqlite`     | SQLite     | stdio | `npx -y @modelcontextprotocol/server-sqlite <path>` | `execute_query`, `list_tables` | none |
| `puppeteer`  | Browser    | stdio | `npx -y @modelcontextprotocol/server-puppeteer` | `take_screenshot`, `click_element`, `fill_form`, `navigate` | none |
| `fetch`      | Fetch      | stdio | `npx -y @modelcontextprotocol/server-fetch` | `fetch_url`, `extract_text` | none |
| `brave`      | Brave Search | stdio | `npx -y @modelcontextprotocol/server-brave-search` | `search_web` | `BRAVE_API_KEY` |
| `slack`      | Slack      | stdio | `npx -y @modelcontextprotocol/server-slack` | `send_message`, `create_channel`, `list_channels` | `SLACK_BOT_TOKEN` |
| `memory`     | Memory     | stdio | `npx -y @modelcontextprotocol/server-memory` | `create_entities`, `search_nodes`, `open_nodes` | none |
| `time`       | Time       | stdio | `npx -y @modelcontextprotocol/server-time` | `get_current_time`, `convert_timezone` | none |
| `everything` | Everything | stdio | `npx -y @modelcontextprotocol/server-everything` | (test server) | none |

### Servidores de terceros (oficial integrations)

| id | provider | transport | install | nota |
|----|----------|-----------|---------|------|
| `cloudflare` | Cloudflare | stdio | `npx -y @cloudflare/mcp-server-cloudflare` | Workers/KV/R2/D1 management |
| `e2b`        | E2B        | stdio | `npx -y @e2b/mcp-server` | corre código en E2B sandboxes |
| `browserbase`| Browserbase | stdio | `npx -y @browserbasehq/mcp-server` | browser automation en cloud |

### Servidor nuestro (custom, ya deployed)

| id | nombre | transport | endpoint | tools | auth |
|----|--------|-----------|----------|-------|------|
| `openclaw-mcp` | OpenClaw MCP bridge | http | `http://127.0.0.1:18791` (en VPS) | `chat.inject`, `chat.load`, `final.load` | `${OC_GATEWAY_TOKEN}` |

> **Importante**: el registry oficial hoy vive en `https://anthropic.com/mcp` (el "MCP Registry").
> La lista de servidores publicados está en `github.com/modelcontextprotocol/servers/README.md`.

## Configuración (ejemplo OpenClaw / Claude Desktop)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>" }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

## Tareas pendientes
- [ ] Probar `ping` (list_tools) a cada MCP en HF Space.
- [ ] Política de auth: qué MCPs requieren token humano vs service-account.
- [ ] Métricas de uso por MCP (alimenta el AI Registry).
- [ ] Soporte para MCPs remotos vía SSE/WS (no solo stdio local).
