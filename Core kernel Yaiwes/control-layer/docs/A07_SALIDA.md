# A07 COMPLETA · InputBlock

## Entregables

- `inputblock/store.py` — append literal + chain + TTL
- `inputblock/reader.py` — verify_chain / ChainBrokenError
- `inputblock/vault.py` — backup CRITICO
- tests

## Checks

- [x] contenido literal sin interpretar
- [x] chain SHA-256 prev|content|seq
- [x] tamper → ChainBrokenError
- [x] TTL no borra CRITICO

## Siguiente

**A08** — Classifier CORRECTION / UPDATE / NEW_TASK
