# RECETA PARA EL AGENTE — Cómo construir los 8 documentos UOOS
# SOURCE: UOOS Parte 1 · schema project_docs.yaml · plantillas B1–B8
# El Wordflow entrega esta receta al agente. El agente NO inventa estructura.

## Orden obligatorio
1. B1 PROJECT_MANIFEST.md
2. B2 state.json
3. B3 nodes/*.yaml   (uno por tarea)
4. B4 dag/DAG-*.yaml
5. B5 loops/L01.yaml … L11.yaml
6. B6 council/tribunal_6.yaml
7. B7 plan/PLAN_*.md
8. B8 recovery/RECOVERY.yaml
9. config/token_ref.yaml · repo_destino.yaml · backup_destino.yaml

## Reglas
- Copia la plantilla de `templates/uoos/` correspondiente.
- Solo rellena campos. No agregues secciones nuevas.
- Campos vacíos obligatorios = rechazo por Sheriff.
- `criterio_exito` y `rollback` deben ser verificables por máquina (comando o procedure_id).
- Nunca pongas el valor del token. Solo la referencia en `config/token_ref.yaml`.
- Sin source OS materializado → no escribas código desde 0 (usa install/ del Wordflow).

## config/ del proyecto (variables por trabajo)
```yaml
# config/token_ref.yaml
token_env: GITHUB_TOKEN          # nombre de la variable de entorno
# nunca: token: ghp_xxxxx

# config/repo_destino.yaml
owner: maxbry123-commits
repo: agentes
branch: main
path_prefix: ""                  # subcarpeta opcional

# config/backup_destino.yaml
memory_path: memory/backup/
gdrive_folder: ""                # opcional, vacío = no Drive
```

## Checklist antes de entregar al Wordflow
- [ ] Los 8 docs existen en las rutas del schema
- [ ] state.json tiene todos los nodos de B3 en pending
- [ ] DAG sin ciclos y todos los ids existen en nodes/
- [ ] Cada nodo tiene rollback + criterio_exito verificable
- [ ] config/ no contiene secretos en claro
- [ ] PROJECT_MANIFEST declara what_it_is_not y limits.hard

## Qué hace el Wordflow después
1. Valida con `schemas/project_docs.yaml`
2. Ejecuta según DAG + loops + tribunal
3. Si hay code/ → install determinista (si aplica) → despliegue leyendo config/
4. Genera evidence.json
