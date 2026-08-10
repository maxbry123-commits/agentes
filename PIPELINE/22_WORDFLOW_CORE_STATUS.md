# PIPELINE 22 — Wordflow Core Status (WAVE2)

**llm_control:** DENY  
**Extensión:** `extensions/wordflow/`

## Entregado A-WF-01 … A-WF-10

| ID | Entrega | Estado |
|----|---------|--------|
| A-WF-01 | InputBlock schema + normalizer | DONE |
| A-WF-02 | Goals 12IN/12OUT + extractor | DONE |
| A-WF-03 | Refute L1-L3 + Repair R1-R6 | DONE |
| A-WF-04 | Sentinel schema/quality | DONE |
| A-WF-05 | Council of 12 | DONE |
| A-WF-06 | main_12 loop runner | DONE |
| A-WF-07 | entrypoint + manifest + contracts | DONE |
| A-WF-08 | VersionSelector + CI workflow | DONE |
| A-WF-09 | state_store + audit integration | DONE |
| A-WF-10 | Cursor techniques hooks | DONE |

## Flujo

```
InputBlock → normalize → goals_in → refute → repair
    → sentinel → council → tasks → goals_out → checkpoint
```

## Tests

- wordflow suite: 57 tests offline
- CI: `.github/workflows/test-wordflow.yml`

## Fuera de WAVE2 (siguientes)

- A-SE Source Evolution / VersionPin motor (WAVE4+)
- A-DEP GitHub Publisher C10 (WAVE6)
- Fase 4 loops Minimax/Kimi
