# PROJECT_MANIFEST — Plantilla B1 (UOOS)
# SOURCE: UOOS Parte 1 · CAPA DE CONTROL 1 · schema project_docs.yaml
# El agente rellena esta plantilla. No inventa campos.

```yaml
project:
  id: ""                    # ej: maxbry-fromted-v1
  name: ""                  # nombre legible
  version: "0.1.0"          # semver
  status: draft             # draft | active | archived

identity:
  what_it_is: ""            # 1-2 frases: qué es este proyecto
  what_it_is_not: ""        # qué NO es (límites duros)
  owner: ""                 # Director / equipo

limits:
  hard:
    - "no modificar el kernel de ningún agente"
    - "no escribir secretos en el repo"
    - "no código desde 0 si existe source OS"
  soft: []

scope:
  in: []                    # qué sí entra en este proyecto
  out: []                   # qué queda fuera

paths:
  code: code/
  nodes: nodes/
  dag: dag/
  loops: loops/
  council: council/
  plan: plan/
  recovery: recovery/
  config: config/

config_refs:
  token_ref: config/token_ref.yaml
  repo_destino: config/repo_destino.yaml
  backup_destino: config/backup_destino.yaml

success_criteria:
  - "todos los nodos en done"
  - "evidence.json presente tras despliegue"
  - "sin secretos en el árbol del repo"

notes: ""
```

## Cómo rellenar (receta para el agente)
1. `id` y `name` = identificador único del trabajo en turno.
2. `what_it_is` / `what_it_is_not` = límites claros (L13 anti-scope-creep).
3. `limits.hard` = no se negocian.
4. `config_refs` apuntan a archivos que viven en la carpeta del proyecto, no en el Wordflow.
5. No añadir secciones nuevas. Solo rellenar.
