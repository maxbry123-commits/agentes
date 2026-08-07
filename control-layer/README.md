# control-layer · Wordflow + Extensión kernel

Núcleo único de control determinista.

## Dualidad

| Cara | Entrypoint | Uso |
|------|------------|-----|
| **Wordflow** | `wordflow/entrypoint.py` | Trabajo diario: code y cualquier tarea |
| **Extensión kernel** | `extension/plugin_adapter.py` | Plugin de OpenClaw / TEAM / host |

Mismo motor. Sin imports de `vendor/openclaw`. Solo contratos + ABI.

## Estructura

```
control-layer/
├─ contracts/          # C00 + L1-L8 (85 schemas declarativos)
├─ contract_engine/    # fingerprint · threat · sentinela · compiler (0% LLM)
├─ sheriff/            # 5 estados GREEN…BLACK
├─ inputblock/         # literal + chain hash
├─ runtime/            # durable horas/días
├─ loops/              # CorrectionSet + fases
├─ council/            # I/O 12 goals (solo inv/diseño/plan/arq)
├─ extension/          # ABI + plugin_adapter
├─ wordflow/           # entrypoint trabajo
├─ registry/           # method/capability mínimo
└─ schemas/            # output_contract, etc.
```

## Estado tareas

- **A01** C00 + schema + capas — HECHO
- A02…A18 / B01…B10 — pendientes

## Ley

LLM nunca selecciona contratos. Sentinela/Router activa subconjuntos C01-C85.
