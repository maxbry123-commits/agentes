# Estado de TODOs — formato

`task-manager` persiste los TODOs en un archivo JSON. El path default es
`~/.openclaw/state/todos.json` (configurable por env `TASK_MANAGER_PATH`).

## Schema (v0.1)

```json
[
  {
    "id": "t-3a9c01",
    "title": "Auditar repo agentes",
    "owner": "M3",
    "status": "pending",
    "created_at": 1753000000.123
  }
]
```

## Estados posibles

- `pending` — creado, no iniciado.
- `in_progress` — alguien lo está haciendo (no se persiste en este spec v0.1, futuro).
- `done` — terminado.
- `blocked` — bloqueado por algo externo.

## Reglas

- El `id` se autogenera si no se pasa (`t-<6 hex>`).
- El archivo se sobreescribe atómicamente en cada `save()` (write + rename).
- No hay concurrencia manejada en v0.1: si 2 procesos escriben a la vez, el último gana.
