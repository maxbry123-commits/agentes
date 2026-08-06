# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.

## Estructura

```
control-layer/
├── workflow_core/     # Núcleo + DAG + Sheriff + Research Engine
├── config/            # rules.yaml · registry.json · task.example.json
├── dsl/               # loader.py
├── sheriff/           # gate.py
└── main.py            # entry point (load → DAG → Sheriff)
```

## Componentes clave
- WorkflowStateMachine (G1)
- DeterministicSheriff + DAGValidator + DAGPatch (G3)
- ResearchEngine + Resolver + ContextBuilder (G2)
- SandboxProvider / MemoryProvider (Protocol stubs)

## Reglas
- Nunca from-scratch · solo adaptar SOURCE
- ≤200 LOC por archivo
- Temporal se conecta después (HF1)

PR: #3
