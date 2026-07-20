# Recomendador — el corazón del AI Registry

> "Dada una tarea en lenguaje natural, devolver el `(agent, skill, harness, model)` óptimo."

## Input
```json
{
  "task": "auditar este repo de github y generar un PR con un fix",
  "context": {
    "user_id": "maxbry",
    "project": "agentes",
    "constraints": ["no tocar VPS", "max 6 líneas de respuesta"]
  }
}
```

## Output
```json
{
  "ranked": [
    {
      "agent":   "mimo-code",
      "skill":   "git",
      "harness": "daytona",
      "model":   "claude-3.7-sonnet",
      "score":   0.92,
      "rationale": "code-task → Daytona per routing rule K; mimo-code por tier gold; skill git requerida para PR",
      "estimated_cost_usd": 0.05,
      "estimated_latency_ms": 14000
    },
    {
      "agent":   "claude-code",
      "skill":   "git",
      "harness": "e2b",
      "model":   "claude-3.7-sonnet",
      "score":   0.84,
      "rationale": "alternativa equivalente, e2b por defecto si Daytona no disponible",
      "estimated_cost_usd": 0.07,
      "estimated_latency_ms": 22000
    }
  ],
  "blocked_by_policies": ["pol.no-real-install"],
  "warnings": []
}
```

## Algoritmo (spec — no código todavía)

1. **Embedding** del `task` + `context` (provider: pgn vector store + reranker).
2. **Match capacidades** → top-K del `06-capability` registry.
3. **Expandir a implementations** → agents y skills que implementan esas capabilities.
4. **Filtrar por policies** → descartar combinaciones que violan `12-policy`.
5. **Routing de harness** → aplicar las reglas de la sección K del prompt M3.
6. **Selección de modelo** → `11-model`, considerando quota y costo.
7. **Ranking** → score = `relevancia * 0.5 + éxito_histórico * 0.3 + (1 - costo_normalizado) * 0.2`.
8. **Output** → top-3 candidatos con rationale.

## Routing rules (referenciadas desde `10-harness`)

| tipo de tarea | harness |
|---------------|---------|
| code / programming | daytona |
| skill aislada       | e2b |
| gpu / inferencia    | hf-space |
| rápida en borde     | cloudflare-sb |
| default             | sandbank |

## Tareas pendientes
- [ ] Elegir modelo de embeddings (¿MiniMax-embed? ¿sentence-transformers local?).
- [ ] Definir tabla de `éxito_histórico` (leer de `08-memory`).
- [ ] Endpoint de retroalimentación: cuando el usuario acepta/rechaza la recomendación, ajustar pesos.
- [ ] Tests de acceptance: 20 tareas reales con respuesta esperada.
