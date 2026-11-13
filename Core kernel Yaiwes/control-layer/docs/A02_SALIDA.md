# A02 COMPLETA · fingerprint + threat + risk_matrix

## Entregables

- `contract_engine/fingerprint.py` — 7 booleanos + hash sha256 estable
- `contract_engine/threat.py` — risk_score 0-10 + band + elevación de op_type
- `contract_engine/risk_matrix.yaml` — umbrales FIJOS (no adaptive)
- `contract_engine/tests/test_fingerprint_threat.py`

## Checks

- [x] 0% LLM
- [x] mismo input → mismo fingerprint_hash
- [x] WRITE + api_key → suggested_op_type=CREDENTIAL_ACCESS
- [x] bands: normal / sheriff_check / quarantine

## Siguiente

**A03** — rules · graph · reverse · compiler
