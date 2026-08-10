# PIPELINE 26 — Fase 2 Contratos B0–B8

**llm_control:** DENY

## Entregas

| ID | Entrega | Estado |
|----|---------|--------|
| B0 | routing 13 tipos + modifiers + bundles | DONE |
| B1 | L2 C09–C22 | DONE (14) |
| B2 | L3 C23–C32 | DONE (10) |
| B3 | L4 C33–C41 | DONE (9) |
| B4 | L5 C42–C50 | DONE (9) |
| B5 | L6 C51–C55 evolution | DONE (5) |
| B6 | L7 C56–C81 | DONE (26) |
| B7 | L8 C82–C85 ABI | DONE (4) |
| B8 | coverage tests + claim | DONE |

## Cobertura

- **C00–C85 = 86 contratos** en `control-layer/contracts/`
- L0/L1 seed: C00–C08
- L2–L8: carpetas L2…L8
- routing.yaml: 13 operation types
- modifiers.yaml: 6 modifiers (§19)
- C82–C85 critical + links enchufe v2

## Tests

- `control-layer/tests/test_contracts_coverage.py` — 8 PASSED

## Fuera

- Runtime enforcement full de cada check_*
- dsl/schemas/registry Fase 3
