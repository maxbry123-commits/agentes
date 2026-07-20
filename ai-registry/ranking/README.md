# Ranking — cómo se ordenan los candidatos

## Score compuesto (v0.1)

```
score = w_r * relevancia
      + w_h * exito_historico
      + w_c * (1 - costo_normalizado)
      + w_f * frescura
```

Pesos por defecto:
- `w_r = 0.50` (relevancia semántica)
- `w_h = 0.30` (éxito en últimas 30d, normalizado 0..1)
- `w_c = 0.15` (costo normalizado contra el candidato más caro del pool)
- `w_f = 0.05` (frescura del card — penaliza entries no usados hace >90d)

## Fuentes de cada componente

| componente | fuente |
|------------|--------|
| relevancia     | embeddings + reranker (recomendador) |
| exito_historico| `08-memory` filtrado por `kind=success` y ref al `agent_id` |
| costo_normalizado | `11-model.pricing` + métricas de uso |
| frescura       | `fetched_at` del card |

## Outliers
- Si `costo > threshold` (default 5x mediana del pool), descartar antes de rankear.
- Si `success_rate_30d < 0.3`, marcar como WARNING en output (no descarta automático).

## Tareas pendientes
- [ ] Calibrar pesos con feedback real.
- [ ] Política de cold-start: ¿qué hacer cuando un agent/skill no tiene historial?
- [ ] Penalizar agentes con `live_ping_ms > 5000` en ranking de harnesses.
