# FORENSE R3 — PASADA 02 CONNECTIVITY

Cadena exigida: DECLARED → REGISTERED → RESOLVED → INVOKED → EXECUTED → OUTPUT_CONSUMED → BEHAVIOR_VERIFIED

**Evidencia:** lectura de `convert.py`, `motor.py`, `bootstrap_fake.py`, catalogs v1.3.0/1.1.0 en `95eb881`.

## Reception (reconfirmada)

```
inbox convert.py                  WIRED (impl import fail-closed)
kernel.reception.convert          WIRED (LINK, no duplica lógica)
handle_message → ingest           WIRED (catalog CONN.handle_ingest)
KernelExtMotor.dispatch ingest    WIRED
  ingest()
    compile_or_reason             INVOKED (WIRED)
    classify_task + decision_gate INVOKED (WIRED)
    locate_phase                  INVOKED wrote=False (WIRED locate)
    enchufe_gate validate_ficha   INVOKED (WIRED; ok on-disk)
    context_pack                  solo si instance_id
    git apply                     GAP (CONN.ingest_writes_phase)
```

OUTPUT_CONSUMED de fase = NO. Contrato actual: locate-only.

## Cadenas restantes (sin cambio de code vs R2)

| Cadena | R2 | R3 |
|--------|----|----|
| Fake E2E → run_code_path | WIRED_NO_PASS | IGUAL — `context_verified=False`, `c19_pass=False` |
| C-19 → forensic_core | WIRED | IGUAL |
| Loop → IntelligenceGateway | WIRED_STUB | IGUAL |
| Loop → run_code_path | PARTIAL | IGUAL — 0 hits code-search en `extensions/maxbry_loop` |
| runner → vendor LLM | GAP | GAP (DENY) |
| audit_to_plan inject | GAP | GAP — RuntimeError sin inject |
| force / HOLD / token_ref | WIRED | no re-ejecutado; catalog WIRED |

## Nuevo borde (ya existía, ahora explicitado)

`ingest()`:
- `ok` = `converted.ok AND compiled.invoked`
- `hops_ok` = convert.ok AND (hop.ok OR hop.invoked) para compile/classify/phase/plugin

Plugin `ok=False` (FICHA_NOT_ON_DISK) **no** tumba `ingest.ok`. FAIL-closed incompleto para PLUGIN.

## Veredicto R3 P2

Reception hasta EXECUTED compiler/fase/plugin: **PASS parcial**.
Sistema completo: **FAIL** (apply, loop→C-19, audit_to_plan, gateway vendor).

CORE-07 repo = False.
