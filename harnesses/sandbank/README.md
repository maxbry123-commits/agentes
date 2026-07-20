# Sandbank — ⭐⭐⭐⭐⭐ (capa unificada)

## Datos básicos
- **URL**: TBD (research en próximo turno)
- **Tipo**: capa de abstracción sobre Daytona/E2B/HF
- **Tier**: el más alto porque **rutea** a los otros

## Por qué existe
En lugar de que el orquestador sepa cuál harness usar, **Sandbank** lo decide:
- Mira la skill (`required_tools`, `timeout_s`, `state_required`).
- Mira el sistema (cuota, costo, latencia objetivo).
- Devuelve el harness real que va a ejecutar.

## Routing interno

| si la skill es... | y necesita... | va a... |
|--------------------|---------------|---------|
| code + workspace persistente | git, docker | daytona |
| code sin estado, <30min | python, node | e2b |
| gpu / inferencia | cuda, tgi | hf-space |
| HTTP-only, <5s | nada pesado | cloudflare-sb |

## Spec del wrapper
```python
# spec, NO instalable
def run(task, skill):
    harness = decide_harness(skill, task.constraints)
    return harness.exec(task, skill)
```

## Estado
- Capa conceptual lista.
- Implementación: depende de research.
- Default si nada matchea: **e2b** (más seguro).

## Pendiente
- [ ] Confirmar si Sandbank es un producto externo o si lo construimos nosotros.
- [ ] Si lo construimos: spec del `decide_harness()`.
- [ ] Tests de routing con casos reales.
