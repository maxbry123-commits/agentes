# TAREAS_ACTUAL.md — Lista integrada
**Fecha:** 2026-08-18
**Fuente:** PIPELINE/52 (49 tareas) + extras chat + AUDIT-5 S01–S05 + HANDOFF T10–T49

## Estado V1
| Métrica | Valor |
|---------|--------|
| TOTAL | 49 |
| DONE | **9** (T01–T09) + AUDIT-5 S01–S05 |
| PEND | 40 (T10–T49) |
| SIGUIENTE | **T10** — ficha_loader ADAPT (publicado, forense pendiente) |

## T10
| Campo | Valor |
|-------|--------|
| Estado | PUBLISHED_AND_VERIFIED pending FORENSIC |
| Path | `extensions/wordflow_kernel/ficha_loader.py` |
| Nota | PATCH3 B1: `artifact_id`/`abi_version` |

## Extras chat
| ID | Tarea | Estado | Trazabilidad |
|----|-------|--------|--------------|
| T0 | 4 motors nativos + reception + knowledge | DONE | motors · reception |
| T2 | Reception/conversion motor | PENDIENTE | T0 reception |
| T2.1 | SDPA vía T2 | PENDIENTE | chat |
| T2.2 | MCR vía T2 | PENDIENTE | chat |
| T2.3 | 20M contexto vía T2 | PENDIENTE | chat |
| CG | Code-gen DSL/DAG/schema | PENDIENTE | chat |
| ARCH | Arquitectura final (ultima) | PENDIENTE | chat |
| DEL | Delete mavis-deploy-keys | PENDIENTE | chat |
| AUDIT-5 | Forense cada 5 tareas | RECURRENTE · S01–S05 cerrado | PIPELINE/54 · AUDIT5_S01_S05.md |

## Lista maestra V1 (49)
Ver PIPELINE/52 + HANDOFF_V1_T10_T49. **T01–T09 DONE.** Siguiente: **T10** (paso 3 forense). No claim C100.
