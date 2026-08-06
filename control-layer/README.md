# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.

## Estructura

```
control-layer/
├── workflow_core/     # Núcleo + DAG + Sheriff + Research Engine + Mirror + Download
├── config/            # rules.yaml · registry.json · task.example.json · policies/
├── dsl/               # loader.py
├── sheriff/           # gate.py
├── scripts/           # run_main.sh
└── main.py            # entry point (load → DAG → Sheriff)
```

## Cómo probar

```bash
cd control-layer
pip install -e ".[dev]"
PYTHONPATH=. pytest workflow_core/tests -q
PYTHONPATH=. python main.py
```

## Componentes clave
- WorkflowStateMachine (G1)
- DeterministicSheriff + DAGValidator + DAGPatch (G3)
- ResearchEngine + Resolver + ContextBuilder + Mirror + DeterministicDownloader (G2)
- SandboxProvider / MemoryProvider (Protocol stubs)

## Reglas
- Nunca from-scratch · solo adaptar SOURCE
- ≤200 LOC por archivo
- Temporal se conecta después (HF1)

PR: #3
