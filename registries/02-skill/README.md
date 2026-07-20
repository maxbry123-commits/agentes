# 02 · Skill Registry

## Propósito
Catálogo de **skills** (paquetes invocables que un agente puede cargar). Una skill = bundle versionado de prompts + tools + (opcional) MCPs + (opcional) harness.

## Schema (v0.1)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SkillCard",
  "type": "object",
  "required": ["id", "name", "version", "entry", "tags"],
  "properties": {
    "id":            { "type": "string", "pattern": "^[a-z0-9-]{3,64}$" },
    "name":          { "type": "string" },
    "version":       { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "entry":         { "type": "string" },
    "description":   { "type": "string" },
    "required_tools":{ "type": "array", "items": { "type": "string" } },
    "required_mcps": { "type": "array", "items": { "type": "string" } },
    "hints":         { "type": "object" },
    "tags":          { "type": "array", "items": { "type": "string" } },
    "source":        { "type": "string", "enum": ["core","openclaw","marketplace","custom"] }
  }
}
```

## Catálogo inicial (los 6 prioritarios del prompt M3)

| id | nombre | entry | required_tools | tags |
|----|--------|-------|----------------|------|
| `task-manager` | Task Manager | `skills-prioritarios/task-manager/` | bash, fs | workflow,todo |
| `test-runner`  | Test Runner  | `skills-prioritarios/test-runner/`  | bash, fs | qa,test |
| `git`          | Git          | `skills-prioritarios/git/`          | bash | vcs,git |
| `terminal`     | Terminal     | `skills-prioritarios/terminal/`     | bash | shell |
| `web-search`   | Web Search   | `skills-prioritarios/web-search/`   | http, parse | research |
| `url-reader`   | URL Reader   | `skills-prioritarios/url-reader/`   | http, parse | research |

## Catálogo objetivo (M3)
- **Top 300 skills** de code/programación
- **Top 430 plugins** marketplace
- **Top 100 herramientas**
- 6 prioritarios desde el día 1 (arriba).

## Tareas pendientes
- [ ] Definir `entry` ejecutable (¿Python module? ¿bash? ¿Node?)
- [ ] Crear `install.sh` por skill (idempotente, no-op si ya está).
- [ ] Crear `validate.py` que ejecuta 1 test mínimo de cada skill.
- [ ] Ranking: votes + uso + éxito histórico.
