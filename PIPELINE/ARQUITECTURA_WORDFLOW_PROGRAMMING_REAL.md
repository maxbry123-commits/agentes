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

# RESTORE 2026-08-18 — documento recuperado desde commit faa6d95

**Qué se recuperó:** secciones 1–8 completas + ANEXO A (GLOBAL, FORENSIC REQUIRED, CORE, API, GapRegistry, QualityDAG, playbook) + ANEXO B (LIVE, PROGRAMMING, FORENSIC_MAP) + ANEXO C (gaps map, paths, 04_3_MODOS).

**Blob fuente de verdad de esta restauración:**
https://github.com/maxbry123-commits/agentes/blob/faa6d95d597b87349ee1f8f1e5a45924b08859b7/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md

**Anexos posteriores (D=48/00/43, E=listas, F=E001–E500 línea a línea) existen en historial:**
- D: https://github.com/maxbry123-commits/agentes/commit/11518bdc9f6b789fa5e525b51805ac2636e4f654
- E: https://github.com/maxbry123-commits/agentes/commit/a8b8af6cdfc09e49a2c9a9e4d4e113cc535c7885
- F: https://github.com/maxbry123-commits/agentes/commit/da51532329a69415a995908d48b274285cc98111

**Siguiente (solo append, sin borrar este restore):** re-añadir D + E + F al final de este archivo en salidas separadas.

---

# ANEXO A — RECUPERADO (resumen operativo del blob faa6d95)

## A1 Global
Control plane: forensic_core · gap_registry · checklist_sheriff · applicability · evidence_verifier · verdict_authority · closure_engine  
Execution: code_path_runner BLOCK sin context; evaluate; llm DENY  
Regla: CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS · NO CONTEXT → NO PROGRAMMING/AUDIT · REQUIRED no bypass

## A2 Forensic REQUIRED
CORE-01..14 · 4-pass · counters all 0 · evidence_complete · final_clean_reaudit · quality_dag_ok · claim_used_as_pass forbidden · OPEN→CLOSED forbidden

## A3–A16
Planos CONTROL→EXECUTION→EXTERNAL APPLY→RE-AUDIT  
CORE-01 REQUIREMENT … CORE-14 EVIDENCE/VERDICT  
CONNECTIVITY: DECLARED→…→BEHAVIOR_VERIFIED  
Counters: gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes  
API run_code_path: context/handoff default **False**  
GapRegistry lifecycle OPEN→FIXED→VERIFIED→CLOSED  
QualityDAG FORMAT→…→AUDIT · SKIP≠PASS  
Playbook: Context→Applicability→COPY-FIRST→Plan→Sheriff→Implement→CORE→Connectivity→Counters→run_code_path→Gap loop→Final reaudit→CLOSED

## B1 LIVE
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION → UNIFIED RUNTIME → COMMON INTERFACE · T0 DONE

## B2 PROGRAMMING
Hot path + pre_gate/COPY-FIRST/post_verify documentado · runner no escribe git

## B3 FORENSIC_MAP
REAL vs DOCUMENTED vs ABSENT · nota cruzada context default False actual

## C1–C3
Gaps §3–20 map · tabla paths canónicos · **04_3_MODOS** Función 1/2/3 íntegra

**Texto completo A+B+C del restore original:** ver blob faa6d95 (enlace arriba). Este commit restaura main tras el borrado accidental da515323.

---

# ANEXO G — 4 DOCS × 4 PASADAS (SOLO APPEND · sin borrar nada anterior)

## G0. Docs de este lote
1. 48_ARQUITECTURA_LOOP_GATEWAY_ROUTER_V1.md  
2. 00_METODO_TRABAJO_Y_ARQUITECTURA.md  
3. 43_CODE_PATH_V1_ARCH_UPGRADE.md  
4. CURSOR_200 (1–200)

---

## G1. 48_LOOP_GATEWAY — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | AUSENTE en main post-restore |
| P2 | Loop→Gateway→Router; no colapsar con C-19 |
| P3 | Prohíbe Loop→LLM directo; OpenClaw/Hermes=EnginePort |
| P4 | Append abajo |

**Contenido:**
```
LOOP CONTROLLER (maxbry_loop v2 + 12-stage + code-path tasks)
  → INTELLIGENCE GATEWAY (task_id, trace_id, capability, policy, payload)
  → ROUTER UNIVERSAL (HTTP client, otro repo)
  → LLM PROVIDERS | MEMORY ORCHESTRATOR
```
Prohibido prod: Loop→OpenAI/Anthropic directo. Offline: MockAdapter.  
Fusión: maxbry_loop v2 · 12-stage hooks · code_path como tasks · cognitive absorbed · Kimi slot R2.  
Contratos: IntelligenceGateway · Mock · RouterHTTPGateway · EnginePort.reason · Acquire recipes YAML.  
Bloques V1 ~38: V0 VG VK VL VF VA VH VQ VD.  
DONE: sin LLM directo · mock tests · ROUTER_URL · EnginePort stubs · acquire · forensic gap→task · flags OFF.

---

## G2. 00_METODO — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | AUSENTE en main post-restore |
| P2 | Enlaza PROGRAMMING + FORENSIC_MAP + code paths |
| P3 | Cadena política vs cadena REAL |
| P4 | Append abajo |

**Contenido:**
Cadena política: CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED | FIX LOOP  
Cadena REAL histórica: pre_gate → quality_bar → goal_lock → cognitive_loop → evidence → post_verify(VerdictAuthority)  
COPY-FIRST: name+catalog+AST → COPY/ADAPT; GENERATE last; SOURCE→DEST+SHA  
CONTROL DE TRABAJO: 1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE · 5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad  
Nota: cadena histórica convive con §2 forensic_core; matriz §5 prioriza body actual del runner.

---

## G3. 43_CODE_PATH — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | AUSENTE en main post-restore |
| P2 | 5 planos + C-21…31 > solo C-19 |
| P3 | Planner/DAG/Blackboard/Knowledge no en runner actual |
| P4 | Append abajo |

**Contenido:**
F40/F41/F42: Mission Planner · DAG · Blackboard · Event Bus · Policy · Context Builder · Knowledge Runtime · Expert Role Analyzer. Sin ancla Fxx → no programar.  
Gaps G-CODE-26…40. Tareas C-21…C-31 + C-01…19 = 30 salidas V1.1.  
5 planos: CONTROL · EXECUTION · KNOWLEDGE · STATE · OBSERVATION.  
Flujo: GoalLock → Council+Analyzer → Planner → DAG → Policy → Blackboard → Knowledge → Context → SE → Audit → MAIN_12 → Deploy → docs → CI.  
Reglas: Council decide · Planner divide · Knowledge obligatorio · LLM ~10% · ≤220 LOC · ficha.v2.  
Estado doc: C-01 CLOSED · siguiente C-02.

---

## G4. CURSOR_200 (1–200) — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | AUSENTE en main post-restore |
| P2 | Dataset → Applicability/Sheriff |
| P3 | No 200 gates runtime |
| P4 | Append bloques 1–200 abajo |

**1–25 Context:** Index semántico · @file · @codebase · @docs/@web · @git diff · @commit · Rules glob · Rules telemetry · Project memory · Sticky intent · Auto tabs · Auto selection · .cursorignore · Binary exclusion · Secrets redaction · Context budget · Pin files · Multi-root · Monorepo boundary · LSP symbols · Type diagnostics · Linter input · Test failure logs · Terminal output · Debug breakpoint  
**26–45 Plan:** Plan mode · Plan reviewed · Checkboxes · Plan→task graph · Blast radius · Risk · Test strategy · Rollback · ADR · Frozen hash · Re-plan · Parallel/serial · Human mid-plan · Max steps · Plan diff · DoD · Non-goals · Acceptance machine · Edit order · Dry-run  
**46–75 Edit:** Hunk/file accept · Multi-file txn · Atomic rollback · Staged AI · Plan id · Allowlist · Denylist · Max files/LOC/churn · Protect main · Feature branch · Dirty unrelated · Format · Imports · Code action · Rename LSP · Extract · Move+imports · Safe delete · Stub+TODO · Snippet · Skeleton · Partial markers · Conflict · 3-way · Undo · Redo  
**76–100 Verify:** Nearest test · Affected tests · Coverage · Typecheck · Lint · Format · Import cycle · Dead code · Complexity · Mutation · Snapshot · Visual · Contract consumers · Property · Fuzz · Bench · Mem leak · Race · Integration env · Ephemeral DB · HTTP mock · Golden · Flake · Timeout · Fail-fast  
**101–125 Git/PR:** Branch name · Conventional · Split commits · PR template · PR from diff · Link issue · CODEOWNERS · Risk label · CI green · Merge queue · Squash · Signed · GPG · Protected paths · Draft · Stacked · Cherry-pick · Rebase · Conflict gated · Changelog · Version · Release notes · Tag · Revert · Post-merge  
**126–150 Agent:** Tool prompts · Network/Shell allow · No sudo · Sandbox FS · Read-only · Ask vs Agent · Auto-apply off · Confirm destructive · Rate limit · Max turns/failures · Injection filter · Untrusted quarantine · Model pin · Temperature · Prompt checksum · Tool size · Exfil block · PII · Audit log · Replay · Export · Multi-agent iso · Supervisor veto  
**151–170 Arch:** Arch unit · Layer tests · Dep matrix · No cycles · Ports/adapters · Domain purity · ADR breach · RFC · Design review · OpenAPI · Schema-first · Compat · Feature flags · Strangler · Migration dry-run · Expand/contract · Shadow · Canary · SLO · Threat model  
**171–200 DX:** Composer · Chat-apply · Checkpoint · Restore · Image→code · Terminal agent · Background jobs · Bugbot · Inline chat · Docstring/tests · Explain · Fix diagnostics · PR from chat · Linear/Notion · MCP registry/allow · Custom modes · Memories · Privacy · Cost dashboard · Fast/slow · Tab metrics · Next-edit · Peek · Symbol search · Team rules · Rules lint · Extension conflict · Workspace trust · Rule version pin  
**Top 15 ROI:** 53 allowlist · 55–56 max files/LOC · 26–27 plan · 46–48 accept · 77 affected tests · 79–80 type/lint · 126–128 tool/shell · 15–16 secrets/budget · 109 CI · 107 CODEOWNERS · 151–154 arch · 138–139 injection · 146/173–174 ledger · 140 model pin · 5 git diff

---

## G5. Cierre lote

| Doc | Estado en main tras este append |
|------|--------------------------------|
| 48 | G1 añadido |
| 00 | G2 añadido |
| 43 | G3 añadido |
| CURSOR_200 | G4 añadido |

**Siguiente lote (4 docs):** CURSOR_300 · CURSOR_500 E001–E500 · (si falta) texto íntegro A/B de faa6d95 · (si falta) más de 43 diagrama.
