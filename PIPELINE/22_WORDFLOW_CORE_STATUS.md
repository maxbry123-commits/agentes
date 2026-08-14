# PIPELINE 22 — Wordflow Core Status (WAVE2)

> **SUPERSEDED** — 2026-08-14  
> Este documento marcaba A-WF-01..11 como DONE al 100%.  
> **Fuente de verdad de gaps y plan residual:** [`PIPELINE/27_AUDIT_FORENSE_GAPS_Y_PLAN.md`](27_AUDIT_FORENSE_GAPS_Y_PLAN.md)  
> Estado real Wordflow: **PARTIAL ~78%** (core sí; faltan watchdog, supervisor, Arch/Code schemas, ficha.v2, G_OUT→Evidence).

**FINAL_COMMIT (histórico):** `51b977197502e5e2b23dd651a93f903931f70783`  
**Extensión:** `extensions/wordflow/`  
**llm_control:** DENY

## Entregado real (presente en GH)

| ID | Entrega | Estado real |
|----|---------|-------------|
| A-WF-01 | InputBlock schema + normalizer | PRESENTE |
| A-WF-02 | Goals 12IN/12OUT + extractor | PRESENTE |
| A-WF-03 | Refute L1-L3 + Repair R1-R6 | PRESENTE |
| A-WF-04 | Sentinel | PRESENTE |
| A-WF-05 | Council of 12 | PRESENTE |
| A-WF-06 | main_12 loop runner | PRESENTE |
| A-WF-07 | entrypoint + manifest + contracts | PRESENTE |
| A-WF-08 | VersionSelector + hooks | PRESENTE |
| A-WF-09 | state_store + audit integration | PRESENTE |
| A-WF-10 | Cursor techniques hooks | PRESENTE |

## Gaps residuales (ver PIPELINE 27 R1)

- watchdog.py + supervisor.py + policies/
- architecture_output / code_output schemas
- ficha.v2.json wordflow
- map G_OUT → EvidencePacket

## Tree presente

- engine/{input_normalizer,goals_extractor,refute_repair,sentinel,council,main_loop,entrypoint,version_selector,state_store,cursor_hooks}.py
- schemas/input_block.schema.json
- store/{goals_catalog,council_roles,main_12,cursor_techniques}.yaml
- contracts/C_WF_{INPUT,LOOP}.yaml
- tests/

**No usar este doc como claim COMPLETED.** Usar PIPELINE 27.
