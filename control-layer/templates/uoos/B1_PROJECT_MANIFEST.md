# PROJECT_MANIFEST — Plantilla D1
# SOURCE: project.schema · Agent Identity + Project Identity
# Declara: esta carpeta ES un proyecto y bajo qué reglas se interpreta.

```yaml
project_id: ""                 # ej: jarvis
project_version: "0.1.0"
control_schema: "1.0"
status: draft                  # draft | active | archived
name: ""

tenant_id: ""                  # opcional; default system

identity:
  what_it_is: ""
  what_it_is_not: ""
  owner: ""

agents_source:
  - nodes/*.yaml

workflows_source:
  - dag/*.yaml

memory:
  provider: ""                 # ej: tencent | local
  isolation: project-agent     # project-agent | project-only | agent-only
  shared_scope: project         # project | none

limits:
  hard:
    - "no modificar kernel de agentes"
    - "no secretos en el repo"
    - "no código desde 0 si existe source"
  soft: []

scope:
  in: []
  out: []

config_refs:
  token_ref: config/token_ref.yaml
  repo_destino: config/repo_destino.yaml
  backup_destino: config/backup_destino.yaml

success_criteria:
  - "agents discovered + sheriff OK"
  - "evidence.json tras despliegue"
  - "sin secretos en árbol"
```

## Reglas
1. `project_id` único y estable.
2. `agents_source` / `workflows_source` = de dónde Discovery lee.
3. Memoria aislada por tenant+project+agent (nunca agent_id solo).
4. Solo rellenar; no inventar secciones.
