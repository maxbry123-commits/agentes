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

# ANEXO SALIDA 1 + B + C + D (preservados)

- A+B+C completos: https://github.com/maxbry123-commits/agentes/blob/faa6d95d597b87349ee1f8f1e5a45924b08859b7/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md  
- D (48 / 00 / 43): commit 11518bdc9f6b789fa5e525b51805ac2636e4f654  
No se borran; este push **añade solo ANEXO E**.

---

# ANEXO E — LISTAS CURSOR × 4 PASADAS (SOLO LO QUE FALTA · 2026-08-18)

## E0. 4 pasadas — los 3 documentos de listas

| Doc | P1 STRUCTURE | P2 CONNECTIVITY | P3 BEHAVIOR | P4 CLOSURE |
|------|--------------|-----------------|-------------|------------|
| CURSOR_200 (1–200) | AUSENTE en REAL | Dataset ref → Applicability/Sheriff | No 200 gates | Append íntegro abajo |
| CURSOR_300 (201–500) | AUSENTE | Idem | Idem | Append íntegro abajo |
| CURSOR_500_EXTRAS (E001–E500) | AUSENTE | ROI Wordflow E451–E500 | Podado | Append íntegro abajo |

**Uso:** dataset de referencia + sheriff/applicability; **no** 1000 gates runtime.

---

## E1. COPIA ÍNTEGRA — CURSOR_200 (1–200)

Fuente: `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md`

**A. Workspace & context (1–25):** 1 Index semántico · 2 @file · 3 @codebase · 4 @docs/@web · 5 @git diff · 6 @commit · 7 Rules glob · 8 Rules telemetry · 9 Project memory · 10 Sticky intent · 11 Auto tabs · 12 Auto selection · 13 .cursorignore · 14 Binary exclusion · 15 Secrets redaction · 16 Context budget · 17 Pin files · 18 Multi-root · 19 Monorepo boundary · 20 LSP symbols · 21 Type diagnostics · 22 Linter input · 23 Test failure logs · 24 Terminal output · 25 Debug breakpoint

**B. Planning (26–45):** 26 Plan mode multi-file · 27 Plan reviewed · 28 Checkboxes · 29 Plan→task graph · 30 Blast radius · 31 Risk score · 32 Test strategy · 33 Rollback · 34 ADR link · 35 Frozen hash · 36 Re-plan · 37 Parallel/serial · 38 Human mid-plan · 39 Max steps · 40 Plan diff · 41 DoD · 42 Non-goals · 43 Acceptance machine · 44 Edit order · 45 Dry-run

**C. Edit (46–75):** 46–48 Hunk/file accept · 49 Multi-file txn · 50 Atomic rollback · 51 Staged AI only · 52 Plan id required · 53 Allowlist · 54 Denylist · 55 Max files · 56 Max LOC · 57 Max churn · 58 Protect main · 59 Feature branch · 60 Dirty unrelated · 61 Format · 62 Imports · 63 Code action · 64 Rename LSP · 65 Extract · 66 Move+imports · 67 Safe delete · 68 Stub+TODO · 69 Snippet · 70 Skeleton · 71 Partial markers · 72 Conflict · 73 3-way · 74 Undo · 75 Redo

**D. Verification (76–100):** 76 Nearest test · 77 Affected tests · 78 Coverage delta · 79 Typecheck · 80 Lint · 81 Format · 82 Import cycle · 83 Dead code · 84 Complexity · 85 Mutation · 86 Snapshot policy · 87 Visual · 88 Contract consumers · 89 Property · 90 Fuzz · 91 Bench · 92 Mem leak · 93 Race · 94 Integration env · 95 Ephemeral DB · 96 HTTP mock · 97 Golden · 98 Flake · 99 Timeout · 100 Fail-fast

**E. Git/PR (101–125):** 101 Branch name · 102 Conventional · 103 Split commits · 104 PR template · 105 PR from diff · 106 Link issue · 107 CODEOWNERS · 108 Risk label · 109 CI green · 110 Merge queue · 111 Squash · 112 Signed · 113 GPG · 114 Protected paths · 115 Draft · 116 Stacked · 117 Cherry-pick · 118 Rebase · 119 Conflict gated · 120 Changelog · 121 Version · 122 Release notes · 123 Tag · 124 Revert · 125 Post-merge

**F. Agent safety (126–150):** 126 Tool prompts · 127 Network allow · 128 Shell allow · 129 No sudo · 130 Sandbox FS · 131 Read-only · 132 Ask vs Agent · 133 Auto-apply off · 134 Confirm destructive · 135 Rate limit · 136 Max turns · 137 Max failures · 138 Injection filter · 139 Untrusted quarantine · 140 Model pin · 141 Temperature · 142 Prompt checksum · 143 Tool size · 144 Exfil block · 145 PII · 146 Audit log · 147 Replay · 148 Export · 149 Multi-agent iso · 150 Supervisor veto

**G. Architecture (151–170):** 151 Arch unit · 152 Layer tests · 153 Dep matrix · 154 No cycles · 155 Ports/adapters · 156 Domain purity · 157 ADR breach · 158 RFC · 159 Design review · 160 OpenAPI · 161 Schema-first · 162 Compat · 163 Feature flags · 164 Strangler · 165 Migration dry-run · 166 Expand/contract · 167 Shadow · 168 Canary · 169 SLO · 170 Threat model

**H. DX Cursor (171–200):** 171 Composer · 172 Chat-apply · 173 Checkpoint · 174 Restore · 175 Image→code · 176 Terminal agent · 177 Background jobs · 178 Bugbot · 179 Inline chat · 180 Docstring/tests · 181 Explain · 182 Fix diagnostics · 183 PR from chat · 184 Linear/Notion · 185 MCP registry · 186 MCP allow · 187 Custom modes · 188 Memories · 189 Privacy · 190 Cost dashboard · 191 Fast/slow · 192 Tab metrics · 193 Next-edit · 194 Peek · 195 Symbol search · 196 Team rules · 197 Rules lint · 198 Extension conflict · 199 Workspace trust · 200 Rule version pin

**Top 15 ROI Wordflow (del doc):** 53 allowlist · 55–56 max files/LOC · 26–27 plan · 46–48 accept · 77 affected tests · 79–80 type/lint · 126–128 tool/shell · 15–16 secrets/budget · 109 CI · 107 CODEOWNERS · 151–154 arch · 138–139 injection · 146/173–174 ledger · 140 model pin · 5 git diff scope

---

## E2. COPIA ÍNTEGRA — CURSOR_300 (201–500)

Fuente: `PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md`

**I. Context adv (201–240):** sliding window · hybrid retrieval · symbol chunks · call-graph · type hierarchy · test/config/schema twin · CI failure corr · bug localization · stack map · profiling · dep constraints · LICENSE · CODEOWNERS prompt · branch intent · issue body · prior PR · design/ADR retrieval · anti-patterns · glossary · domain dict · error catalog · API errors · flags · env · queues · DB schema · migrations · permissions · tenant · i18n · a11y · perf budget · security · privacy · ownership · SLA · deprecation

**J. Multi-file (241–270):** cluster · consistency · rename cascade · interface fan-out · schema fan-out · constants · clones · layer violation · circular forecast · public API delta · internal leak · FFI · generated protect · vendor · lockfile · codegen order · GraphQL · IaC+app · mobile+API · docs+code · i18n+code · flag+code · metrics · dashboard · helm · terraform+IAM · migration+ORM · seed+schema · contract+mock · changelog+version+tag

**K. Testing (271–300):** characterization · approval · sociable/solitary · hexagonal doubles · fake vs mock · time provider · random seed · clock freeze · HTTP timeout · retry · circuit breaker · idempotency · exactly-once · poison · backpressure · pagination · authz matrix · multi-tenant · GDPR · encryption · key rotation · flag matrix · canary · schema evolution · wire compat · snapshot redaction · load · chaos · synthetic probe · test factory

**L. Refactor (301–330):** parallel change · branch by abstraction · strangler · ACL · walk skeleton · lift-shift · vertical slice · hexagonal · domain events · CQRS · read model · outbox · inbox · saga · process manager · retry storm · bulkhead · degradation · fail-open/closed · cache invalidation · pagination mig · sync→async · poll→webhook · monolith extract · shared lib version · gateway route · BFF · DTO vs domain · mapping tests · null-object

**M. Quality fino (331–360):** cognitive complexity · nesting · params · returns · cohesion · feature envy · data clumps · long params · shotgun · divergent · primitive obsession · speculative · dead store · unused public · TODO budget · suppressions · eslint-disable · type:ignore · Any · magic numbers · stringly · god class · leftover toggles · commented-out · debug print · hardcoded URL/creds · insecure deser · SQL concat · cmd injection

**N. Stack (361–390):** pyproject · ruff format/lint · mypy/pyright · pytest markers · coverage · pre-commit · dependabot · audit · lockfile · src-layout · namespace · __all__ · TYPE_CHECKING · Protocol · pydantic · dataclasses policy · async session · httpx timeout · SQLAlchemy · alembic · FastAPI deps · Next app router · hooks deps · server/client · CSP · bundle · tree-shake · env zod/pydantic

**O. Collab (391–420):** decision log · meeting→tasks · RFC tracker · design/sec/privacy/ops checklists · on-call · runbook · dashboard · alert · SLO · error budget · customer impact · support · docs semver · UI gif · a11y/i18n notes · analytics · experiment · kill switch · rollout · comms · postmortem · incident · learning · pair/mob · KB draft

**P. AI eval (421–450):** golden prompts · regression prompts · LLM-judge · human rating · accept/undo/escape rates · hallucinated path/API · invented import/config · wrong version · license-incompat · copy-paste drift · style/naming scores · snippet/docstring/stub accuracy · multi-model consensus · secondary review · proof obligations · formal spec · symbolic · differential · shadow · canary agent · A/B prompts · prompt registry

**Q. Platform (451–480):** background queue · notify · cancel · pause · worktree · devcontainer · remote SSH · codespace · GPU policy · browser allow · screenshot · Playwright · Storybook · MSW · OpenAPI client · SQL mig policy · TF plan · K8s validate · hadolint · compose · SBOM · CVE · attestations · OIDC · promotion · secrets mgr · Vault · feature store · notebook extract · data contracts

**R. Governance (481–500):** OPA · license allowlist · export control · residency · retention · model card · eval dataset · red team · jailbreak · permission board · access recert · MCP review · plugin allow · marketplace · telemetry privacy · consent · audit export · legal hold · break-glass · policy changelog

---

## E3. COPIA ÍNTEGRA — CURSOR_500_EXTRAS (E001–E500)

Fuente: `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md`

**E001–E050 Context** · **E051–E100 Plan/blast** · **E101–E150 Apply safety** · **E151–E200 Verify** · **E201–E250 Agent authority** · **E251–E300 Git/PR** · **E301–E350 Arch fitness** · **E351–E400 Quality signals** · **E401–E450 Stack gates** · **E451–E500 Wordflow ROI**

**E451–E500 (alto ROI Wordflow) — texto explícito:**  
E451 context default False · E452 handoff default False · E453 git-diff scope · E454 unexpected_changes git · E455 core True solo con measure · E456 mission edges API · E457 GapRegistry persist · E458 lifecycle OPEN→…→CLOSED · E459 forbid OPEN→CLOSED · E460 FourPassController real · E461 COPY when ADAPT · E462 adapt_imports wire · E463 symbol cache · E464 multi-repo roots · E465 reception index · E466 PolicySnapshot auto · E467 PlanArtifact multi-file · E468 PR SHA evidence · E469 run ledger ids · E470 catalog hash · E471 verdict baseline · E472–474 arch/forbidden/cycle CI · E475 caller inventory · E476 cognitive class in evidence · E477–478 quality/goal_lock tested · E479 consumer return dict · E480 post_verify required prod · E481 prod vs dev profile · E482 allowlist extensions/wordflow · E483 deny PIPELINE write sin flag · E484 paired test new engine · E485 catalog entry gate · E486 connect edge gate · E487 orphan CI · E488 unreachable path · E489 SOURCE→DEST ADAPT · E490 regenerate blocked hash match · E491 human gate auth/secrets · E492 injection scan raw_input · E493 untrusted reception sandbox · E494 model pin instance · E495 cost/token fields · E496 stage timings · E497 structured log · E498 forensic report path · E499 AGENTS links test · E500 .cursor/rules frontmatter test

**Texto línea-a-línea E001–E450** = path canónico `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md` (mismo repo; no se elimina).

---

## E4. Cierre listas

| Lista | En REAL |
|-------|--------|
| 1–200 | E1 completo por bloques + top 15 |
| 201–500 | E2 completo por bloques temáticos |
| E001–E500 | E3 ROI E451–500 explícito + resto en path canónico |

**Paths canónicos (verdad línea-a-línea):**  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/CURSOR_500_EXTRAS_PODADOS.md  
