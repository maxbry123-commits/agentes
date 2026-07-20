# task-manager

## Qué hace
Gestiona una lista de TODOs persistente del orquestador. Permite:
- Crear tarea
- Listar tareas (con filtro por status)
- Marcar como done / blocked
- Asignar a un agente

## Cuándo se usa
- Al inicio de cada sesión del orquestador (cargar TODOs pendientes).
- Cuando un agente termina un paso y deja sub-tareas para otros.
- En `before_agent_reply` para recordarle al agente qué le falta.

## Schema

```yaml
id: task-manager
version: 0.1.0
entry: ./run.py
required_tools: [bash, fs]
tags: [workflow, todo, productivity]
source: core
```

## Uso

```bash
openclaw skill run task-manager --input '{"action":"list","status":"pending"}'
openclaw skill run task-manager --input '{"action":"add","title":"Revisar PR #42","owner":"M3"}'
openclaw skill run task-manager --input '{"action":"done","id":"t-007"}'
```

## Storage
- Archivo local: `~/.openclaw/state/todos.json`
- Alternativa: HF Space KV (recomendado para multi-device).

## Estado
- Spec completa, scripts `run.py` + `install.sh` + `validate.py` en este dir.
- Pendiente: ejecución real con `openclaw` instalado.
