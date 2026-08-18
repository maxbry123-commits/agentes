# ROOT MAP IDs canónicos — S03 / T03
**Fecha:** 2026-08-18  
**Tarea:** T03 · ID→path estable  
**Fuente árbol:** extensions/* + PIPELINE + control-layer (repo agentes)

## Convención
`[WF.xx]` → `[FILE.xxx]` → path real → `[FN.x]` → `[CONN]` → `[TOOL]` → `[SCHEMA]`

Estados: IMPLEMENTED | PARTIAL | MISSING | PENDING | PLACEHOLDER | DEPRECATED | EXTERNAL | UNKNOWN

## Mapa raíz (WF)

| ID | Path / Componente | Tipo | Estado |
|----|-------------------|------|--------|
| WF.00 | KERNEL (`extensions/wordflow_kernel/`) | kernel | PARTIAL |
| WF.01 | `extensions/wordflow/` | extension | IMPLEMENTED |
| WF.02 | `extensions/wordflow_kernel/` | extension | PARTIAL |
| WF.03 | `control-layer/` | control | PARTIAL |
| WF.04 | `PIPELINE/` | docs | IMPLEMENTED |
| WF.05 | `extensions/maxbry_loop/` | extension | PARTIAL |
| WF.06 | `extensions/audit_forensic/` | extension | PARTIAL |
| WF.07 | `extensions/github_deploy/` | extension | PARTIAL |
| WF.08 | `extensions/github_publisher/` | extension | PARTIAL |
| WF.09 | `extensions/project_bootstrap/` | extension | PARTIAL |
| WF.10 | `extensions/source_evolution/` | extension | PARTIAL |
| WF.11 | `extensions/adapters/` | extension | PARTIAL |
| WF.12 | `extensions/knowledge/` | extension | PARTIAL |

## Archivos / dirs canónicos (FILE)

| ID | Path | Tipo | Estado |
|----|------|------|--------|
| FILE.001 | `extensions/wordflow/engine/` | dir | IMPLEMENTED |
| FILE.002 | `extensions/wordflow/accounts/` | dir | IMPLEMENTED |
| FILE.003 | `extensions/wordflow/connectors/` | dir | IMPLEMENTED |
| FILE.004 | `extensions/wordflow_kernel/bootstrap_v1.py` | file | IMPLEMENTED |
| FILE.005 | `extensions/wordflow_kernel/gateway/` | dir | PARTIAL |
| FILE.006 | `extensions/wordflow_kernel/engines/` | dir | PARTIAL |
| FILE.007 | `extensions/wordflow_kernel/resources/` | dir | PARTIAL |
| FILE.008 | `extensions/wordflow/motors/` | dir | IMPLEMENTED (T0) |
| FILE.009 | `extensions/wordflow/reception/` | dir | IMPLEMENTED (T0) |
| FILE.010 | `PIPELINE/55_LISTA_COMPLETA_V1.md` | file | IMPLEMENTED |
| FILE.011 | `README.md` (sección multi-instancia T02) | file | IMPLEMENTED (T02) |
| FILE.012 | `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md` | file | IMPLEMENTED |
| FILE.013 | `PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md` | file | IMPLEMENTED |
| FILE.014 | `PIPELINE/ROOT_MAP_IDS.md` | file | IMPLEMENTED (T03) |
| FILE.015 | `extensions/wordflow/standards/` | dir | IMPLEMENTED |
| FILE.016 | `extensions/wordflow/component_catalog.json` | file | IMPLEMENTED |
| FILE.017 | `extensions/wordflow/connect_catalog.json` | file | PARTIAL (T06 stub) |
| FILE.018 | `extensions/wordflow/ficha.v2.json` | file | IMPLEMENTED |
| FILE.019 | `extensions/wordflow/engine/code_path_runner.py` | file | IMPLEMENTED |
| FILE.020 | `extensions/wordflow/engine/programming_pipeline.py` | file | IMPLEMENTED |

## Conexiones (CONN)

| ID | Componente | Estado |
|----|------------|--------|
| CONN.001 | AccountResolver | PARTIAL |
| CONN.002 | github_external | PARTIAL |
| CONN.003 | connect_catalog list_connections | PENDING (T06) |

## Schemas (SCHEMA)

| ID | Path | Estado |
|----|------|--------|
| SCHEMA.001 | `extensions/wordflow/ficha.v2.json` | IMPLEMENTED |
| SCHEMA.002 | `extensions/wordflow/schemas/input_block.schema.json` | IMPLEMENTED |

## Instancias

| ID | Notas | Estado |
|----|-------|--------|
| INST.v1 | default (actual) | PARTIAL |
| INST.* | spawn vía T09 | PENDING |

## Nota X-Ray
Estados **no inventados como 100% IMPLEMENTED** sin árbol/code. T04 ampliará STATUS real por archivo bajo `extensions/*`.
