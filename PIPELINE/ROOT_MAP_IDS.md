# ROOT MAP IDs canónicos — S03 / T03
**Fecha:** 2026-08-17

## Convención
`[WF.xx]` → `[FILE.xxx]` → path real → `[FN.x]` → `[CONN]` → `[TOOL]` → `[SCHEMA]`

Estados: IMPLEMENTED | PARTIAL | MISSING | PENDING | PLACEHOLDER | DEPRECATED | EXTERNAL | UNKNOWN

## Mapa raíz

| ID | Path / Componente | Tipo | Estado |
|----|-------------------|------|--------|
| WF.00 | KERNEL (wordflow_kernel/) | kernel | PARTIAL |
| WF.01 | extensions/wordflow/ | extension | IMPLEMENTED |
| WF.02 | extensions/wordflow_kernel/ | extension | PARTIAL |
| WF.03 | control-layer/ | control | PARTIAL |
| WF.04 | PIPELINE/ | docs | IMPLEMENTED |
| FILE.001 | extensions/wordflow/engine/ | dir | IMPLEMENTED |
| FILE.002 | extensions/wordflow/accounts/ | dir | IMPLEMENTED |
| FILE.003 | extensions/wordflow/connectors/ | dir | IMPLEMENTED |
| FILE.004 | extensions/wordflow_kernel/bootstrap_v1.py | file | IMPLEMENTED |
| FILE.005 | extensions/wordflow_kernel/gateway/ | dir | PARTIAL |
| FILE.006 | extensions/wordflow_kernel/engines/ | dir | PARTIAL |
| FILE.007 | extensions/wordflow_kernel/resources/ | dir | PARTIAL |
| FILE.008 | extensions/wordflow/motors/ | dir | IMPLEMENTED (T0) |
| FILE.009 | extensions/wordflow/reception/ | dir | IMPLEMENTED (T0) |
| FILE.010 | PIPELINE/55_LISTA_COMPLETA_V1.md | file | IMPLEMENTED |
| FILE.011 | README_ARQUITECTURA.md | file | IMPLEMENTED (T02) |
| CONN.001 | AccountResolver | connector | PARTIAL |
| CONN.002 | github_external | connector | PARTIAL |
| SCHEMA.001 | ficha.v2.json | schema | IMPLEMENTED |
| SCHEMA.002 | input_block.schema.json | schema | IMPLEMENTED |

## Instancias (futuro)
| ID | Notas |
|----|-------|
| INST.v1 | default (actual) |
| INST.* | spawn vía T09 |

## Connections (futuro T06)
Ver connect_catalog.json
