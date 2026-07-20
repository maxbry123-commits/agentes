---
name: task-manager
description: "Gestiona TODOs persistentes del orquestador. Crea, lista, marca como done o blocked, y asigna tareas a agentes. Use when el orquestador necesita trackear trabajo multi-paso o cuando un agente debe dejar sub-tareas para otros. Trigger with 'task-manager add' o '/task'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "Bash, Read, Write"
compatibility: "Designed for OpenClaw. Compatible with Claude Code, Codex, Cursor."
tags: [workflow, todo, productivity, orchestrator]
metadata:
  category: workflow
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# task-manager

Skill para gestionar la lista de TODOs persistente del orquestador.

## Cuándo se usa
- Al inicio de cada sesión del orquestador (cargar TODOs pendientes).
- Cuando un agente termina un paso y deja sub-tareas para otros.
- En el hook `before_agent_reply` para recordarle al agente qué le falta.

## Acciones (acciones del CLI)

| acción | args | descripción |
|--------|------|-------------|
| `add`  | `title`, `owner?`, `id?`     | crear tarea |
| `list` | `status?` (pending/in_progress/done/blocked) | listar (con filtro) |
| `done` | `id` | marcar como hecha |
| `blocked` | `id` | marcar como bloqueada |
| `show` | `id` | ver una |
| `assign` | `id`, `owner` | cambiar dueño |

## Ejemplos

```bash
# crear
echo '{"action":"add","title":"Auditar repo agentes","owner":"M3"}' \
  | openclaw skill run task-manager

# listar pendientes
echo '{"action":"list","status":"pending"}' \
  | openclaw skill run task-manager

# marcar como done
echo '{"action":"done","id":"t-001"}' \
  | openclaw skill run task-manager
```

## Storage
- Archivo local por default: `~/.openclaw/state/todos.json`.
- Configurable vía env var `TASK_MANAGER_PATH`.
- Alternativa (futuro): HF Space KV para multi-device.

## Output shape
```json
{ "ok": true, "item": {"id":"t-...","title":"...","status":"pending","owner":"...","created_at":<epoch>} }
{ "ok": true, "items": [...], "count": 3 }
```

## Tests
`scripts/validate.py` corre 3 acciones (add / list / done) sobre un archivo temporal.
PASS esperado cuando `python3` puede escribir y leer JSON.

## Véase también
- `references/state-format.md` — schema del archivo `todos.json`.
