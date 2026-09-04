# A04 COMPLETA · Sentinela/Router de schemas

## Entregable

`contract_engine/sentinela_router.py`

## Qué hace

1. Compila ContractSet (A03)
2. Mapea cada C* → procesos (`PROCESS_MAP`)
3. Ordena `process_plan` (fases de control)
4. Decide `sheriff_required` y `block_execution`
5. Expone `mode_hint`: wordflow | extension | dual

## Checks

- [x] READ_LOCAL → plan sin block
- [x] WRITE+secret → credential_gate + block_execution
- [x] 0% LLM
- [x] reutilizable por Wordflow y por ABI extensión

## Siguiente

**A05** — Sheriff 5 estados + shadow ORANGE
