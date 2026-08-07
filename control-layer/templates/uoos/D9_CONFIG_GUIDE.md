# D9 config/ — guía unificada v2.0
# Vive en PROJECT/config/ · valores de destino por trabajo · NUNCA en control-layer runtime secrets

## Archivos canónicos

| Archivo | Qué declara |
|---------|-------------|
| `token_ref.yaml` | solo nombre de env var (GITHUB_TOKEN, …) |
| `repo_destino.yaml` | owner/repo/branch/path_prefix del código |
| `backup_destino.yaml` | memory_path + gdrive_folder opcional |
| `deploy_config.yaml` | reglas organizador (ver templates/despliegue/) |

## Reglas Sheriff
1. Cero secretos en claro (ghp_, sk-, AKIA…)
2. token_ref solo `token_env: NAME`
3. D1.config_refs apunta a estas rutas
4. Cambio de repo/token = editar config del proyecto, no Wordflow

## Ejemplo árbol proyecto
```
PROJECT/
  config/
    token_ref.yaml
    repo_destino.yaml
    backup_destino.yaml
    deploy_config.yaml
  PROJECT_MANIFEST.md
  nodes/
  dag/
  …
```
