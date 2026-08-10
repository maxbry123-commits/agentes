# PIPELINE 20 — CONTROL LAYER FASE 1 (CERRADA 100%)

```
fecha: 2026-08-09
status: COMPLETED 100%
repo: maxbry123-commits/agentes
MOTOR_RANGE: e36eba91 → 4d9c112c
CLOSE: b83f4170 · HYGIENE: 8a11ccb0 · G-DOC: d6b8755 · CI: (este)
```

---

## 0. ALCANCE

### FASE1_MVP (claim A1–A11)
```
control/ sheriff/ rules/ policies/
contracts/C00 + C01–C08 (semillas)
ficha.v2.json manifest.yaml
tests/ 8 suites · CI workflow · este PIPELINE
```

### LEGACY (no claim)
```
contract_engine/ evolution/ extension/ memory/ agents/ wordflow/
council/ hermes/ research/ skills/ loops/ input*/ execution/
runtime/ observability/ planning/ change/ format/ github/
registry/ schemas/ source_mirror/ docs/ bootstrap.py config.py
contracts/L1…L8 dirs (stubs preexistentes) + *.py auxiliares
```

---

## 1. MOTOR

```
normalize → fingerprint → threat → rules → graph → reverse
→ compile → sheriff.decide → gate → ALLOW|DENY|ESCALATE
```

LOC ~650 · LLM 0% · routing seed = 5 tipos

| Commit | Tarea |
|--------|-------|
| e36eba91 | A1 fingerprint |
| 14ac1676 | A2 threat |
| 76bd4c02 | A3 rules |
| 09e1a017 | A4 graph+reverse |
| 578c3280 | A5 compiler |
| 0c2f5858 | A6 C00+L1 seed |
| 11966d4b | A7 sheriff states |
| 95eaeb79 | A8 gate |
| dcd69138 | A9 enchufe v2 |
| 4d9c112c | A10 tests+CI |

---

## 2. G-DOC-1 · EQUIVALENCIA C01–C08 seed ↔ SALIDA4 L1

| Seed A6 | Nombre seed | SALIDA4 L1 (literal) | Acción |
|---------|-------------|----------------------|--------|
| C00 | governance | C00 Governance | OK literal |
| C01 | identity | C01 borde / identidad | B1 o alias |
| C02 | intent | C02 DbC / intención | B1 o alias |
| C03 | input_schema | C03 Schema entrada | parcial OK |
| C04 | output_schema | C04 Schema salida | parcial OK |
| C05 | auth_boundary | C05 frontera auth | parcial OK |
| C06 | scope_limit | C06 alcance | parcial OK |
| C07 | audit_trail | C07 trazabilidad | parcial OK |
| C08 | fail_closed | C08 fail-closed | parcial OK |

---

## 3. FASE 2 — CONTRATOS (B0 obligatorio primero)

| ID | Entrega |
|----|----------|
| **B0** | routing **13 tipos** + modificadores §19 |
| B1 | L2 C09–C22 + reescritura L1 literal |
| B2 | L3 C23–C32 |
| B3 | L4 C33–C41 |
| B4 | L5 C42–C50 |
| B5 | L6 C51–C55 Evolution |
| B6 | L7 C56–C81 |
| B7 | L8 C82–C85 ABI YAML |
| B8 | tests cobertura + claim |

---

## 4. FASE 3 / FUERA

| Pieza | Fuente | Fase |
|-------|--------|------|
| dsl/ schemas/ registry/ | CAPA_CONTROL_1 | F3 |
| reasoning/ + 44 gates | SALIDA6 | F3+ |
| Sandbox/API Slot | SALIDA7 | fuera |
| KER / 6 Ideas | SALIDA2/3 | fuera |
| validator_v2.py código | ENCHUFE v2 | F3 |

---

## 5. TESTS + G-DOC-5 CERRADO

```
CI_RUN_ID: 31354290850
URL: https://github.com/maxbry123-commits/agentes/actions/runs/31354290850
JOB_ID: 93350915605
HEAD_SHA: 4d9c112c4086ef731a808e20b19b6b2c6b1a643a
CONCLUSION: success
STATUS: completed
EVENT: push (A10)
STEPS: checkout · setup-python · install pyyaml · Run unit tests → success
CREATED: 2026-08-10T04:02:40Z
COMPLETED: 2026-08-10T04:02:52Z
```

Workflow: `.github/workflows/test-control-layer.yml`
Suites: fingerprint threat rules graph compiler sheriff gate integration

G-DOC-5: **CERRADO** (evidencia independiente CI verde).

---

## 6. ENCHUFE v2.0

```
artifact_id: wordflow.control_layer.mvp
categoria: transversal · etapa: T
abi_version: 2.0 · extension_type: control_layer
kernel_min: 1.0.0 · mount_mode: sidecar · load_priority: 10
llm_ratio: 0.0 · DENY · fail_closed: true
```

---

## 7. MICRODIAGRAMA

```
INPUT → normalize → fingerprint(7bool) → threat(0-10)
      → rules(routing5+bundles) → graph → reverse
      → CompilePlan → sheriff(5est) → gate → ALLOW|DENY|ESCALATE
```

---

## 8. G-DOC STATUS FINAL

| ID | Estado |
|----|--------|
| G-DOC-1 equivalencia L1 | CERRADO |
| G-DOC-2 B0 obligatorio | CERRADO |
| G-DOC-3 C82–C85 → B7 | CERRADO |
| G-DOC-4 Fase3/fuera | CERRADO |
| G-DOC-5 CI run | **CERRADO** run 31354290850 success |
