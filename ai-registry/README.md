# 🧠 AI Registry — Capa Intermedia

> "El índice que conecta todo lo demás."
> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección M.

## Propósito
Un **índice semántico unificado** sobre los 12 registries. En lugar de que cada consumidor consulte N registries y haga joins, el AI Registry expone:

- **Agent Cards** — vista normalizada de los entries del Agent Registry, enriquecida con skills/tools/mcps/harness.
- **Skill Cards** — vista normalizada del Skill Registry, con dependencias y stats de uso.
- **MCP Cards** — vista normalizada del MCP Registry, con health en vivo.
- **Índice semántico** — embeddings sobre `name+description+tags` para búsqueda por significado.
- **Ranking** — score por (relevancia × éxito histórico × costo).
- **Historial** — qué se ejecutó, qué resultado dio, cuánto costó.
- **Dependencias** — grafo de qué skills/agents/tools se necesitan entre sí.
- **Recomendador** — dada una tarea NL, devuelve el `agent+skill+harness+model` óptimo.
- **Caché** — resultados recientes de recomendador y discovery.
- **API** — endpoint único (`POST /v1/ai-registry/recommend`) que el resto del sistema consume.

## Arquitectura

```
                  ┌──────────────────┐
                  │   12 Registries  │  (fuente)
                  └────────┬─────────┘
                           │ sync
                           ▼
                  ┌──────────────────┐
                  │   AI Registry    │  (índice + cards)
                  │  ─────────────   │
                  │  • agent cards   │
                  │  • skill cards   │
                  │  • mcp cards     │
                  │  • embeddings    │
                  │  • ranking       │
                  │  • historial     │
                  │  • recomendador  │
                  │  • caché         │
                  └────────┬─────────┘
                           │ query
                           ▼
                  ┌──────────────────┐
                  │   Consumidores   │  (orquestador, gateway, hub, panel)
                  └──────────────────┘
```

## Estructura

| carpeta | qué hay |
|---------|---------|
| `cards/`     | Definición + generador de Agent/Skill/MCP cards (json) |
| `ranking/`   | Algoritmo de scoring (spec + datos) |
| `recommender/` | Endpoint `/v1/ai-registry/recommend` (spec, no código) |
| `cache/`     | Política de caché y TTL por tipo de entry |
| `api/`       | OpenAPI spec del endpoint |
| `docs/`      | Decisiones arquitectónicas, ADRs |

## Estado

- 6/6 carpetas creadas.
- 0/6 specs escritos.
- Próximo paso: definir formato exacto de cada `*_card.json` y el contrato del recomendador.

## Owner

M3 — Director: Max.
