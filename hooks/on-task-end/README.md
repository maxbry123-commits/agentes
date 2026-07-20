# Hook `on-task-end`

## Cuándo
Cada vez que una tarea (workflow, skill-run, agent-call) termina.

## Contrato

```yaml
name: on_task_end
trigger: "task.complete"
input:
  task_id: string
  agent_id: string
  skill_id: string
  status: enum[ok, fail, partial, blocked]
  duration_s: number
  cost_usd: number
  output: object
output:
  memory_entries_added: array
  metrics_emitted: array
  warnings: array
```

## Comportamiento
1. Persiste una entry en `08-memory` registry (success/failure/pattern).
2. Emite métricas (latencia, costo, success_rate).
3. Si el status es fail → crea un TODO en `task-manager` con la causa.

## Pendiente
- [ ] Política de muestreo: ¿escribimos memoria para TODAS las tareas o solo 1/N?
- [ ] Sincronizar con el AI Registry (refresh de cards).
