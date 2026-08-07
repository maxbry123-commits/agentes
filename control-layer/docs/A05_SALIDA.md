# A05 COMPLETA · Sheriff 5 estados + shadow ORANGE

## Entregables

- `sheriff/estados.py` — GREEN YELLOW ORANGE RED BLACK
- `sheriff/shadow.py` — ledger + promote_candidate (C55)
- `sheriff/gate.py` — Sentinela → Verdict (+ shadow append)
- `sheriff/tests/test_sheriff.py`

## Prioridad de estados

BLACK > RED > ORANGE > YELLOW > GREEN

## Checks

- [x] GREEN path normal ejecuta
- [x] RED block_execution no ejecuta
- [x] ORANGE shadow_only + ledger
- [x] promote exige provenance + test + trust
- [x] BLACK critical / evidence missing

## Siguiente

**A06** — Declarar 73/85 YAML + impl_ref
