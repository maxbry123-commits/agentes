# TAREAS_ACTUAL.md — Lista integrada
**Fecha:** 2026-08-18
**Fuente:** PIPELINE/52 (49 tareas) + extras chat + AUDIT-5 S01–S05 + HANDOFF T10–T49

## Estado V1
| Métrica | Valor |
|---------|--------|
| TOTAL | 49 |
| DONE | **12** (T01–T12) + AUDIT-5 S01–S05 |
| PEND | 37 (T13–T49) |
| SIGUIENTE | **T13** — bootstrap_fake GoalLock→loop→code_path→deploy Fake |

## Reciente
| ID | Estado | Path | Commit |
|----|--------|------|--------|
| T10 | DONE | `ficha_loader.py` | `baa302f7…` |
| T11 | DONE | `bootstrap_multi.py` + `spawn.py` | `55d07000…` / `f330f4d9…` |
| T12 | DONE | `fail_closed.py` | `30da7837…` |

## Extras chat
| ID | Tarea | Estado | Trazabilidad |
|----|-------|--------|--------------|
| T0 | 4 motors nativos + reception + knowledge | DONE | motors · reception |
| T2 | Reception/conversion motor | PENDIENTE | T0 reception |
| T2.1 | SDPA vía T2 | PENDIENTE | chat |
| T2.2 | MCR vía T2 | PENDIENTE | chat |
| T2.3 | 20M contexto vía T2 | PENDIENTE | chat |
| CG | Code-gen DSL/DAG/schema | PENDIENTE | chat |
| ARCH | Arquitectura final (última) | PENDIENTE | chat |
| DEL | Delete mavis-deploy-keys | PENDIENTE | chat |
| AUDIT-5 | Forense cada 5 tareas | RECURRENTE · S01–S05 cerrado | PIPELINE/54 · AUDIT5_S01_S05.md |

## Lista maestra V1 (49)
Ver PIPELINE/52 + HANDOFF_V1_T10_T49. **T01–T12 DONE.** Siguiente: **T13**. No claim C100.
