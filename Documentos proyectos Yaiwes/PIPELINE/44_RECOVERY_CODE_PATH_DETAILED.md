# PIPELINE 44 — RECOVERY MASTER · CODE PATH V1.1 (DETALLADO)
# Fuente de verdad ÚNICA: GitHub maxbry123-commits/agentes
# Fecha: 2026-08-15
# Ancla: PIPELINE/43_CODE_PATH_V1_ARCH_UPGRADE.md
# Regla: 1 tarea = 1 salida = 1 commit · ≤220 LOC · llm_control: DENY núcleo
# PROHIBIDO: usar sandbox como fuente de verdad

---

## 0. ESTADO REAL (auditoría 4 pasadas · 2026-08-15 · SOLO GITHUB)

```
PASO 1 · EXISTENCIA EN GITHUB (commit b13ce147…)
  extensions/wordflow/engine/goal_lock.py     → EXISTS (sha 55b2daea…)
  extensions/wordflow/tests/test_goal_lock.py → EXISTS
  extensions/wordflow/ficha.v2.json           → EXISTS
  extensions/wordflow/ (council, sentinel, main_loop, refute_repair, …) → EXISTS
  PIPELINE/43_CODE_PATH_V1_ARCH_UPGRADE.md    → EXISTS (fuente plan)

PASO 2 · CLAIMS vs CÓDIGO
  C-01 GoalLock: SOSTENIDO en GitHub
  C-02…C-31: pendientes según PIPELINE 43

PASO 3 · AMBIGÜEDAD CORREGIDA AQUÍ
  Cada tarea tiene: path exacto · acceptance · LOC · ancla · claim format
  Claim incompleto (sin sha/tests) = PARTIAL automático

PASO 4 · RECUPERACIÓN
  Cualquier Grok nuevo: leer SOLO este archivo + PIPELINE/43 en GitHub
  No inventar. Si falta ancla Fxx → pedir al Director.
```

**Siguiente tarea obligatoria:** C-02

---

## 1. INVARIANTES (ley inmutable)

1. 90 % determinista · LLM solo en Council / Cognitive Loop (10 %).
2. llm_control: DENY en todo módulo de compute.
3. can_write_kernel = false · can_write_github = false hasta C-16 autorizado.
4. Token nunca en journal / provenance / código.
5. 1 archivo ≤ 220 LOC · 1 tarea = 1 commit.
6. Claim COMPLETED solo con: path + size + blob_sha + tests PASS + ancla Fxx.
7. Sin ancla Fxx → no se programa.
8. Stubs no cuentan como 100 %.
9. **Fuente de verdad = solo GitHub.** Sandbox no cuenta.

---

## 2. LISTA 1 — GAPS VIVOS (trazabilidad)

| ID | Gap | Ancla | Estado GitHub |
|----|-----|-------|---------------|
| G-CODE-01 | SE acquire_12 completo | F10 F15 | parcial |
| G-CODE-02 | SE analyze_12 + reuse_decision | F10 F11 | parcial |
| G-CODE-03/04 | reuse_compile + promote_12 | F12 F16 | parcial |
| G-CODE-05 | C09 dual compiler | F12 F13 F29 | parcial |
| G-CODE-06/33 | Resource Runtime 8 pasos | F30 F41 | parcial |
| G-CODE-07 | Handoff can_write_kernel=false | GAP_02 | pendiente |
| G-CODE-08 | Audit 4-pasadas + EvidencePacket | F01–F04 | parcial |
| G-CODE-09/23 | C10 Git Data API real + multi-repo | F15 F16 | publisher parcial ≠ C10 |
| G-CODE-10 | CodeOutput + Validator fail_closed | UOOS | schemas existen · validator endurecer |
| G-CODE-11 | InputBlock + GoalLock e2e | F05 F28 | **C-01 DONE en GitHub** |
| G-CODE-13 | Enchufe v2 en todo módulo code | F17 | wordflow ficha EXISTS · gate endurecer |
| G-CODE-19 | 9 docs nativos runtime wiring | F21 | parcial |
| G-CODE-20/35/36 | ExpertPanel + Role Analyzer + multi-motor | F06 F42 | council parcial |
| G-CODE-22 | Credential Manager | F31 F26 | pendiente |
| G-CODE-24 | Capability Live/MCP/Snapshot | F32 | pendiente |
| G-CODE-26 | Mission Planner | F40 | pendiente |
| G-CODE-27 | Mission Graph DAG ligero | F40 | pendiente |
| G-CODE-28 | Blackboard operativo | F40 | pendiente |
| G-CODE-29 | Event Bus mínimo | F40 | pendiente |
| G-CODE-30 | Context Builder | F40 | pendiente |
| G-CODE-31 | Policy Engine seed | F40 | pendiente |
| G-CODE-32 | Knowledge Runtime + Unified Registry | F41 | pendiente |
| G-CODE-34 | Adapter contract único | F41 | pendiente |
| G-CODE-25 | Engine adapters Hermes/OpenClaw | F23 | post-V1 |

---

## 3. LISTA 2 — TAREAS DETALLADAS (recuperables desde GitHub)

### C-01 · InputBlock + GoalLock e2e
- **Estado:** COMPLETED en GitHub
- **Paths:** `extensions/wordflow/engine/goal_lock.py` · `tests/test_goal_lock.py`
- **Ancla:** F05 F28 G-CODE-11
- **No re-trabajar**

### C-02 · Enchufe gate + fichas v2 (SIGUIENTE)
- **Objetivo:** Gate que rechaza carga si falta ficha o llm_control != DENY. Completar fichas en módulos code path.
- **Paths:**
  - `extensions/wordflow/ficha.v2.json` (ya existe — validar campos)
  - `extensions/source_evolution/ficha.v2.json` (crear si falta)
  - `extensions/audit_forensic/ficha.v2.json` (crear si falta)
  - `extensions/project_bootstrap/ficha.v2.json` (crear si falta)
  - `extensions/wordflow/engine/enchufe_gate.py` (≤80 LOC)
  - `extensions/wordflow/tests/test_enchufe_gate.py`
- **Campos mínimos ficha:** abi_version, extension_type, kernel_min, mount_mode, load_priority, llm_control:"DENY", artifact_id
- **Acceptance:**
  1. Cada ficha parsea + required fields + llm_control == DENY
  2. enchufe_gate.load(module) FAIL si falta ficha o llm_control != DENY
  3. Tests ≥ 4 casos (ok, missing, wrong llm, bad schema)
  4. LOC nuevos ≤ 120
- **Ancla:** G-CODE-13 · F17
- **Dependencias:** C-01
- **Claim al cerrar:** path + size + blob_sha de cada ficha + test output

### C-03 · architecture_output + code_output + Validator fail_closed
- **Paths:** schemas ya en GitHub · `extensions/wordflow/engine/validator.py`
- **Acceptance:** fail_closed=true · tests rechazan output incompleto
- **Ancla:** G-CODE-10 · LOC ≤120

### C-04 · SE acquire_12
- **Paths:** `extensions/source_evolution/loops/acquire_12.py`
- **Acceptance:** nunca from-0 si source existe · pin SHA40 · license_gate · FakePort tests
- **Ancla:** G-CODE-01 · LOC ≤180

### C-05 · SE analyze_12 + reuse_decision
- **Paths:** `extensions/source_evolution/loops/analyze_12.py`
- **Acceptance:** IR 0-4 · REUSE_FIRST|ADAPT|GENERATE_LAST
- **Ancla:** G-CODE-02 · LOC ≤150

### C-06 · C09 dual compiler + MethodPackage seed
- **Paths:** skill_compiler/ o source_evolution/compiler/
- **Acceptance:** skill_ir → knowledge|procedure|executable
- **Ancla:** G-CODE-05 · LOC ≤200

### C-07 · promote_12 → request_deploy
- **Paths:** `extensions/source_evolution/loops/promote_12.py`
- **Acceptance:** solo AuditVerdict PASS · payload sin token
- **Ancla:** G-CODE-03/04 · LOC ≤140

### C-08 · Resource Runtime
- **Paths:** resource_brain / resource runtime
- **Acceptance:** DISCOVERED→…→AVAILABLE · no carga si no AVAILABLE
- **Ancla:** G-CODE-06/33 · LOC ≤180

### C-09 · Audit 4-pasadas cierre
- **Paths:** audit_forensic (ya existe) · cerrar wiring + CI
- **Ancla:** G-CODE-08 · LOC ≤120 adicionales

### C-10 · Doc→Arch→Code microflow
- **Paths:** `extensions/wordflow/microflows/doc_to_code.py`
- **Ancla:** G-CODE-18 · LOC ≤150

### C-11 · 9 docs nativos runtime (lazy 4 core)
- **Core:** PROJECT_PROFILE · ARCHITECTURE · CAPABILITIES · TRACEABILITY
- **Ancla:** G-CODE-19 · LOC ≤150

### C-12 · ExpertPanel + Role Analyzer + multi-motor
- **Paths:** council.py (existe) + role_analyzer.py
- **Acceptance:** AvailableMotors → CouncilContract
- **Ancla:** G-CODE-20/35/36 · LOC ≤180

### C-13 · HF index (opcional V1)
- **Ancla:** G-CODE-21 · LOC ≤160

### C-14 · Credential Manager
- **Paths:** `extensions/credentials/`
- **Acceptance:** get(provider,scope) → token_ref · nunca literal
- **Ancla:** G-CODE-22 · LOC ≤200

### C-15 · Capability Router Live/MCP/Snapshot (opcional V1)
- **Ancla:** G-CODE-24 · LOC ≤160

### C-16 · C10 github_deploy
- **Paths:** `extensions/github_deploy/` (NUEVO)
- **Acceptance:** dry-run · blob→tree→commit→ref · expected_head · no force_push · evidence.json
- **Ancla:** G-CODE-09/23 · LOC ≤220

### C-17 · SSH adapter
- **Ancla:** G-CODE-23/34 · LOC ≤100

### C-18 · main_12 wiring code path
- **Ancla:** G-CODE-12 · LOC ≤150

### C-19 · License + Repair e2e + CI + claim final
- **Ancla:** G-CODE-15 · LOC ≤120

### Bloque arquitectura C-21…C-31
Ver PIPELINE/43 sección 3 · mismos IDs · mismos acceptance mínimos (Planner, DAG, Blackboard, Event Bus, Context, Policy, Knowledge Runtime, Adapters, Package, Wiring, claim).

---

## 4. ORDEN DE EJECUCIÓN

```
C-02 → C-03 → C-21 → C-23 → C-25
→ C-12 → C-26
→ C-08/C-27 → C-28
→ C-04…C-07 → C-22 → C-24
→ C-14 → C-15 → C-16
→ C-11 → C-09 → C-10 → C-18 → C-19/C-31
```

C-13 y C-15 opcionales V1 sin token HF/MCP.

---

## 5. FORMATO CLAIM OBLIGATORIO

```yaml
status: COMPLETED | PARTIAL
task_id: C-0X
final_commit: <sha>
paths:
  - path: extensions/...
    size_bytes: N
    blob_sha: <hex>
tests:
  command: python -m ...
  result: N/N PASS
ancla: G-CODE-XX · Fxx
loc_net: N
llm_control: DENY
stubs: false
```

Claim incompleto = PARTIAL.

---

## 6. RECUPERACIÓN SI SE PIERDE CONTEXTO

1. Leer SOLO desde GitHub: PIPELINE/44_RECOVERY_CODE_PATH_DETAILED.md
2. Verificar C-01 en GitHub: extensions/wordflow/engine/goal_lock.py + test_goal_lock.py
3. Siguiente tarea = primera C-xx no COMPLETED según este documento.
4. Si falta ancla Fxx → parar y pedir documento al Director.
5. No re-escribir C-01. No tocar control-layer Fase1 ya auditada.
6. Cada 4 tareas: re-leer PIPELINE/43 + PIPELINE/44 en GitHub.
7. PROHIBIDO usar sandbox como fuente de verdad.

---

## 7. BITÁCORA

| Fecha | Evento |
|-------|--------|
| 2026-08-15 | C-01 COMPLETED en GitHub (goal_lock) |
| 2026-08-15 | PIPELINE 43 = plan arquitectura |
| 2026-08-15 | **PIPELINE 44** = recovery detallado · solo GitHub · siguiente C-02 |

---

## 8. ENLACES GITHUB (ÚNICA FUENTE DE VERDAD)

**Este documento:**  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/44_RECOVERY_CODE_PATH_DETAILED.md

**Plan arquitectura vigente:**  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/43_CODE_PATH_V1_ARCH_UPGRADE.md

**C-01 GoalLock:**  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/goal_lock.py  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/tests/test_goal_lock.py

**Ficha wordflow:**  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/ficha.v2.json

**Repo:**  
https://github.com/maxbry123-commits/agentes

---

**FIN PIPELINE 44**  
Estado: C-01 cerrado en GitHub · **siguiente salida = C-02**
