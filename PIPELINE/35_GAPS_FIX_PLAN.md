# PIPELINE/35 — Plan cierre gaps + G1 Input canónico

**Fecha:** 2026-08-14  
**Repo:** maxbry123-commits/agentes  
**Precondición:** Auditoría 40/40 PASS (existencia). Gaps menores G-S* no bloqueantes.

---

## G1 · Input canónico (CERRADO en este doc)

### Decisión

| Artefacto | Rol |
|-----------|-----|
| **`schemas/input_contract.schema.json` + `engine/input_compiler.py`** | **CANÓNICO** — única entrada WAVE-0 para compilar objetivo/constraints/success |
| `schemas/input_block.schema.json` + flujos legacy asociados | **LEGACY / alias** — no usar en código nuevo; no borrar aún (compat) |

### Reglas

1. Todo bridge, facade, test nuevo y T25+ debe usar `compile_input_contract` / InputContract.  
2. Prohibido añadir campos solo a input_block sin espejo en InputContract.  
3. Si main_loop legacy lee input_block → adaptar vía bridge a Contract (G2–G3), no al revés.  
4. Gap **G-S1-01** → **RESUELTO** por esta decisión.

### Paths canónicos

- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/schemas/input_contract.schema.json  
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/input_compiler.py  

---

## Plan restante (salidas G2–G9)

| ID | Gap origen | Entrega | Pri |
|----|------------|---------|-----|
| G2 | G-S1-02 | `loop_bridge.py` contract→questions→goals→lock | P0 |
| G3 | G-S1-02 | bridge + echo/registers/classify/ping | P0 |
| G4 | G-S4-02 / G-S3-05 | `execution_facade.py` resource vs engine→Bus | P0 |
| G5 | G-S4-02 | facade no engine bypass desde parallel payload | P0 |
| G6 | G-S4-03 | scope Guarded documentado + test | P1 |
| G7 | G-S2-02 / G-S2-03 | `policies/engine_attach.yaml` + ports exports | P1 |
| G8 | — | tests integración P0 | P0 |
| G9 | — | este PIPELINE actualizar “gaps closed” + unlock T25 | P0 |

**Skip P2 schemas** (gate/broker/lease/handoff.manifest_id): no salidas dedicadas salvo auditoría externa.

**Diferido:** T40 CI (G-S1-03), T3, HF/SSH real.

---

## Microflujo post-G1

```
InputContract (G1 CANÓNICO)
    → loop_bridge (G2–G3)
    → GoalLock + Classifier
    → execution_facade (G4–G5)
         ├ resource → Gate → Broker → Passport
         └ engine   → Manifest → Bus → Engine
    → ParallelRuntime (slots only)
    → [T25 Sheriff after G9]
```

---

## Estado

| Item | Estado |
|------|--------|
| G1 InputContract canónico | **DONE** |
| G2–G9 | pendiente |
| T25+ | bloqueado hasta G9 |

**SIGUIENTE:** G2 `extensions/wordflow/engine/loop_bridge.py`  
