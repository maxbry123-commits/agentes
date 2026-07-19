---
# Orquestador Universal v1.0

Conecta el chat a cualquier agente mediante **sandboxes aislados**.
El orquestador NO toca código interno de los agentes.

## 10 Loops · 16 Razonamiento · 16 Recuperación · 10 Goals

Ver `docs/ARCHITECTURE.md`, `docs/LOOP_ENGINE.md`, `docs/PIPELINE_MASTER.md`.

## Estructura

```
orchestrator-universal/
├── docs/                       (5 MD)
├── orchestrator/
│   ├── orchestrator.py         loop engine (10 loops)
│   ├── state.py                workflow_state atómico
│   ├── sentinel.py             observabilidad
│   ├── sandbox.py              docker wrapper + supervisor
│   ├── router.py               asignación de sandboxes
│   ├── sheriff.py              6 gates + validador + verificador
│   ├── juez.py                 3 simulaciones + baseline
│   ├── consensus.py            2-de-3
│   ├── repair.py               F1-F16
│   └── agents/
│       ├── base.py
│       ├── claude_code.py
│       ├── mimo_code.py
│       └── opencode.py
├── tests/test_mvp.py
├── main.py
└── requirements.txt
```

## Uso

```bash
pip install -r requirements.txt
python main.py --demo
```

O con tu propia plantilla:

```bash
python main.py --template mi_template.json
```

Plantilla:

```json
{
  "objetivo": "...",
  "planificar": ["L1", "L2", ...],
  "organizar": {"L1": "Orquestador", ...},
  "tareas": ["..."],
  "metas": ["..."],
  "proposito": "...",
  "refutaciones": ["..."],
  "consensus": "fast"
}
```

## Tests

```bash
pytest tests/ -v
```
