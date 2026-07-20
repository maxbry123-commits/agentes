# 01 · Agent Registry

## Propósito
Catálogo canónico de los **agentes** que el sistema puede despachar. Un agente = un endpoint ejecutable (HTTP/gRPC/stdio) con un `agent_card.json` que describe capacidades, modelo subyacente, y habilidades.

## Schema (v0.1)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentCard",
  "type": "object",
  "required": ["id", "name", "version", "endpoint", "model"],
  "properties": {
    "id":          { "type": "string", "pattern": "^[a-z0-9-]{3,64}$" },
    "name":        { "type": "string" },
    "version":     { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "endpoint":    { "type": "string", "format": "uri" },
    "model":       { "type": "string" },
    "provider":    { "type": "string", "enum": ["MiniMax","anthropic","cerebras","groq","nvidia","openai","google","deepseek","alibaba","mistral"] },
    "skills":      { "type": "array", "items": { "type": "string" } },
    "tools":       { "type": "array", "items": { "type": "string" } },
    "mcps":        { "type": "array", "items": { "type": "string" } },
    "harness":     { "type": "string" },
    "tier":        { "type": "string", "enum": ["platinum","gold","silver","bronze"] },
    "rate_limit":  { "type": "object" },
    "tags":        { "type": "array", "items": { "type": "string" } }
  }
}
```

## Catálogo inicial (placeholder — completar en próximo turno)

| id | nombre | provider | model | endpoint | tier |
|----|--------|----------|-------|----------|------|
| `m3-research` | M3 Research | MiniMax | MiniMax-M3 | http://127.0.0.1:18789/v1/chat/completions | platinum |
| `claude-code` | Claude Code | anthropic | claude-3.7 | http://127.0.0.1:8081 | gold |
| `mimo-code`   | Mimo Code   | anthropic | claude-3.7 | http://127.0.0.1:8082 | gold |
| `openclaw`    | OpenClaw    | MiniMax | MiniMax-M3 | http://127.0.0.1:8083 | platinum |
| `codex-cli`   | Codex CLI   | openai | gpt-4o | TBD | silver |
| `openhands`   | OpenHands   | openai | gpt-4o | TBD | silver |
| `kimi-cli`    | Kimi CLI    | alibaba | kimi-k2 | TBD | silver |
| `hermes-cli`  | Hermes CLI  | nous | hermes-3 | TBD | bronze |
| `nemotron`    | Nemotron    | nvidia | llama-3.1-nemotron | TBD | silver |
| `litellm`     | LiteLLM router | multi | multi | http://127.0.0.1:4000 | gold |

## Tareas pendientes
- [ ] Validar cada endpoint con `curl` + `Authorization: Bearer ${OC_GATEWAY_TOKEN}`.
- [ ] Crear HTML de validación por agente (11 secciones, ver `agentes-catalog/<id>/index.html`).
- [ ] Documentar rate limit real (tokens/min, req/min).
- [ ] Confirmar tier con datos de uso.
