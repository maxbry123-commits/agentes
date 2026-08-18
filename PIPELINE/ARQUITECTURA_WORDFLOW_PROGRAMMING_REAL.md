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

**Blob fuente:** https://github.com/maxbry123-commits/agentes/blob/faa6d95d597b87349ee1f8f1e5a45924b08859b7/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md

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

---

# ANEXO G — 48 + 00 + 43 + CURSOR_200 (PRESERVADO · no borrar)

G1 48: Loop→Gateway→Router · Mock · EnginePort · bloques V0–VD  
G2 00: CONTEXT→COPY-FIRST→IMPLEMENT→WIRE→FORENSIC→VERDICT→CLOSED  
G3 43: 5 planos · C-21…31 · F40/F41/F42 · Knowledge Runtime  
G4 CURSOR_200: puntos 1–200 por bloques A–H + top 15 ROI  

(Detalle completo G1–G4 en commit 2cd0547a55cddcc6d89005f600534162039ce245 — contenido G estaba íntegro en versión previa de este archivo.)

---

# ANEXO H — 4 DOCS × 4 PASADAS (SOLO APPEND)

## H0. Docs de este lote
1. CURSOR_300 (201–500)  
2. CURSOR_500_EXTRAS (E001–E500)  
3. ARQUITECTURA_WORDFLOW_GLOBAL (ampliado)  
4. FORENSIC_ENFORCEMENT_REQUIRED (ampliado)

---

## H1. CURSOR_300 (201–500) — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | Faltaba en main post-G |
| P2 | Dataset 201–500 |
| P3 | No 300 gates runtime |
| P4 | Append |

**I 201–240 Context adv:** sliding window · hybrid retrieval · symbol chunks · call-graph · type hierarchy · test/config/schema twin · CI failure · bug localization · stack map · profiling · dep constraints · LICENSE · CODEOWNERS prompt · branch intent · issue body · prior PR · design/ADR · anti-patterns · glossary · domain dict · error catalog · API errors · flags · env · queues · DB schema · migrations · permissions · tenant · i18n · a11y · perf budget · security · privacy · ownership · SLA · deprecation  
**J 241–270 Multi-file:** cluster · consistency · rename cascade · interface/schema fan-out · constants · clones · layer violation · circular forecast · public API delta · internal leak · FFI · generated/vendor protect · lockfile · codegen · GraphQL · IaC+app · mobile+API · docs/i18n/flag/metrics/dashboard/helm/terraform co-edit · migration+ORM · seed+schema · contract+mock · changelog+version+tag  
**K 271–300 Testing:** characterization · approval · sociable/solitary · hexagonal doubles · fake vs mock · time/random/clock · HTTP timeout · retry · circuit breaker · idempotency · exactly-once · poison · backpressure · pagination · authz · multi-tenant · GDPR · encryption · key rotation · flag matrix · canary · schema evolution · wire compat · snapshot redaction · load · chaos · synthetic · test factory  
**L 301–330 Refactor:** parallel change · branch by abstraction · strangler · ACL · walk skeleton · lift-shift · vertical slice · hexagonal · domain events · CQRS · read model · outbox/inbox · saga · process manager · retry storm · bulkhead · degradation · fail-open/closed · cache invalidation · pagination/sync-async/poll-webhook mig · monolith extract · shared lib · gateway · BFF · DTO vs domain · mapping · null-object  
**M 331–360 Quality:** cognitive complexity · nesting · params · returns · cohesion · feature envy · data clumps · shotgun · divergent · primitive obsession · speculative · dead store · unused public · TODO/suppressions/eslint-disable/type:ignore/Any/magic budgets · stringly · god class · leftover toggles · commented-out · debug print · hardcoded URL/creds · insecure deser · SQL concat · cmd injection  
**N 361–390 Stack:** pyproject · ruff · mypy/pyright · pytest markers · coverage · pre-commit · dependabot · audit · lockfile · src-layout · namespace · __all__ · TYPE_CHECKING · Protocol · pydantic · dataclasses · async session · httpx · SQLAlchemy · alembic · FastAPI · Next · hooks · server/client · CSP · bundle · tree-shake · env zod/pydantic  
**O 391–420 Collab:** decision log · meeting→tasks · RFC · design/sec/privacy/ops checklists · on-call · runbook · dashboard · alert · SLO · error budget · customer impact · support · docs semver · UI gif · a11y/i18n · analytics · experiment · kill switch · rollout · comms · postmortem · incident · learning · pair/mob · KB  
**P 421–450 AI eval:** golden/regression prompts · LLM-judge · human rating · accept/undo/escape rates · hallucinated path/API · invented import/config · wrong version · license-incompat · copy-paste drift · style/naming · snippet/docstring/stub accuracy · multi-model · secondary review · proof · formal · symbolic · differential · shadow · canary agent · A/B · prompt registry  
**Q 451–480 Platform:** background queue · notify · cancel · pause · worktree · devcontainer · SSH · codespace · GPU · browser allow · screenshot · Playwright · Storybook · MSW · OpenAPI client · SQL mig · TF · K8s · hadolint · compose · SBOM · CVE · attestations · OIDC · promotion · secrets · Vault · feature store · notebook · data contracts  
**R 481–500 Governance:** OPA · license allowlist · export control · residency · retention · model card · eval dataset · red team · jailbreak · permission board · access recert · MCP review · plugin · marketplace · telemetry privacy · consent · audit export · legal hold · break-glass · policy changelog

---

## H2. CURSOR_500 E001–E500 — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | Faltaba línea a línea en main |
| P2 | ROI Wordflow E451–E500 |
| P3 | Dataset sheriff |
| P4 | Append bloques completos |

**E001–E050 Context:** @file · @folder · @git diff · LSP · test log · stack map · call-graph · test/config/schema twin · .cursorignore · secrets · budget · pin · multi-root · package boundary · CI failure · CODEOWNERS · issue · ADR · design · glossary · error/env/flag catalogs · deprecation · generated/vendor protect · negative examples · symbol chunks · type hierarchy · import graph · diff hunks · open editors · selection · terminal · pre-commit · type/lint burst · lockfile · migration · permission · public API · internal leak · clones · dead export · TODO/FIXME · suppressions · related PR · branch intent  
**E051–E100 Plan:** plan mode · artifact · frozen hash · non-goals · acceptance · blast · risk · test/rollback strategy · order · dry-run · max steps · re-plan · parallel/serial · mid approval · cluster · fan-out interface/schema · rename cascade · co-edit docs/tests/i18n/flag · lockfile · codegen · migration before ORM · contract before mock · version · changelog · ADR · no-touch-core · allow/deny paths · max files/LOC · DoD · GENERATE vs ADAPT · COPY sources · evidence · post-conditions · invariants · error-path · observability · security · data · concurrency · idempotency · performance · compat · exit criteria  
**E101–E150 Apply:** allow/deny paths · max files/LOC/churn · feature branch · protect branch · atomic · rollback · undo · hunk/file accept · format · lint-fix · imports · conflict · 3-way · generated protect · no secrets/.env · paired test/snapshot · rename LSP · move+imports · safe delete · partial markers · no silent drop · plan id/hash · stage vs apply · worktree · dirty · lockfile · binary/large deny · symlink · line-ending · license/copyright · utf-8 · no reformat unrelated · minimize diff · single concern · split · description · task id · SOURCE→DEST · import rewrites · file/hash evidence  
**E151–E200 Verify:** typecheck · lint · format · affected unit · integration · coverage · cycle · dead · complexity · secret scan · dep audit · license · lockfile drift · schema · OpenAPI · contract consumers · snapshot · flake · timeout · fail-fast · smoke · build · import/entrypoint smoke · migration dry-run · idempotency/concurrency/authz/validation/error/characterization/differential · golden · bench · bundle · a11y · i18n · CSP · docker/compose/TF/K8s · SBOM/CVE release · CI green · pre-push/pre-commit · skip≠pass · missing gate=fail · evidence packet  
**E201–E250 Agent:** ask default · agent explicit · auto-apply off · tool/shell/network allow · no sudo · read-only · max tool/turns/failures · confirm destructive · injection · untrusted quarantine · model pin · temperature · prompt checksum · tool size · exfil · PII · audit · export · replay · supervisor · multi-agent · MCP allow/review · plugin · rate · cost/token budget · fast/slow · secondary review · hallucinated path/symbol · invented import/config · copy-paste drift · style · naming · prompt/rules version · policy snapshot · change/mission/task id · human gate · risk secrets · deny prod creds · sandbox FS  
**E251–E300 Git/PR:** conventional · split · template · body from diff · link task · CODEOWNERS · risk labels · draft · CI green · signed · protected · changelog · version · revert · post-merge · branch from task · no secrets · no force main · merge queue · squash · conflict gated · stacked · release notes · tag · size/file limits · tests/docs required · screenshot/a11y/migration/flag/rollback notes · owner · review SLA · stale · block TODO/gates · approval N · dismiss stale · CODEOWNERS standards/kernel · binary/blob deny · submodule/vendor · generated mark · checklist · forensic+plan hash links  
**E301–E350 Arch fitness:** layer tests · no cycles · dep matrix · domain purity · ports/adapters · forbidden imports · public API delta · semver · ADR · no-touch-core · LOC/fan-out/fan-in budgets · SDP/ADP · boundary engine/standards/kernel · catalog entry · connect edge · orphan/unreachable/dead/duplicate reports · naming · event/DTO version · expand/contract · feature flag · deprecation · flag deadline · arch CI · import linter · dep cruiser · metrics · hotspot · churn · knowledge concentration · bus factor · owned map · experimental/deprecated/examples/scripts/tools/generated/third_party policy · docs real paths · PIPELINE links · no doc-only claims · diagram from catalogs · arch drift bot  
**E351–E400 Quality signals:** cognitive complexity · nesting · params · cohesion · feature envy · god class · magic/Any/type:ignore/lint-disable/TODO budgets · commented-out · debug print · hardcoded URL · SQL concat · cmd injection · insecure deser · path traversal · SSRF/XSS · pickle/eval · assert control · bare except · mutable default · resource leak · file handle · timeout missing · retry no jitter · busy wait · N+1 · unbounded list · missing pagination · naive datetime · timezone · float money · UUID/string · enum drift · dict typo · optional · race dict · lock ordering · async cancel · task group · context manager · idempotent · exactly-once banned · at-least-once · poison · backpressure · graceful shutdown  
**E401–E450 Stack:** ruff format/lint · mypy/pyright · pytest markers · coverage · pre-commit · audit · lockfile · src layout · pydantic/zod · httpx timeout · SQLAlchemy · alembic · FastAPI · React hooks · server/client · env schema · no scattered env · structured log · request id · OTel · health/readiness/metrics · graceful timeout · docker non-root · dockerignore · multi-stage · pin images · no latest · CI cache/matrix/artifacts · determinism seed · freezegun · respx · factories · hypothesis · snapshot · ts strict · eslint · prettier · no-floating-promises · exhaustiveness · import type · side-effect free · barrels · circular barrels · tree-shake · bundle analyzer  
**E451–E500 Wordflow ROI:** E451 context default False · E452 handoff default False · E453 git-diff scope · E454 unexpected_changes git · E455 core True solo con measure · E456 mission edges API · E457 GapRegistry persist · E458 lifecycle enforced · E459 forbid OPEN→CLOSED · E460 FourPassController real · E461 COPY when ADAPT · E462 adapt_imports wire · E463 symbol cache · E464 multi-repo roots · E465 reception index · E466 PolicySnapshot auto · E467 PlanArtifact · E468 PR SHA evidence · E469 run ledger ids · E470 catalog hash · E471 verdict baseline · E472–474 arch/forbidden/cycle CI · E475 caller inventory · E476 cognitive class evidence · E477–478 quality/goal_lock tested · E479 consumer return dict · E480 post_verify required prod · E481 prod vs dev · E482 allowlist wordflow · E483 deny PIPELINE write · E484 paired test · E485 catalog entry gate · E486 connect edge gate · E487 orphan CI · E488 unreachable path · E489 SOURCE→DEST ADAPT · E490 regenerate blocked · E491 human gate auth · E492 injection scan · E493 untrusted reception · E494 model pin · E495 cost/token · E496 stage timings · E497 structured log · E498 forensic report path · E499 AGENTS links test · E500 .cursor/rules frontmatter test

---

## H3. ARQUITECTURA_WORDFLOW_GLOBAL — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | Solo resumen A1 |
| P2 | Control vs execution plane |
| P3 | Fail-closed rules |
| P4 | Append ampliado |

**Control plane (fail-closed):** forensic_core (CORE14+4-pass+counters+PASS) · gap_registry · checklist_sheriff + applicability + evidence_verifier · verdict_authority / closure_engine  
**Execution plane:** code_path_runner — BLOCK sin context; forensic evaluate obligatorio; llm DENY  
**Data:** catalogs JSON · PIPELINE policy · CI forensic-gates  
**Regla de oro:** CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS · NO VERIFIED CONTEXT → NO PROGRAMMING / NO AUDIT · REQUIRED no se bypasea

---

## H4. FORENSIC_ENFORCEMENT_REQUIRED — 4 pasadas
| P | Hallazgo |
|---|----------|
| P1 | Solo resumen A2 |
| P2 | Runtime paths |
| P3 | PASS rules |
| P4 | Append ampliado |

**Runtime:** standards/forensic_core.py · engine/code_path_runner.py · standards/gap_registry.py  
**Rules:** NO VERIFIED CONTEXT → NO PROGRAMMING/AUDIT · CLAIM≠EVIDENCE≠VERIFICATION≠PASS · required_without_handler=FAIL · required_skip=FAIL · skip!=pass · OPEN→CLOSED forbidden · all_four_passes_required · no_dev_bypass_required  
**PASS only if:** context_verified ∧ handoff_verified ∧ CORE14 ∧ 4 passes ∧ counters all 0 ∧ evidence_complete ∧ final_clean_reaudit ∧ quality_dag_ok  
**Caller must supply:** core_measures[CORE-01..14] · connectivity flags · counters · evidence_complete · final_clean_reaudit_passed · quality_dag_ok

---

## H5. Cierre lote H

| Doc | Estado |
|------|--------|
| CURSOR_300 | H1 añadido |
| CURSOR_500 E001–E500 | H2 añadido |
| GLOBAL | H3 ampliado |
| FORENSIC_ENFORCEMENT | H4 ampliado |

**Confirmación:** §§1–8 + RESTORE + A + G **no se borraron**. Solo se añadió Anexo H al final.

**Archivo:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md
