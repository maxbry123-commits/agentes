# OPS SIM R5 — 3 simulaciones (sin C100)

**HEAD ancla:** ver commit `feat: UI provisional wired to ingest+agents`
**Contrato:** offline / DENY vendor. No React. No ROUTER_URL live.

## Cadena auditada

```
UI provisional (ui_gateway.plugin wire_kernel=True)
  → handle_message(action=ingest)
      → reception.ingest (compiler + classify + locate + plugin)
  → EngineRegistry.reason(openclaw, hermes) via MockIntelligenceGateway
  → bootstrap_fake → run_code_path(context_verified=False) → BLOCK
```

| CONN | Status |
|------|--------|
| ui_kernel | WIRED |
| ui_agents | WIRED_STUB |
| path_gateway | WIRED_DENY |
| bootstrap_fake_path | WIRED_NO_PASS |

## Simulaciones

| ID | Qué prueba | PASS esperado |
|----|------------|---------------|
| SIM-1 | UI → ingest | ROUTED o PARTIAL; no vendor |
| SIM-2 | UI → OpenClaw+Hermes stubs | ambos invoked STUB |
| SIM-3 | UI → Fake E2E | ok=True y c19_pass=False |

## Veredicto máquina

```
operational: OFFLINE_STUB   (si las 3 ok)
C100: NO
V1 100%: NO
live agents / live UI host: NO
```

Runner: `python -m wordflow_kernel.ops_sim`
UI one-shot: `python -m wordflow_kernel.ui_gateway.provisional "objective: …"`
