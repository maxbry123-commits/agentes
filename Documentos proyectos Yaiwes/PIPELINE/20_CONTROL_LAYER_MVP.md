# PIPELINE 20 — CONTROL LAYER MVP (A1–A11)

## Bloque cerrado
Motor fingerprint→threat→rules→graph→reverse→compiler + Sheriff 5 estados + gate + enchufe v2.0 + L1 contracts.

## Estructura materializada
```
control-layer/
├── control/
│   ├── fingerprint.py      # A1  7 bools 0% LLM
│   ├── threat.py           # A2  risk_score 0-10
│   ├── rules.py            # A3  when→add contracts
│   ├── graph.py            # A4  deps + topo
│   ├── reverse.py          # A4  conflict check
│   ├── normalizer.py       # A5  input canónico
│   └── compiler.py         # A5  pipeline completo
├── sheriff/
│   ├── states.py           # A7  GREEN..BLACK
│   ├── decision.py         # A7  ALLOW/DENY/ESCALATE
│   └── gate.py             # A8  checks fail_closed
├── rules/
│   ├── risk_matrix.yaml    # A2
│   ├── routing.yaml        # A3  5 ops
│   └── bundles.yaml        # A3  2 bundles
├── policies/
│   └── sheriff.yaml        # A8
├── contracts/
│   ├── C00_governance.yaml # A6
│   └── C01..C08 (L1)       # A6
├── ficha.v2.json           # A9  Enchufe Universal v2.0 completo
├── manifest.yaml           # A9  ABI 5 campos
└── tests/                  # A1-A10  ~45 tests
```

## Pipeline motor
```
normalize → fingerprint → threat → rules → graph → reverse → compile_plan → sheriff.decide → gate
```

## FUERA DE ESTE BLOQUE (explícito)
- dsl/ schemas/ registry/
- contracts L2–L8 completos
- enchufe/validator_v2.py completo
- 44 gates / reasoning real
- Sandbox Broker · API Slot Pool · Resource Governor
- KER / Idea 6 · Agent Plane
- Publisher GitHub · Acquire-OS

## Tests
fingerprint 8 · threat 5 · rules 6 · graph 5 · compiler 5 · sheriff 5 · gate 5 · integration 6 = 45

## CI
.github/workflows/test-control-layer.yml

## Commits A1–A10
A1 e36eba91 · A2 14ac1676 · A3 76bd4c02 · A4 09e1a017 · A5 578c3280
A6 0c2f5858 · A7 11966d4b · A8 95eaeb79 · A9 dcd69138 · A10 4d9c112c
