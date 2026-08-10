# PIPELINE 20 — CONTROL LAYER FASE 1 (CERRADA)

```
fecha: 2026-08-09
bloque: control-layer MVP Fase 1
status: COMPLETED (núcleo)
repo: maxbry123-commits/agentes
MOTOR_COMMITS: e36eba91 → 4d9c112c
CLOSE_COMMIT: b83f4170 (PIPELINE 20)
HYGIENE_COMMIT: (este) claim alcance
```

---

## 0. HIGIENE DE ALCANCE (auditoría CAPA2)

### FASE1_MVP — entregado A1–A11 (ÚNICO alcance del claim)

```
control-layer/
├── control/          # fingerprint threat rules graph reverse normalizer compiler
├── sheriff/          # states decision gate
├── rules/            # risk_matrix.yaml routing.yaml bundles.yaml
├── policies/         # sheriff.yaml
├── contracts/
│   ├── C00_governance.yaml
│   └── C01_*.yaml … C08_*.yaml   # semillas L1 (~280B c/u)
├── ficha.v2.json     # Enchufe v2.0 completo
├── manifest.yaml     # ABI 5 campos
└── tests/
    test_fingerprint|threat|rules|graph|compiler|sheriff|gate|integration.py
```

+ `.github/workflows/test-control-layer.yml`
+ `PIPELINE/20_CONTROL_LAYER_FASE1.md`

### LEGACY / FUERA DE FASE 1 — preexistente en control-layer/

**No forma parte del claim A1–A11.** No se borra sin autorización Director.

```
contract_engine/   # motor paralelo legado
evolution/ extension/ memory/ agents/ wordflow/
council/ hermes/ research/ skills/ loops/
input/ inputblock/ execution/ runtime/ observability/
planning/ change/ format/ github/ registry/ schemas/
source_mirror/ docs/ bootstrap.py config.py README.md
contracts/L1_interface … L8_abi/   # carpetas stub preexistentes
contracts/{budget,failure,goals,output_contract}.py  # legado
contracts/catalog.yaml schema_contract.json goals_*.yaml
```

L2–L8 dirs = **stubs preexistentes**, no entregables B1–B7.
Fase 2 (B0–B8) los reemplaza o formaliza; no cuentan como “entregados” aquí.

C01–C08 de A6 = **semillas finas** (identity/intent/…), no contratos literales SALIDA4 borde/Meyer.
Aceptados como seed; semántica completa → Fase 2 / revisión Director.

---

## 1. MOTOR (rango commits)

| Commit | Tarea |
|--------|-------|
| e36eba91 | A1 fingerprint |
| 14ac1676 | A2 threat + risk_matrix |
| 76bd4c02 | A3 rules + routing(5) + bundles |
| 09e1a017 | A4 graph + reverse |
| 578c3280 | A5 compiler + normalizer |
| 0c2f5858 | A6 C00 + C01–C08 |
| 11966d4b | A7 sheriff states + decision |
| 95eaeb79 | A8 gate + policy |
| dcd69138 | A9 ficha.v2 + manifest |
| 4d9c112c | A10 integration tests + CI |
| b83f4170 | A11 PIPELINE 20 |

Pipeline:
```
normalize → fingerprint → threat → rules → graph → reverse
→ compile → sheriff.decide → gate → ALLOW|DENY|ESCALATE
```

LOC motor ~650 · Tests locales 45 (8 suites) · LLM 0%

---

## 2. ENCHUFE v2.0

```
artifact_id: wordflow.control_layer.mvp
categoria: transversal · etapa: T
abi_version: 2.0 · extension_type: control_layer
kernel_min: 1.0.0 · mount_mode: sidecar · load_priority: 10
llm_ratio: 0.0 · llm_control: DENY · fail_closed: true
```

---

## 3. FASE 2 (plan, no ejecutada)

| ID | Entrega |
|----|----------|
| B0 | routing 13 tipos + modificadores §19 |
| B1 | L2 C09–C22 (formal, no stub) |
| B2 | L3 C23–C32 |
| B3 | L4 C33–C41 |
| B4 | L5 C42–C50 |
| B5 | L6 C51–C55 |
| B6 | L7 C56–C81 |
| B7 | L8 C82–C85 ABI YAML |
| B8 | tests cobertura + claim |

---

## 4. TESTS

Claim local: 45 OK en sandbox ejecutor.
CI workflow: `.github/workflows/test-control-layer.yml` presente.
Evidencia CI run independiente: **pendiente** (no verificada en esta auditoría).

---

## 5. MICRODIAGRAMA

```
INPUT → normalize → fingerprint(7bool) → threat(0-10)
      → rules(routing5+bundles) → graph(topo) → reverse
      → CompilePlan → sheriff(5est) → gate(fail_closed)
      → ALLOW|DENY|ESCALATE
```
