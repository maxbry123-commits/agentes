# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.

## Estructura

```
control-layer/
├── workflow_core/     # Núcleo + DAG + Sheriff + Research (T-001..T-003)
├── config/            # rules.yaml · registry.json · task.example.json
├── dsl/               # loader.py
└── sheriff/           # gate.py
```

## Reglas
- Nunca from-scratch · solo adaptar SOURCE
- ≤200 LOC por archivo
- Temporal se conecta después (HF1)

PR: #3
