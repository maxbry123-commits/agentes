# 11 · Model Registry

## Propósito
Catálogo de **modelos LLM** disponibles. Una entrada = 1 modelo con sus capacidades, costo, límites, y rutas de acceso.

## Schema (v0.1)
```json
{
  "title": "Model",
  "type": "object",
  "required": ["id", "provider", "context_window", "pricing"],
  "properties": {
    "id":             { "type": "string" },
    "provider":       { "type": "string", "enum": ["MiniMax","anthropic","openai","google","deepseek","alibaba","mistral","meta","cerebras","groq","nvidia"] },
    "family":         { "type": "string" },
    "context_window": { "type": "integer" },
    "modalities":     { "type": "array", "items": { "type": "string", "enum": ["text","image","audio","video"] } },
    "tools":          { "type": "boolean" },
    "json_mode":      { "type": "boolean" },
    "pricing":        { "type": "object", "properties": { "input_per_1k": { "type": "number" }, "output_per_1k": { "type": "number" } } },
    "rate_limit":     { "type": "object" },
    "endpoint":       { "type": "string" },
    "auth_env":       { "type": "string" }
  }
}
```

## Catálogo seed

| id | provider | context | tools | auth_env |
|----|----------|---------|-------|----------|
| `MiniMax-M3`         | MiniMax     | 1M  | true  | (configurado en gateway) |
| `MiniMax-M2.7`       | MiniMax     | 1M  | true  | (idem) |
| `claude-3.7-sonnet`  | anthropic   | 200k | true  | `ANTHROPIC_API_KEY` |
| `gpt-4o`             | openai      | 128k | true  | `OPENAI_API_KEY` |
| `gemini-2.0-flash`   | google      | 1M  | true  | `GOOGLE_API_KEY` |
| `deepseek-v3`        | deepseek    | 64k | true  | `DEEPSEEK_API_KEY` |
| `qwen-2.5-72b`       | alibaba     | 128k | true | `QWEN_API_KEY` |
| `kimi-k2`            | alibaba     | 128k | true | `KIMI_API_KEY` |
| `llama-3.1-8b`       | groq        | 128k | true | `GROQ_API_KEY` |
| `llama-3.1-nemotron` | nvidia      | 128k | true | `NVIDIA_API_KEY` |
| `gemma-2-27b`        | cerebras    | 8k   | false | `CEREBRAS_API_KEY` |

## Tareas pendientes
- [ ] Validar cada `endpoint` con un `chat.completions` mínimo.
- [ ] Cargar pricing real desde docs oficiales.
- [ ] Marcar modelos con cuota agotada / deprecados.
