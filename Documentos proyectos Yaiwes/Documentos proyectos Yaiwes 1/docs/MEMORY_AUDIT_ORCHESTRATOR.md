# Memory + Audit Orchestrator (osquestador)

TEAM SEALS · no toca `control-layer/`

## Rol
Orquesta **auditoría de snapshots de agentes** y **memoria de pins/estado** entre chats AI.

## Fuentes de verdad
- `agents/_state/*.json` — estado por agente
- `agents/<Id>/manifest.json` + `source/` + `distribution/`
- `docs/METHOD_ASYNC_ACQUIRE.md` — protocolo acquire
- `control-layer/` — Wordflow (solo lectura)

## Operaciones
1. `inventory` — lista agentes + status DONE/PENDING
2. `audit <Id>` — checklist 100% (pin, source SHA, dist pin o Release)
3. `memory-write` — actualiza `_state` + resumen en `memory/ledger.jsonl`
4. `memory-read` — últimos N eventos ledger
5. `resume` — 1 check por turno (async METHOD)

## Ledger
`memory/ledger.jsonl` líneas JSON: `{ts, op, agent, status, note}`

## CLI
```bash
python scripts/osquest.py inventory
python scripts/osquest.py audit Codex
python scripts/osquest.py memory-read 20
```
