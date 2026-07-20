# 04 · Prompt Registry

## Propósito
Catálogo de **prompts, plantillas, roles y DSL** reutilizables. No es el registry de skills (eso es nivel superior): es el contenido textual + estructural que las skills y los agentes consumen.

## Schema (v0.1)
```json
{
  "title": "PromptEntry",
  "type": "object",
  "required": ["id", "kind", "version", "body"],
  "properties": {
    "id":      { "type": "string" },
    "kind":    { "type": "string", "enum": ["system","user","template","role","dsl","fewshot","rubric"] },
    "version": { "type": "string" },
    "body":    { "type": "string" },
    "vars":    { "type": "array", "items": { "type": "string" } },
    "tags":    { "type": "array", "items": { "type": "string" } }
  }
}
```

## Categorías

| kind | ejemplo | uso |
|------|---------|-----|
| `system`   | "Eres M3, asistente de Max..."  | Carga al iniciar sesión agente |
| `user`     | Plantillas de preguntas tipo    | Reutilizables |
| `template` | "Resume este {{doc}} en 3 bullets" | Con vars `{{var}}` |
| `role`     | Rol "sheriff" / "sentinel" / "judge" | Inyectables en nodos |
| `dsl`      | `dsl-dag-sheriff-v7.lobster`    | Workflows formales |
| `fewshot`  | Lista de pares input→output    | In-context learning |
| `rubric`   | Criterios de PASS/FAIL          | Judge del sheriff |

## Seed (este turno)
- `dsl-dag-sheriff-v7` (ya está en `lobster/`)
- `rol:sheriff`, `rol:sentinel`, `rol:judge`
- `system:mavis-root-v1`

## Tareas pendientes
- [ ] Migrar todos los prompts existentes en `agents/nct-anchors/IDENTITY.md` a este registry.
- [ ] Versionar rubric del Judge.
- [ ] Diff visual entre versiones de un mismo prompt.
