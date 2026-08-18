# ARQUITECTURA WORDFLOW GLOBAL (REAL + enforcement P0)

**Repo:** maxbry123-commits/agentes  
**Fecha:** 2026-08-18  
**Fuente de verdad código:** `extensions/wordflow/**`, `extensions/wordflow_kernel/**`  
**Mapa forense programming:** `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`  
**Programming detallado:** `PIPELINE/WORDFLOW_PROGRAMMING_COMO_FUNCIONA.md`

---

## 1. Vista de capas

```
┌──────────────────────────────────────────────────────────┐
│ Callers: bootstrap_v1, code_path_smoke, (otros UNKNOWN)  │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ ENGINE (wordflow/engine)                                 │
│  code_path_runner · quality_bar · goal_lock              │
│  cognitive_loop · evidence_packet · programming_pipeline │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ STANDARDS (wordflow/standards) — enforcement determinista│
│  catalog · applicability · context · evidence_verifier   │
│  checklist_sheriff · forensic_contract · verdict         │
│  gap_registry · closure_engine · copy_first · wiring     │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ KERNEL (wordflow_kernel)                                 │
│  bootstrap_v1 / bootstrap_multi · spawn · instance       │
│  stages · bridge · resources (parcial)                   │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ DATA / POLICY                                            │
│  component_catalog.json · connect_catalog.json           │
│  PIPELINE/*.md · .cursor/rules · AGENTS.md · CI          │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Control plane vs execution plane

| Plano | Qué hace | Qué no hace |
|-------|----------|-------------|
| **Control** (`standards/*`, gates, sheriff, verdict) | Decide BLOCK/PASS, mide, exige checklist | No es el editor de git del Director |
| **Execution** (`code_path_runner` + cognitive) | Orquesta path C-19 | No escribe el árbol git por sí solo |
| **External apply** (GitHub API / agente humano) | Commits reales | Debe pasar por política de checklist al integrar |

---

## 3. Módulos standards (enforcement)

| Módulo | Responsabilidad |
|--------|-----------------|
| `programming_points_catalog.py` | CORE/CONDITIONAL/ADVISORY/REFERENCE + tags |
| `applicability_engine.py` | Tags → required ids; agente no downgrade |
| `context_manifest.py` | Manifest + validator (no solo bool) |
| `evidence_verifier.py` | Resuelve evidence; claim ≠ verification |
| `checklist_sheriff.py` | Juez checklist + version pin |
| `executor_gates.py` | Pre/post gates |
| `forensic_contract.py` | Contrato cierre |
| `verdict_authority.py` | Único PASS formal standards |
| `gap_registry.py` | OPEN→FIXED→VERIFIED→CLOSED |
| `closure_engine.py` | CLOSED solo si todo limpio |
| `copy_first.py` + `symbol_index.py` | Reuse scan |
| `wiring_graph.py` | Catalog connectivity |
| `test_runner.py` | Smoke effectiveness |

---

## 4. Flujo global de una tarea de code

```
ContextManifest → ContextValidator
       ↓
ApplicabilityEngine → required points
       ↓
AgentChecklistClaim
       ↓
ChecklistSheriff (+ EvidenceVerifier)
       ↓ PASS
code_path_runner (quality→lock→cognitive→evidence)
       ↓
PostVerify / VerdictAuthority / ClosureEngine
       ↓
GapRegistry loop (si gaps)
       ↓
CLOSED | OPEN
```

---

## 5. Multi-instancia

`bootstrap_multi` puede anotar config `copy_first`, `forensic_post_verify`, pipeline path.  
Instance store ≠ GapRegistry.

---

## 6. Límites explícitos

- FourPass como 4 runners independientes: aún parcial (mediciones en post).
- DOC→REQ→CODE graph completo: no cerrado.
- ImpactAnalyzer AST callers: no cerrado.
- Apply git dentro del runner: no (by design control vs execution).

---

## 7. Referencias

- `PIPELINE/WORDFLOW_PROGRAMMING_COMO_FUNCIONA.md`
- `PIPELINE/ENFORCEMENT_P0_REDESIGN.md`
- `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md`
- `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`
