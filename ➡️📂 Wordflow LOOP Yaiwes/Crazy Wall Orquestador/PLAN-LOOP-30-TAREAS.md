# PLAN LOOP — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP` · cola `1×1`.
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## BLOQUE 3 PASOS — CERRADO
| Paso | Estado | Ubicación actual |
|---|---|---|
| 1 — Índice | VERIFIED_CLOSED | `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme indice agentes.md` |
| 2 — Cableado | VERIFIED_CLOSED_WIRING | `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/` + `wordflow_loop/contracts/ficha.agent_fleet.v2.json` |
| 3 — verificación histórica | VERIFIED_CLOSED | evidence `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`; run `34406268016`; job `102649876845` |

## FLEET
18 bindings. Council12=12. Runtimes no configurados fallan cerrado. Hermes, Muse/Glimmer y Goose siguen `EXTERNAL_NOT_VENDORED`.

## ROUTER MVP
`➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Prioridad global: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS. Verifica disponibilidad y hace failover por API/key/modelo.

## MIGRACIÓN DE ALCANCE
Commit `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`. Índice retirado del repo motor por `a17e1572b9df41954597fc8c66b390c47800d081`. Registry externo preexistente restaurado al blob `ce40e9afd13fdbea22609fe57807566770dfc1b0`.

## SIGUIENTE
Solo pruebas reales de agentes cuando estén autorizadas y existan valores API/MCP/command reales. No existe trabajo autorizado fuera de la raíz Wordflow.
