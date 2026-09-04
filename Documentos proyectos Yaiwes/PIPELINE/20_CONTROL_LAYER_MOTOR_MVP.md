# PIPELINE 20 — Control Layer Motor MVP (A1–A10)

## Objetivo del bloque
Motor determinista fingerprint → threat → rules → graph → reverse → compiler + Sheriff 5 estados + gate.
Capa de Control parcial (no cierra toda CAPA_CONTROL_1).

## Pipeline horizontal
```
INPUT → normalizer → fingerprint(7bool) → threat(0-10) → rules(routing+bundles)
      → graph(topo) → reverse → compiler(CompilePlan) → sheriff.decide → gate → ALLOW|DENY|ESCALATE
```

## Estructura materializada
```
control-layer/
├── manifest.yaml              # ABI 5 campos
├── ficha.v2.json              # Enchufe Universal v2.0 completo
├── control/
│   ├── fingerprint.py         # A1 ≤120
│   ├── threat.py              # A2 ≤100
│   ├── rules.py               # A3 ≤140
│   ├── graph.py + reverse.py  # A4 ≤160
│   ├── normalizer.py          # A5
│   └── compiler.py            # A5
├── rules/
│   ├── risk_matrix.yaml
│   ├── routing.yaml           # 5 ops seed
│   └── bundles.yaml           # 2 bundles
├── contracts/
│   ├── C00_governance.yaml
│   └── C01..C08 (L1)
├── sheriff/
│   ├── states.py              # GREEN..BLACK
│   ├── decision.py
│   └── gate.py
├── policies/sheriff.yaml
└── tests/ (8 módulos, 45 tests)
```

## FUERA DE ESTE BLOQUE (explícito)
- dsl/ schemas/ registry/
- contracts L2–L8 completos
- enchufe/validator_v2.py completo
- 44 gates / reasoning real
- Sandbox Broker · API Slot Pool · Resource Governor
- KER / Idea 6 · Agent Plane
- Publisher GitHub · Acquire-OS

## Invariantes respetados
- 0% LLM en núcleo (llm_ratio=0.0, runtime_type=compute)
- fail_closed=true
- 1 motor + YAML contracts (no 85 módulos)
- ≤300 LOC/archivo
- Separación Control ≠ KER ≠ Agent Plane

## Commits A1–A10
| ID | Commit (short) | Entrega |
|----|----------------|---------|
| A1 | e36eba91 | fingerprint |
| A2 | 14ac1676 | threat + risk_matrix |
| A3 | 76bd4c02 | rules + routing + bundles |
| A4 | 09e1a017 | graph + reverse |
| A5 | 578c3280 | compiler + normalizer |
| A6 | 0c2f5858 | C00 + L1 C01-C08 |
| A7 | 11966d4b | sheriff states + decision |
| A8 | 95eaeb79 | gate + policy |
| A9 | dcd69138 | ficha.v2 + manifest ABI |
| A10| 4d9c112c | integration + CI |

## Tests
45 tests locales OK (fingerprint/threat/rules/graph/compiler/sheriff/gate/integration).
CI: .github/workflows/test-control-layer.yml
