# PIPELINE 20 — CONTROL LAYER FASE 1 (CERRADA)

```
fecha: 2026-08-09
bloque: control-layer MVP
fase: 1 / motor + C00 + L1 + Sheriff + enchufe v2
status: COMPLETED
repo: maxbry123-commits/agentes
```

---

## 1. QUÉ SE MATERIALIZÓ (A1–A10)

```
normalize → fingerprint → threat → rules → graph → reverse → compile → sheriff.decide → gate
```

| ID | Path | LOC | Tests |
|----|------|-----|-------|
| A1 | control/fingerprint.py | 100 | 8 |
| A2 | control/threat.py + rules/risk_matrix.yaml | 99 | 5 |
| A3 | control/rules.py + routing.yaml + bundles.yaml | 100 | 6 |
| A4 | control/graph.py + reverse.py | 125 | 5 |
| A5 | control/compiler.py + normalizer.py | 82 | 5 |
| A6 | contracts/C00 + C01–C08 | 9 yaml | — |
| A7 | sheriff/states.py + decision.py | 131 | 5 |
| A8 | sheriff/gate.py + policies/sheriff.yaml | 114 | 5 |
| A9 | ficha.v2.json + manifest.yaml (Enchufe v2.0 completo) | — | — |
| A10 | tests/test_integration.py + CI workflow | 61 | 6 |
| **Total motor** | | **~650** | **45** |

Commits clave:
- A1 e36eba91 · A2 14ac1676 · A3 76bd4c02 · A4 09e1a017
- A5 578c3280 · A6 0c2f5858 · A7 11966d4b · A8 95eaeb79
- A9 dcd69138 · A10 4d9c112c

---

## 2. ENCHUFE v2.0 (A9)

```
artifact_id: wordflow.control_layer.mvp
categoria: transversal · etapa: T
abi_version: 2.0 · extension_type: control_layer
kernel_min: 1.0.0 · mount_mode: sidecar · load_priority: 10
ejecucion.runtime_type: compute · llm_ratio: 0.0
seguridad.sandbox: process · fail_closed: true
```

Ficha cumple required schema v2.0:
artifact_id, version, estado, categoria, etapa, contrato, ejecucion, seguridad, firma.

---

## 3. FUERA DE FASE 1 (explícito)

- dsl/ · schemas/ · registry/
- contracts L2–L8 (C09–C85) completos
- C82–C85 como YAML de contrato (ABI montaje) — solo campos en ficha A9
- 44 gates / reasoning real
- Sandbox Broker · API Slot Pool · Resource Governor Python
- KER / Idea 6 · Agent Plane
- validator_v2.py completo (schema existe en docs; código diferido)
- routing 13 tipos completos (A3 seed = 5 tipos MVP)

---

## 4. FASE 2 — CONTRATOS RESTANTES (plan numerado)

| ID | Entrega | Notas |
|----|----------|-------|
| B0 | routing.yaml → 13 tipos + modificadores §19 | cierra G3 auditoría |
| B1 | L2 C09–C22 | Interface extendida |
| B2 | L3 C23–C32 | |
| B3 | L4 C33–C41 | Network/IO |
| B4 | L5 C42–C50 | Security/Evidence |
| B5 | L6 C51–C55 | Evolution |
| B6 | L7 C56–C81 | Extended + Research (subgrupos) |
| B7 | L8 C82–C85 ABI YAML + enlace ficha A9 | Mount/Lifecycle/Loader |
| B8 | tests cobertura contratos + claim | |

---

## 5. MICRODIAGRAMA HORIZONTAL

```
INPUT → normalize → fingerprint(7bool) → threat(0-10)
      → rules(routing+bundles) → graph(topo) → reverse
      → CompilePlan → sheriff.decide(5est) → gate(fail_closed)
      → ALLOW|DENY|ESCALATE
```

---

## 6. TRAZABILIDAD DOCS → CÓDIGO

| Fuente | Materializado en |
|--------|------------------|
| SALIDA4 §14 pipeline | A1–A5 compiler |
| SALIDA4 §16 risk | A2 risk_matrix.yaml |
| SALIDA4 §20 Sheriff | A7–A8 |
| SALIDA4 C00+L1 | A6 |
| ENCHUFE v2.0 FABLES | A9 ficha.v2.json |
| CAPA_CONTROL_1 estructura | control/ contracts/ sheriff/ rules/ policies/ |
| APORTES_3 1 motor + YAML | cumple (no 85 módulos) |
| UOOS frontera reasoning | reasoning/ no tocada (fuera) |

---

## 7. ANTI-SOBREINGENIERÍA

- 0% LLM en núcleo (llm_ratio=0, LLM_CONTROL=DENY)
- 1 motor, no 85 módulos Python
- ≤300 LOC/archivo respetado
- Governor/Sandbox/KER fuera
- Sin lexer/parser propio
