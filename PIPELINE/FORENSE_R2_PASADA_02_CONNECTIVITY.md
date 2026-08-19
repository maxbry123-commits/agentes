# FORENSE R2 — PASADA 02 CONNECTIVITY

Cadena: DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT_CONSUMED → BEHAVIOR_VERIFIED

## Reception (la cadena que fallaba en R1)

```
inbox convert                 WIRED
  ↑ import
kernel.reception.convert      WIRED
  ↑
handle_message / KernelExtMotor  WIRED
  ↓
ingest()
  → compile_or_reason         INVOKED (WIRED)
  → classify_task             INVOKED (WIRED)
  → locate_phase              INVOKED (WIRED, wrote=False)
  → enchufe_gate              INVOKED (WIRED; ok depende de ficha on disk)
  → context_pack              solo si instance_id
  → git apply                 GAP (diseño: apply externo)
```

OUTPUT_CONSUMED de fase = **NO** (no escribe). Eso es GAP consciente `CONN.ingest_writes_phase`.

## Otras cadenas

| Cadena | R1 | R2 |
|--------|----|----|
| Fake E2E → run_code_path | STUB dry | WIRED_NO_PASS (invoca, BLOCK) |
| C-19 → standards | WIRED | WIRED |
| Loop → gateway | WIRED_STUB | igual |
| Loop → run_code_path | PARTIAL | PARTIAL |
| runner → gateway | GAP | GAP (no se cierra: DENY vendor) |
| audit_to_plan | GAP | GAP |
| force/HOLD/token_ref | WIRED | WIRED |

## Veredicto R2 P2

Reception hasta EXECUTED de compiler/fase/plugin: **PASS parcial**.  
Sistema completo: **FAIL** (apply, loop→C-19, audit_to_plan).

CORE-07 repo = aún no True.
