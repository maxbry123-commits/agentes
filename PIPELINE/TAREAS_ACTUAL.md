# TAREAS_ACTUAL.md — Lista integrada
**Fecha:** 2026-08-18
**Fuente:** PIPELINE/52 (49 tareas) + extras chat + AUDIT-5 + HANDOFF T10–T49

## Estado V1
| Métrica | Valor |
|---------|--------|
| TOTAL | 49 |
| DONE | **16** (T01–T15 + T22) + AUDIT-5 S01–S10 |
| PEND | 33 |
| SIGUIENTE | **T16** — run_context_pack |

## Reciente
| ID | Estado | Path | Commit |
|----|--------|------|--------|
| T22 | DONE | `llm_control.py` | `3bd554e0…` |
| T15 | DONE | `preflight.py` | `d2d9499e…` |

## Extras chat
| ID | Tarea | Estado | Trazabilidad |
|----|-------|--------|--------------|
| T0 | 4 motors nativos + reception + knowledge | DONE | motors · reception |
| T2 | Reception/conversion motor | PENDIENTE | T0 reception |
| T2.1–T2.3 | SDPA/MCR/20M vía T2 | PENDIENTE | chat |
| CG | Code-gen DSL/DAG/schema | PENDIENTE | chat |
| ARCH | Arquitectura final (última) | PENDIENTE | chat |
| DEL | Delete mavis-deploy-keys | PENDIENTE | chat |
| AUDIT-5 | Forense cada 5 | RECURRENTE · S01–S10 cerrado | PIPELINE/54 |

## Lista maestra V1 (49)
Ver PIPELINE/52 + HANDOFF. Orden: T13→T14→T22→T15→**T16**. No claim C100.
