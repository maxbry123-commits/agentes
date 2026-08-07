# Control Layer (Wordflow)

Capa de control determinista · 90% código / 10% LLM.
Compatible con Temporal, OpenClaw, Hermes o cualquier agente vía Adapter + ENCHUFE.

## Estructura

```
control-layer/
├── workflow_core/     # Núcleo + DAG + Sheriff + Research
├── enchufe/           # ENCHUFE UNIVERSAL v2.0 validator
├── adapters/          # AgentAdapter + TemporalAdapter
├── registry/          # agents.yaml + extensions.yaml
├── extensions/        # MetaExtension
├── hf/                # (diferido)
├── goals/ · council/ · tribunal/ · loops/ · mission/ · contracts/
├── config/ · dsl/ · sheriff/ · errors/
└── main.py
```

## Cómo conectar un agente nuevo
1. Implementar `AgentAdapter` (7 funciones)
2. Registrar en `registry/agents.yaml`
3. Validar ficha con `enchufe.validator_v2.validar()`

PR: #3
