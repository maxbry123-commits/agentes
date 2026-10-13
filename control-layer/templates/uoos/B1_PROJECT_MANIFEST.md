# PROJECT_MANIFEST — D1 v2.0 (plantilla nativa Wordflow)
# SOURCE research 2026: OpenAPM · agent-contracts · AgentSchema · AGENTS.md ·
#   agent-manifest (dabit3) · Manifest YAML identity · AWF · Orchestra pipelines
# Este archivo = identidad + contrato de interpretación. NO es estado vivo (→ D2).

```yaml
schema_version: "2.0"
kind: PROJECT_MANIFEST
control_schema: "2.0"
control_layer_min: "0.2.0"

# ── Identidad (inmutable post-active salvo bump version) ─────────────────
project_id: ""                      # ^[a-z0-9][a-z0-9_-]{1,63}$  estable forever
project_version: "0.1.0"            # semver 2.0
name: ""
slug: ""                            # opcional display corto
status: draft                       # draft | active | paused | archived

tenant_id: system
owner: ""                           # humano o team id
created_at: ""                      # ISO-8601
updated_at: ""

identity:
  purpose: ""                       # 1 frase medible
  what_it_is: ""
  what_it_is_not: ""                # anti scope-creep obligatorio
  domain: ""                        # ej: code | research | ops
  tags: []

# ── Árbol documental (D1–D10) — discovery paths ──────────────────────────
docs:
  manifest: PROJECT_MANIFEST.md     # este archivo
  state: state.json                 # D2 vivo
  nodes: nodes/*.yaml               # D3 agentes/nodos
  dag: dag/*.yaml                   # D4 workflows
  loops: loops/*.yaml               # D5
  council: council/*.yaml           # D6 tribunal
  plan: plan/                       # D7
  recovery: recovery/               # D8
  config: config/                   # D9 token/repo/backup refs
  receta: RECETA_AGENTE.md          # D10 contrato trabajo

# ── Fuentes de discovery (globs relativos a project root) ────────────────
agents_source:
  - nodes/*.yaml
workflows_source:
  - dag/*.yaml
loops_source:
  - loops/*.yaml
  - loops/L*.yaml

# ── Memoria / isolation (alineado LoopContext + MemoryPlugin scopes) ─────
memory:
  provider: local                   # local | plugin:<name>
  isolation: project-agent          # project-agent | project-only | agent-only
  scopes_enabled: [loop, task, agent, project, strategy]
  # namespaces runtime:
  #   loop:    {tenant}/{project}/runs/{run_id}
  #   task:    {tenant}/{project}/tasks/{task_id}
  #   agent:   {tenant}/{project}/agents/{agent_id}
  #   project: {tenant}/{project}/project
  #   strategy:{tenant}/{project}/strategy

# ── Política / autonomía / riesgo ────────────────────────────────────────
policy:
  autonomy_max: supervised          # supervised | semi | autonomous
  human_gates: []                   # deploy_production | force_push | delete_data
  max_parallel_agents: 4
  max_parallel_loops: 8
  default_loop_strategy: sequential # sequential | parallel | adversarial | consensus
  default_budget_level: tarea       # micro | tarea | fase | proyecto

# ── Límites (Sheriff hard = rechazo; soft = warn) ────────────────────────
limits:
  hard:
    - no_modify_control_layer
    - no_secrets_in_repo
    - no_code_from_scratch_without_source
    - no_skip_required_phases
    - no_global_memory_without_sheriff
    - no_change_project_id_after_active
  soft:
    - prefer_source_adapt_over_rewrite

forbidden_paths:
  - ".env"
  - ".env.*"
  - "**/*secret*"
  - "**/*.pem"
  - "**/*.key"
  - "**/credentials*"
  - "**/token*plain*"

# ── Config por proyecto (capa inmutable; valores fuera del control-layer) ─
config_refs:
  token_ref: config/token_ref.yaml        # solo env var name
  repo_destino: config/repo_destino.yaml
  backup_destino: config/backup_destino.yaml

# ── Criterios de éxito ejecutables (predicados, no prosa) ────────────────
success_criteria:
  - id: SC01
    check: "discovery.nodes_rejected == []"
  - id: SC02
    check: "state.json exists"
  - id: SC03
    check: "no secret patterns in tree"
  - id: SC04
    check: "dag leaf nodes status == done OR no active dag"
  - id: SC05
    check: "loops engine bootstrap ok"

# ── Scope de producto ────────────────────────────────────────────────────
scope:
  in: []
  out: []

# ── Integración Loop Engine (opcional override) ──────────────────────────
loops_engine:
  persist_dir: loop_data/{project_id}
  metrics_enabled: true
  policy_ref: null                    # null = default_policy.yaml del control-layer
```

---

## Objetivo del documento
Declarar **quién es el proyecto** y **cómo la capa de control lo interpreta** (discovery, memoria, límites, success). No guarda progreso de tareas.

## Plan / tareas deterministas (agente al crear D1)
1. Generar `project_id` único (`^[a-z0-9][a-z0-9_-]{1,63}$`).
2. Rellenar `identity.purpose` + `what_it_is` + `what_it_is_not` (3 campos no vacíos).
3. Fijar `status: draft` hasta primer bootstrap exitoso → luego `active`.
4. Verificar que paths en `docs.*` / globs existen o se crean vacíos.
5. `config_refs.*` solo referencias a archivos; **nunca** secretos en claro.
6. `success_criteria[].check` debe ser evaluable por Sheriff/script (sin lenguaje natural).
7. No listar agentes aquí → van en `nodes/*.yaml` (D3).

## Verificación Sheriff (fail = no bootstrap)
| Check | Regla |
|-------|--------|
| S1 | `schema_version` == 2.0 y `kind` == PROJECT_MANIFEST |
| S2 | `project_id` match pattern |
| S3 | `identity.purpose` len > 10 |
| S4 | `agents_source` no vacío |
| S5 | cero matches de secret patterns en el archivo |
| S6 | `status` ∈ {draft, active, paused, archived} |
| S7 | `config_refs` paths bajo `config/` |

## Prohibido
- Definir agentes/capabilities concretas (D3)
- Estado de runs/tareas (D2)
- Pegar tokens / ghp_ / AWS keys
- Cambiar `project_id` si `status == active`

## Referencias de diseño (research)
OpenAPM name+semver · agent-contracts system.id · AGENTS.md contract separation ·
agent-manifest capabilities at node level not project · isolation namespaces Wordflow loops
