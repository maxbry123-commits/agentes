# Cómo funciona el Wordflow de programación de code (detallado)

**Path canónico:** `extensions/wordflow/engine/code_path_runner.py` → `run_code_path`  
**Enforcement:** `extensions/wordflow/standards/*`  
**Arquitectura global:** `PIPELINE/ARQUITECTURA_WORDFLOW_GLOBAL.md`

---

## 1. Resumen en una frase

El Wordflow de programming **orquesta y verifica de forma determinista** un intento de tarea de code; **no** sustituye al agente que escribe commits en GitHub, pero **sí puede BLOCK** si faltan contexto, checklist, evidence o veredicto.

---

## 2. Entrada

```python
run_code_path(
    raw_input,
    plan_steps=None,
    skill=None,
    mission_id="",
    context_verified=False,   # default False (P0)
    handoff_verified=False,   # default False
    enforce_copy_first=True,
    enforce_post_verify=True, # forzado salvo allow_skip_post_verify
    allow_skip_post_verify=False,  # solo dev/test
)
```

---

## 3. Secuencia interna

### 3.1 Pre-gate (COPY-FIRST + policy)

1. `ProgrammingPipeline.pre_implement` / scanner `ExistingCodeScanner`:
   - busca por nombre de archivo, `component_catalog.json`, símbolos AST
   - plan: ADAPT si hay match; GENERATE solo si no hay match
2. Si se usa `ExecutorPreImplementGate` con checklist:
   - exige `AgentChecklistClaim`
   - `ChecklistSheriff.evaluate`:
     - pin `catalog_version`
     - `ApplicabilityEngine.classify(...)` → required ids
     - rechaza `proposed_non_applicable` sobre required
     - `EvidenceVerifier` sobre cada evidence
     - BLOCK si GENERATE sin claim de no-match, COPY/ADAPT sin sources, etc.
3. `context_verified` / `handoff_verified` en False → BLOCK en validator de contrato.

### 3.2 Quality bar

`admit_or_reject(raw_input)` — si no ok, stage `quality_bar`.

### 3.3 Goal lock

`lock_goals({text, raw})` — si no ok, stage `goal_lock`.

### 3.4 Cognitive loop

`run_cognitive_loop(topic, plan_steps, mission_id, goal_lock, task_class="CODE")`  
Interior LLM: **UNKNOWN** (no clasificado aún en evidence).

### 3.5 Skill compile (opcional)

Si `skill` dict → `compile_skill_to_code`.

### 3.6 Evidence engine

`build_evidence_packet` + `verify_evidence_packet` (paquete del **engine**, distinto del `EvidencePacket` de standards).

### 3.7 Post-verify (obligatorio en perfil normal)

- Smoke `default_smoke_runner`
- `ForensicCodeContract` + `VerdictAuthority.decide`
- `ClosureEngine.decide` (checklist/forensic/evidence/gaps)
- `llm_control` siempre `"DENY"` en el return del runner

---

## 4. Catálogo de puntos (cómo se programó)

No hay 500 ifs.

```
ProgPoint(id, stage, title, enforcement, applicability tags, evidence_type)
enforcement ∈ {CORE, CONDITIONAL, ADVISORY, REFERENCE}
```

- **CORE:** siempre en required del sheriff cuando el stage aplica.
- **CONDITIONAL:** solo si `ApplicabilityEngine` pone el tag (multi_file, db, security, …).
- **ADVISORY:** no bloquea solo.
- **REFERENCE:** patrón, no gate.

Inventario largo 1–500 en PIPELINE = **dataset de referencia**.  
Runtime = **subset con metadatos** en `programming_points_catalog.py`.

---

## 5. Objetos clave

### AgentChecklistClaim
- mission_id, task_id, catalog_version
- action: COPY | ADAPT | GENERATE
- sources[], files_touched[]
- claims[]: point_id, addressed, evidence, evidence_kind
- proposed_non_applicable[] (no puede bajar CORE/required)
- tags_hint{} para applicability

### ChecklistSheriff
- Entrada: claim
- Sale: passed, findings BLOCK, coverage_ratio, applicability dump
- Reglas: `AGENT_CLAIM_IS_NOT_VERIFICATION`, `AGENT_CANNOT_DOWNGRADE_REQUIRED_CHECK`

### GapRegistry
- Estados: OPEN → FIXED → VERIFIED → CLOSED
- Prohibido OPEN → CLOSED

### ClosureEngine
- CLOSED solo si checklist + forensic + evidence OK y counters de gaps/unexpected/broken en 0

---

## 6. Salida de `run_code_path`

Dict típico:

- `ok` bool
- `mission_id`, `lock`, `cognitive`, `skill_compile`
- `programming_pre_gate`, `programming_post_verify`
- `evidence`, `evidence_ok`
- `llm_control: "DENY"`
- `enforce_post_verify`

---

## 7. Cómo se programó (técnico)

1. **Dataclasses** para contratos (claim, gap, manifest, point).
2. **Motores puros** sin I/O de red: applicability, evidence verify, sheriff, closure.
3. **Scanner** con `pathlib` + `ast` + JSON catalogs.
4. **Gates** como funciones que devuelven dict allow/reason (fácil de testear).
5. **Defaults seguros:** context/handoff False; post_verify True.
6. **Separación** engine evidence vs standards EvidencePacket (conviven; no unificar a la fuerza aún).
7. **CI** `.github/workflows/forensic-gates.yml` smoke imports + skip≠pass.

---

## 8. Qué debe hacer el agente de programming en la práctica

1. Construir `ContextManifest` + pasar validator.
2. Correr applicability → ver required.
3. Rellenar `AgentChecklistClaim` con evidence resoluble.
4. No marcar PASS: solo claim.
5. Ejecutar path / apply externo.
6. Post-verify + closure; si gaps → GapRegistry transitions hasta VERIFIED→CLOSED.

---

## 9. Limitaciones actuales

- Checklist completa aún no es argumento de primera clase en todos los callers de `run_code_path` (pre_gate simplificado en el runner puede no pasar claim).
- Four-pass = mediciones agregadas, no 4 procesos independientes.
- Scope git-diff real: parcial (scope_measure heurístico).
- Trace graph DOC→REQ→CODE: no cerrado.

---

## 10. Archivos a leer en orden

1. `engine/code_path_runner.py`
2. `standards/checklist_sheriff.py`
3. `standards/programming_points_catalog.py`
4. `standards/applicability_engine.py`
5. `standards/executor_gates.py`
6. `standards/gap_registry.py` / `closure_engine.py`
7. `PIPELINE/ENFORCEMENT_P0_REDESIGN.md`
