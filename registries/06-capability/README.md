# 06 · Capability Registry

## Propósito
Catálogo de **capacidades declarativas** (vs tools concretas). Una capability = "lo que el sistema sabe hacer", independientemente de qué agente o skill la implementa. Esto permite que el recomendador haga match semántico.

## Schema (v0.1)
```json
{
  "title": "Capability",
  "type": "object",
  "required": ["id", "name", "description", "implementations"],
  "properties": {
    "id":              { "type": "string" },
    "name":            { "type": "string" },
    "description":     { "type": "string" },
    "category":        { "type": "string", "enum": ["code","research","ops","memory","ui","data","infra"] },
    "input_types":     { "type": "array", "items": { "type": "string" } },
    "output_types":    { "type": "array", "items": { "type": "string" } },
    "implementations": { "type": "array", "items": { "type": "string" }, "description": "skill IDs o agent IDs" }
  }
}
```

## Catálogo seed

| id | nombre | categoría | implementaciones |
|----|--------|-----------|------------------|
| `cap.code.review`     | Revisión de código       | code     | [`claude-code`, `mimo-code`] |
| `cap.code.generate`   | Generar código           | code     | [`claude-code`, `mimo-code`, `codex-cli`] |
| `cap.research.web`    | Investigación web        | research | [`m3-research`, `web-search`, `url-reader`] |
| `cap.ops.deploy`      | Desplegar servicio       | ops      | [`workflow:deploy-docker`] |
| `cap.memory.recall`   | Recordar memoria extendida | memory | [`memory-registry`] |
| `cap.data.ocr`        | OCR de PDFs              | data     | [`tool:ocr`] |
| `cap.ui.render`       | Renderizar UI            | ui       | [`openclaw`] |

## Tareas pendientes
- [ ] Confirmar cada `implementation` con evidencia real.
- [ ] Indexar capacidades en `ai-registry/recommender/` para búsqueda semántica.
- [ ] Permitir que un mismo agente declare varias capabilities.
