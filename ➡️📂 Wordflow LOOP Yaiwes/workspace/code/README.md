# Workspace Code — Wordflow LOOP YAIWES

Esta carpeta es el **staging lógico de archivos de trabajo** antes de promoverlos a un destino real.

No sustituye `runtime/src`, no es un segundo kernel y no es un destino final.

Cada proyecto debe vivir bajo:

```text
workspace/code/<project_id>/
├── SOURCE.json
├── ARCHITECTURE.json
├── TASK-DAG.json
└── working/
```

Antes de promover un archivo desde `working/` se exige:

- `project_id` y destino resueltos;
- provenance/hash de la entrada;
- arquitectura y dependencias trazadas;
- task/node/claim identificados;
- `command_id` estable para side effects/retries;
- Sheriff autorizado cuando corresponda;
- tests del perfil `backend` o `frontend`;
- evidence persistida;
- no colisión con writer concurrente.

Para frontend, code/build por sí solos no cierran el trabajo: runtime + browser + interacción + console/DOM/visual + mobile/touch son parte del completion gate.
