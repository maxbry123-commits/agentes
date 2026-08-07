# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.

## Estructura actual

```
control-layer/
├── workflow_core/     # Núcleo + DAG + Sheriff + Research + Mirror + Download
├── hf/                # 5 Spaces config + Router + Governor + Lifecycle + Queue + Repair + Context
├── goals/             # InputGoal / OutputGoal 12 campos
├── council/           # Council 12 roles
├── tribunal/          # Tribunal 6 roles
├── config/            # rules · registry · anti_escalation · policies
├── dsl/               # loader
├── sheriff/           # gate + anti_escalation checker
├── scripts/
└── main.py
```

## Cómo probar

```bash
cd control-layer
pip install -e ".[dev]"
PYTHONPATH=. pytest workflow_core/tests -q
PYTHONPATH=. python main.py
```

## SOURCE
G01-G03 + arquitectura final de hf.md + SALIDA_1_CAPA_CONTROL_PARTE_1/2/3

PR: #3
