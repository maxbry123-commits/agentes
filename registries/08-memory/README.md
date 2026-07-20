# 08 · Memory Registry

## Propósito
Memoria operativa del sistema. Registra **qué funcionó, qué falló, qué patrón aprendió**. Es la base de las "100 mejoras de memoria extendida" del prompt M3.

## Schema (v0.1)
```json
{
  "title": "MemoryEntry",
  "type": "object",
  "required": ["id", "kind", "content", "created_at"],
  "properties": {
    "id":         { "type": "string" },
    "kind":       { "type": "string", "enum": ["success","failure","pattern","preference","constraint","metric"] },
    "content":    { "type": "string" },
    "tags":       { "type": "array", "items": { "type": "string" } },
    "refs":       { "type": "array", "items": { "type": "string" }, "description": "agent_id, skill_id, task_id" },
    "score":      { "type": "number", "minimum": -1, "maximum": 1 },
    "created_at": { "type": "string", "format": "date-time" }
  }
}
```

## Categorías y ejemplos

| kind | ejemplo |
|------|---------|
| `success`     | "Daytona resolveu bug en 12s, usar siempre para code execution" |
| `failure`     | "Codex-cli no soporta stdio en HF Spaces, fallback a openclaw" |
| `pattern`     | "Tareas de web-scraping siempre van por E2B, no Daytona" |
| `preference`  | "Max prefiere respuestas de máx 6 líneas" |
| `constraint`  | "No tocar VPS sin autorización explícita" |
| `metric`      | "Latencia p95 OpenClaw = 1.8s" |

## Tareas pendientes
- [ ] Definir política de retención (¿cuándo se purga una memory?).
- [ ] Pipeline de scoring automático: el sheriff marca success/failure.
- [ ] Integrar con el shell `memory_*` de M3 (que ya existe a nivel agente).
