# TAREAS_ACTUAL.md — Lista integrada
**Fecha:** 2026-08-18
**Fuente:** PIPELINE/52 (49 tareas) + extras chat + AUDIT-5 + HANDOFF T10–T49

## Estado V1
| Métrica | Valor |
|---------|--------|
| TOTAL | 49 |
| DONE | **15** (T01–T14 + T22) + AUDIT-5 S01–S10 |
| PEND | 34 |
| SIGUIENTE | **T15** — run_preflight |

## Reciente
| ID | Estado | Path | Commit |
|----|--------|------|--------|
| T10–T14 | DONE | kernel + C100 Fake | AUDIT5_S06_S10.md |
| T22 | DONE | `llm_control.py` | `3bd554e0…` |
| AUDIT-5 S06–S10 | PASS | `PIPELINE/AUDIT5_S06_S10.md` | `7527d6df…` |

## Extras chat
| ID | Tarea | Estado | Trazabilidad |
|----|-------|--------|--------------|
| T0 | 4 motors nativos + reception + knowledge | DONE | motors · reception |
| T2 | Reception/conversion motor | PENDIENTE | T0 reception |
| T2.1–T2.3 | SDPA/MCR/20M vía T2 | PENDIENTE | chat |
| CG | Code-gen DSL/DAG/schema | PENDIENTE | chat |
| ARCH | Arquitectura final (última) | PENDIENTE | chat |
| DEL | Delete mavis-deploy-keys | PENDIENTE | chat |
| AUDIT-5 | Forense cada 5 tareas | RECURRENTE · S01–S10 cerrado | PIPELINE/54 |

## Lista maestra V1 (49)
Ver PIPELINE/52 + HANDOFF. Orden: T13→T14→T22→**T15**. No claim C100.
