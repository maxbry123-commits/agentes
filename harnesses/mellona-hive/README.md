# Agent Hive / Mellona Hive — ⭐⭐⭐⭐☆

## Datos básicos
- **URL**: TBD (research en próximo turno)
- **Tipo**: multi-tenant agent orchestration
- **Tier**: 1 estrella menos porque es más experimental que los 3 anteriores

## Por qué
Cuando una sola tarea requiere **N agentes cooperando** (no uno solo). Por ejemplo:
- Agente A lee el repo.
- Agente B audita el código.
- Agente C genera el PR.
- Agente D aprueba.

Mellona coordina esos N agentes con memoria compartida.

## Integración
- **Auth**: API key + workspace id.
- **Patrón**: nuestro orquestador lanza un "hive job" con N steps.

## Spec del wrapper
```python
# spec, NO instalable
def run_hive(steps: list[Step], shared_memory: MemoryRef):
    hive = Mellona.create_workspace()
    for step in steps:
        agent = pick_agent(step.capability)
        hive.spawn(agent, step, shared_memory)
    return hive.collect(timeout=step.deadline)
```

## Riesgos
- Si un agente del hive se cuelga, ¿timeout global o por-step?
- Memoria compartida es un surface de inconsistencia.
- Pricing por agente activo (puede escalar mal).

## Pendiente
- [ ] Confirmar si Mellona = Agent Hive o son productos distintos.
- [ ] Investigar open-source alternatives (Mellona tiene repo público?).
- [ ] Evaluar si podemos usar Daytona+E2B para simular hive sin el producto externo.
