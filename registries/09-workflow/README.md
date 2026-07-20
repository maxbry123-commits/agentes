# 09 · Workflow Registry

## Propósito
Catálogo de **flujos completos pre-armados** (un workflow = secuencia de skills + tools + agents, con DAG). Cubre casos como "Deploy → Git → Docker → Railway".

## Schema (v0.1)
```json
{
  "title": "Workflow",
  "type": "object",
  "required": ["id", "name", "dag"],
  "properties": {
    "id":          { "type": "string" },
    "name":        { "type": "string" },
    "version":     { "type": "string" },
    "dag":         { "type": "object", "description": "nodos + edges (mismo formato que lobster DSL)" },
    "inputs":      { "type": "object" },
    "outputs":     { "type": "object" },
    "tags":        { "type": "array", "items": { "type": "string" } },
    "owner":       { "type": "string" }
  }
}
```

## Catálogo seed

| id | nombre | descripción |
|----|--------|-------------|
| `wf.deploy.docker`        | Deploy Docker   | test → build → push → restart |
| `wf.git.pr`               | PR a GitHub     | branch → commit → push → PR |
| `wf.railway.up`           | Deploy Railway  | railway up → domain |
| `wf.dsl-dag-sheriff-v7`   | Pipeline M3     | INPUT→PRECHECK→...→CERTIFICATION (ya en `lobster/`) |
| `wf.openapi.skill-audit`  | Auditar skill   | fetch → static check → run → report |

## Tareas pendientes
- [ ] Migrar workflows del repo `osquestador-auditor` a este registry.
- [ ] Definir validador estático de DAG (no ciclos, todos los nodos alcanzables).
- [ ] Versionar cada cambio de un workflow (mantener historial).
