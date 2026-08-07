# PROJECT_MANIFEST — D1 (plantilla nativa Wordflow)
# SOURCE: project.schema + investigación D1 (AgentSchema, OpenAPM, agent-contracts, CrewAI, Cursor)
# Este archivo declara CÓMO interpretar la carpeta del proyecto. No es estado vivo.

```yaml
schema_version: "1.0"
control_schema: "1.0"
control_layer_min: "0.1.0"

project_id: ""                    # ^[a-z0-9][a-z0-9_-]*$  estable
project_version: "0.1.0"          # semver
name: ""
status: draft                     # draft | active | archived

tenant_id: system
owner: ""
created_at: ""                    # ISO-8601

identity:
  purpose: ""                     # 1 frase: para qué existe el proyecto
  what_it_is: ""
  what_it_is_not: ""              # límites de producto (anti scope-creep)

# Discovery sources (globs bajo project root)
agents_source:
  - nodes/*.yaml
workflows_source:
  - dag/*.yaml
loops_source:
  - loops/L*.yaml

memory:
  provider: local                 # local | tencent | other
  isolation: project-agent        # project-agent | project-only | agent-only
  shared_scope: project            # project | none
  # namespaces runtime:
  #   private: {tenant}/{project}/agents/{agent_id}
  #   project: {tenant}/{project}/project

policy:
  autonomy_max: supervised        # supervised | semi | autonomous
  human_gates: []                 # ej: [deploy_production, force_push]
  max_parallel_agents: 4

limits:
  hard:
    - no_modify_agent_kernels
    - no_secrets_in_repo
    - no_code_from_scratch_without_source
    - no_skip_dag
    - no_global_memory_without_sheriff
  soft: []

forbidden_paths:
  - ".env"
  - "**/*secret*"
  - "**/*.pem"
  - "**/credentials*"

config_refs:
  token_ref: config/token_ref.yaml      # solo nombre de env var
  repo_destino: config/repo_destino.yaml
  backup_destino: config/backup_destino.yaml

success_criteria:
  - id: SC01
    check: "bootstrap_agents.rejected == []"
  - id: SC02
    check: "evidence.json exists after deploy"
  - id: SC03
    check: "no secret patterns in tree"
  - id: SC04
    check: "all dag leaf nodes status == done"

scope:
  in: []
  out: []
```

## Plan / objetivo / tareas deterministas (del documento)

**Objetivo:** declarar identidad del proyecto y reglas de interpretación para Discovery + Sheriff.

**Tareas del agente al crear D1:**
1. Asignar `project_id` único (minúsculas, sin espacios).
2. Rellenar purpose / what_it_is / what_it_is_not (sin ambigüedad).
3. Confirmar globs agents_source y workflows_source existen o se crearán.
4. Dejar token_ref solo con `token_env` (nunca valor).
5. success_criteria solo con checks ejecutables (strings de predicado).

**Verificación Sheriff:**
- schema_version presente
- project_id pattern OK
- agents_source no vacío
- forbidden_paths sin solaparse con code/ legítimo de forma accidental
- ningún ghp_ / github_pat_ en el archivo

**Prohibido:** definir agentes aquí; meter state de tareas; pegar API keys.
