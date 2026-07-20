# 07 · Knowledge Registry

## Propósito
Catálogo de **manuales, API docs, wikis, RFCs, papers** que el sistema puede consultar. Indexa documentos, no los almacena (los archivos viven en `docs/` o en URLs externas).

## Schema (v0.1)
```json
{
  "title": "KnowledgeDoc",
  "type": "object",
  "required": ["id", "title", "source"],
  "properties": {
    "id":          { "type": "string" },
    "title":       { "type": "string" },
    "source":      { "type": "string", "description": "path local o URL" },
    "version":     { "type": "string" },
    "tags":        { "type": "array", "items": { "type": "string" } },
    "checksum":    { "type": "string" },
    "indexed_at":  { "type": "string", "format": "date-time" },
    "summary":     { "type": "string" }
  }
}
```

## Catálogo seed (ya presente en repo)

| id | título | source |
|----|--------|--------|
| `k.openclaw.config`   | OpenClaw config reference | `openclaw/openclaw.json.template` |
| `k.dsl.dag-sheriff`   | DSL DAG SHERIFF V7 prompt | `attachments/.../PROMPT_M3_DSL_SHERIFF_V7.md` |
| `k.runtime.recovery`  | Recovery guide            | `core/B8_RECOVERY.md` |
| `k.runtime.inventory` | RUNTIME_INVENTORY         | `agents/RUNTIME_INVENTORY.md` |
| `k.nct-anchors`       | IDENTITY de cada agente   | `agents/nct-anchors/IDENTITY.md` |

## Tareas pendientes
- [ ] Agregar API docs de cada proveedor LLM (Anthropic, OpenAI, Groq, Cerebras, NVIDIA).
- [ ] Indexar el changelog de OpenClaw.
- [ ] Vincular cada knowledge doc a skills que lo usan.
