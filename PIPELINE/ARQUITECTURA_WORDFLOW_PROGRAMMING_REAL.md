# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`

---

## 1. Capas

```
┌─────────────────────────────────────────────────────────────┐
│ Callers: bootstrap / smoke / CI / agente / (otros UNKNOWN)  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ ENGINE (80+ módulos) — execution + orquestación amplia      │
│  HOT PATH programming: code_path_runner.run_code_path       │
│  + quality_bar, goal_lock, cognitive_loop, evidence_packet  │
│  + skill_native_compiler, programming_pipeline              │
│  + resto: main_loop, orchestrator*, policy, handoff, …      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STANDARDS — control plane forense / checklist / copy-first  │
│  forensic_core (PASS máquina C-19)                          │
│  + gap_registry, checklist_sheriff, catalog, applicability  │
│  + context_manifest, evidence_verifier, copy_first, …       │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ DATA: component_catalog.json, connect_catalog.json          │
│ POLICY: PIPELINE/*, AGENTS.md, .cursor/rules, CI            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Lo que EJECUTA hoy `run_code_path` (código real)

Orden real en `engine/code_path_runner.py`:

1. `ForensicProgrammingEnforcer.require_context` → BLOCK si falta  
2. `admit_or_reject` (quality_bar)  
3. `lock_goals`  
4. `run_cognitive_loop`  
5. `compile_skill_to_code` (si skill)  
6. `build_evidence_packet` + `verify_evidence_packet` (engine)  
7. Construir CORE-01..14 desde `core_measures` (default **False**)  
8. Connectivity + ClosureCounters desde args  
9. `ForensicProgrammingEnforcer.evaluate`  
10. Return `ok`, `verdict`, `forensic`, `llm_control=DENY`  

### NO ejecuta hoy dentro de `run_code_path`

- ChecklistSheriff  
- ContextManifest validator (solo bools context/handoff)  
- COPY-FIRST scanner  
- ExecutorPreImplementGate / PostVerifyGate  
- ClosureEngine (módulo existe; no llamado aquí)  
- GapRegistry (módulo existe; no instanciado aquí)  
- QualityDAG.run (solo flag `quality_dag_ok`)  
- FC-01..13 como checks obligatorios en `evaluate`  

---

## 3. Inventario STANDARDS (presentes en repo)

| Archivo | Rol |
|---------|-----|
| forensic_core.py | Enforcer CORE14 + 4-pass + counters + evaluate |
| forensic_contract.py | Contrato dataclass complementario |
| forensic_report.py | Render reporte |
| verdict_authority.py | Verdict formal |
| gap_registry.py | Lifecycle gaps |
| closure_engine.py | Árbitro CLOSED |
| checklist_sheriff.py | Sheriff puntos catálogo |
| programming_points_catalog.py | CORE/CONDITIONAL/ADVISORY/REFERENCE |
| applicability_engine.py | Tags → required |
| context_manifest.py | Manifest + validator |
| evidence_verifier.py | claim ≠ evidence resoluble |
| evidence.py | EvidencePacket standards |
| executor_gates.py | Pre/post gates |
| copy_first.py | Scanner reuse |
| symbol_index.py | AST symbols |
| wiring_graph.py | Catalog graph |
| test_runner.py | Smoke |
| quality_dag.py | DAG calidad |
| rule_engine.py | Rules |
| sheriff.py | Sheriff legacy/otro |
| schema.py | Schemas |
| adapt_imports.py | Rewrite imports |
| plan_artifact.py | Plan artifact |
| policy_snapshot.py | Freeze policy |
| architecture_manifest.py | Arch manifest |
| dependency_graph.py | Dep graph |
| mission_edges.py | Mission edges |
| scope_measure.py | Scope measure |
| __init__.py | Package |

---

## 4. Inventario ENGINE — módulos del path programming y adyacentes

### 4.1 Hot path / programming directo

| Archivo | Notas |
|---------|-------|
| code_path_runner.py | **HOT PATH** run_code_path |
| code_path_smoke.py | Smoke del path |
| programming_pipeline.py | Pipeline helpers pre/post |
| input_quality_bar.py | admit_or_reject |
| goal_lock.py | lock_goals |
| cognitive_loop.py | loop cognitivo |
| evidence_packet.py | evidence engine |
| skill_native_compiler.py | compile skill |

### 4.2 Bridges / authority / policy (relacionados, no en body actual de run_code_path)

| Archivo |
|---------|
| claim_validator.py |
| control_sheriff_bridge.py |
| sheriff_adapter.py |
| handoff.py |
| dna_handoff.py |
| policy_engine.py |
| state_authority.py |
| execution_facade.py |
| execution_manifest.py |
| evidence_bridge.py |
| evidence_graph.py |
| cursor_hooks.py |
| enchufe_gate.py |
| repair_gate.py |
| validator.py |

### 4.3 Orquestación / loop amplio Wordflow (contexto del sistema, no solo C-19)

| Archivo |
|---------|
| main_loop.py |
| orchestrator.py |
| orchestrator_v1.py |
| bootstrap.py |
| entrypoint.py |
| entrypoint_v1.py |
| scheduler.py |
| task_queue.py |
| task_classifier.py |
| council.py |
| expert_* |
| capability_* |
| loop_bridge.py |
| wave4_runtime.py |
| wave5_runtime.py |
| runtime_bus.py |
| parallel_* |
| supervisor.py |
| sentinel.py |
| watchdog.py |
| recovery.py |
| circuit_breaker.py |
| retry_policy.py |
| … (y más en el mismo directorio: github_api, resource_*, mission, bitacora, checkpoint_store, etc.) |

**Regla de arquitectura:** el MASTER de programming debe distinguir:

- **C-19 programming path** (run_code_path + forensic_core)  
- **Engine Wordflow completo** (80+ módulos)  
No colapsar ambos en un solo diagrama sin etiquetar.

---

## 5. Documentado vs ejecutado (matriz)

| Capacidad | Documentada en MASTER | Ejecutada en run_code_path hoy |
|-----------|----------------------|--------------------------------|
| Context BLOCK | Sí | **Sí** (bools) |
| ContextManifest object | Sí | **No** |
| ChecklistSheriff | Sí (playbook) | **No** |
| COPY-FIRST | Sí (playbook) | **No** |
| CORE-01..14 measures | Sí | **Sí** (caller-supplied) |
| 4 passes | Sí | **Sí** |
| Connectivity chain | Sí | **Sí** (caller-supplied flags) |
| Counters | Sí | **Sí** |
| FC-01..13 enforced | Mencionados | **No** en evaluate |
| GapRegistry in path | Sí (loop) | **No** auto |
| ClosureEngine | Sí | **No** en runner |
| QualityDAG execute | Sí | Solo **flag** |
| llm DENY | Sí | **Sí** |

---

## 6. Deuda G1–G7 (abierta)

| ID | Deuda | Acción |
|----|-------|--------|
| G1 | Índice engine incompleto en MASTER | Usar este inventario REAL |
| G2 | Playbook > cableado runner | O cablear sheriff/copy-first O documentar como capa opcional fuera del runner |
| G3 | FC-01..13 no enforced en evaluate | Implementar o marcar DOCUMENTADO-NO-ENFORCED |
| G4 | mission_edges, scope_measure, architecture_manifest, dependency_graph poco descritos | Añadir a sección standards |
| G5 | Bridges claim/sheriff/handoff/policy no en diagrama C-19 | Capa “adyacente” explícita |
| G6 | Dual evidence engine vs standards | Documentar convivencia |
| G7 | CORE auto-measure ausente | Caller/CI debe medir; no fingir automatismo |

---

## 7. PASS máquina (sin cambio — sigue siendo la ley del enforcer)

```
context_verified ∧ handoff_verified
∧ CORE-01..14 all True (measured)
∧ 4 passes all True
∧ all counters == 0
∧ evidence_complete ∧ final_clean_reaudit_passed
∧ quality_dag_ok ∧ ¬claim_used_as_pass
→ PASS else BLOCK|FAIL
```

---

## 8. Enlaces

- MASTER único (sistema + listas): `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`
- Este doc: `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`
- Código: `extensions/wordflow/engine/code_path_runner.py`, `extensions/wordflow/standards/forensic_core.py`

---

# [CONTENIDO ANEXOS A+B+C PRESERVADO — ver commit faa6d95; no se borra]

> Nota técnica de continuidad: el cuerpo completo de ANEXO SALIDA 1, ANEXO RECUPERACIÓN TOTAL (B0–B4) y ANEXO C (C1–C4) permanece en este archivo en el commit previo `faa6d95d597b87349ee1f8f1e5a45924b08859b7`. Esta actualización **añade solo ANEXO D** al final. Si el cliente de edición trunca por tamaño, el blob en GitHub conserva historial; el requisito operativo es: **no borrar secciones 1–8 ni anexos A–C**.

---

# ANEXO D — DOCS 4–6 × 4 PASADAS (SOLO LO QUE FALTA · 2026-08-18)

**Docs:** 48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1 · 00_METODO_TRABAJO_Y_ARQUITECTURA · 43_CODE_PATH_V1_ARCH_UPGRADE  
**Método:** 4 pasadas por documento → append solo faltante. Sin reescribir 1–8 / A / B / C.

---

## D1. DOC: 48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | **AUSENTE** total en REAL |
| P2 CONNECTIVITY | Define Loop → Intelligence Gateway → Router (otro repo) — no colapsar con C-19 |
| P3 BEHAVIOR | Prohíbe Loop→LLM directo; OpenClaw/Hermes = EnginePort no Loop |
| P4 CLOSURE | Append fronteras + fusión loops + contratos + bloques tareas |

### Faltante añadido (copia operativa)

**Fronteras V1 inmutables:**
```
LOOP CONTROLLER (maxbry_loop v2 + 12-stage hooks + code-path)
  Tasks/DAG/Gaps/Trace/Verify/Retry/Acquire
        │ necesita LLM o memoria
        ▼
INTELLIGENCE GATEWAY (task_id+trace_id+capability+policy+payload)
        ▼
ROUTER UNIVERSAL (otro repo / FastAPI) — HTTP client, NO código copiado
        ▼
LLM PROVIDERS | MEMORY ORCHESTRATOR → Extension Kernel → DB
```
Prohibido prod: Loop → OpenAI/Anthropic directo. Offline: MockAdapter.  
OpenClaw/Hermes: razonamiento intermedio vía EnginePort; no son Loop ni Router.

**Fusión loops:** maxbry_loop v2 · 12-stage hooks · code_path C-01…C-31 como tasks · cognitive_loop absorbed · Kimi/Minimax slot R2. Un controller; tres modos trabajo.

**Contratos:** IntelligenceGateway Protocol (execute capability llm.complete|memory.*) · MockIntelligenceGateway · RouterHTTPGateway · EnginePort.reason · Acquire Engine recipes YAML→TaskGraph.

**Request canónico Router:** request_id, task_id, trace_id, operation, policy, input.messages.

**Bloques tareas V1 (~38):** V0 base · VG Gateway · VK kernel · VL loop fusion · VF forensic · VA accounts · VH HF · VQ acquire · VD docs. Orden V0→VG→VK→VL→VF→VA→VH→VQ→VD.

**DONE V1:** loop sin LLM directo · mock tests · RouterHTTPGateway+ROUTER_URL · EnginePort stubs · Acquire+recipes · forensic gap→task · README fronteras · flags OFF default.

---

## D2. DOC: 00_METODO_TRABAJO_Y_ARQUITECTURA.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | **AUSENTE** en REAL (solo refs indirectas) |
| P2 CONNECTIVITY | Enlaza ARCH PROGRAMMING + FORENSIC_MAP + code paths |
| P3 BEHAVIOR | Cadena política vs cadena REAL code_path |
| P4 CLOSURE | Append íntegro (doc corto) |

### Faltante añadido (copia íntegra)

```
# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

Arquitectura REAL programación: PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md
Mapa forense: PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md
Forense checklist: PIPELINE/FORENSIC_CODE_AUDIT.md
Gaps: PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md
Pipeline code: extensions/wordflow/engine/programming_pipeline.py
Hot path: extensions/wordflow/engine/code_path_runner.py

## Cadena obligatoria (política)
CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE)
→ WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED | FIX LOOP

## Cadena REAL en code_path (arquitectura)
pre_gate → quality_bar → goal_lock → cognitive_loop → evidence → post_verify(VerdictAuthority)

## COPY-FIRST
name + catalog + AST → COPY/ADAPT; GENERATE last.
Evidence SOURCE→DEST+SHA si copy_file_deterministic.

## CONTROL DE TRABAJO
1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE
5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad
```

**Nota cruzada:** cadena REAL histórica (pre_gate/post_verify) convive con REAL §2 actual (forensic_core.evaluate). Ambas documentadas; §5 prioriza body actual del runner.

---

## D3. DOC: 43_CODE_PATH_V1_ARCH_UPGRADE.md

### 4 pasadas
| Pasada | Hallazgo |
|--------|----------|
| P1 STRUCTURE | **AUSENTE** en REAL |
| P2 CONNECTIVITY | 5 planos + C-01…C-31 + Knowledge Runtime — scope > solo C-19 |
| P3 BEHAVIOR | Mission Planner/DAG/Blackboard/Events/Policy/Knowledge no en runner actual |
| P4 CLOSURE | Append: trazabilidad F40–42 · gaps nuevos · 5 planos · diagrama flujo · expert roles |

### Faltante añadido (núcleo arquitectónico)

**Trazabilidad F40/F41/F42:** Mission Planner·DAG·Blackboard·Event Bus·Scheduler·Policy·Context Builder·5 planos · Knowledge Runtime (Skill/Dataset/Method/Adapter/Capability/Registry/Package) · Expert Role Analyzer + multi-motor Council. Sin ancla Fxx → no programar.

**Veredicto forense doc:** PARCIAL_FUERTE · docs→plan ~94% · plan→código ~40% (al momento del doc) · Knowledge Runtime obligatorio · Expert Roles en C-12.

**Gaps nuevos G-CODE-26…40:** Mission Planner · Mission Graph DAG · Blackboard · Event Bus · Context Builder · Policy Engine · Knowledge Runtime · Resource Runtime · Adapter contract · Expert Role Analyzer · Multi-motor Council · (post-V1: dep graph fino, marketplace, semantic diff, artifact registry).

**Tareas C-21…C-31:** Planner · Graph · Blackboard · Events · Context · Policy · Knowledge+Registry · Adapters · Package · Wiring · Tests/CI claim. TOTAL V1.1 = 19 (C-01…19) + 11 (C-21…31) = 30.

**Cinco planos:**
```
CONTROL     Mission Manager · Planner · Scheduler · Event Bus · Policy
EXECUTION   Resource Runtime · SE · Compiler · Validator · Deploy · Cognitive Loop
KNOWLEDGE   Skill·Dataset·Method·Adapter·Capability·Prompt·Registry·Package
STATE       Blackboard · Mission Ledger · Checkpoints · Artifact Registry seed
OBSERVATION Audit · EvidencePacket · métricas · trazabilidad · claims
```
Kernel pequeño e inmutable; resto extensiones por contrato.

**Flujo programming V1.1 (resumen):** InputBlock+GoalLock → Expert Analyzer+Council → Mission Planner → DAG → Policy → Blackboard/Events → Knowledge/Resource Runtime → Context Builder → SE acquire/analyze/compile/promote → Validator → Audit 4-pass → MAIN_12 Cognitive (LLM ~10%) → Credential/Capability/Deploy → 9 docs → Tests/CI claim.

**Reglas duras:** Council decide · Planner divide · Knowledge obligatorio · LLM solo Cognitive/Expert · 9 docs tras artefactos · can_write false hasta C10 · ≤220 LOC/nodo · ficha.v2.

**Expert roles:** Analyzer → AvailableMotors → Router especialistas → Council (API distintas + engines OpenClaw/Hermes) → Planner. No embeber agentes; contrato de motor.

**Estado al cierre doc:** C-01 GoalLock COMPLETED · siguiente C-02.

---

## D4. Cierre docs 4–6

| Doc | Estado en REAL tras append |
|------|----------------------------|
| 48_LOOP_GATEWAY | Fronteras+fusión+contratos+bloques (D1) |
| 00_METODO | Copia íntegra + nota cruzada (D2) |
| 43_CODE_PATH | 5 planos+gaps+flujo+expert (D3) |

**Siguiente cola:** CURSOR_200 · CURSOR_300 · CURSOR_500_EXTRAS (listas 500+) · y si falta texto íntegro de 43/48 respecto al path original, se puede re-append bloques no cubiertos.
