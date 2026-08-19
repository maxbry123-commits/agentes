# TAREAS_ACTUAL.md — Lista integrada
**Fecha:** 2026-08-18
**Fuente:** PIPELINE/52 (49 tareas) + extras chat + AUDIT-5 S01–S05 + HANDOFF T10–T49

## Estado V1
| Métrica | Valor |
|---------|--------|
| TOTAL | 49 |
| DONE | **10** (T01–T10) + AUDIT-5 S01–S05 |
| PEND | 39 (T11–T49) |
| SIGUIENTE | **T11** — bootstrap multi-instance aware |

## T10
| Campo | Valor |
|-------|--------|
| Estado | **DONE** |
| Path | `extensions/wordflow_kernel/ficha_loader.py` |
| Commit | `baa302f7640d5de38e413ad03bce113f26b32da3` |
| Nota | PATCH3 B1: `artifact_id`/`abi_version`; forense gaps=0 |

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
Ver PIPELINE/52 + HANDOFF_V1_T10_T49. **T01–T10 DONE.** Siguiente: **T11**. No claim C100.
