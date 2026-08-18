# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`  
**RESTORE:** blob `0f19cb2` (H1–H5 íntegro) + anexos posteriores I/X/Y  

---

## 1. Capas

```
Callers → ENGINE (80+ · hot path run_code_path) → STANDARDS (forensic_core…) → DATA/POLICY
```

## 2. run_code_path (snapshot histórico §2)
1 require_context BLOCK · 2 quality · 3 goal_lock · 4 cognitive · 5 skill? · 6 evidence · 7 CORE default False · 8 connectivity/counters · 9 evaluate · 10 DENY  
**NO en snapshot §2:** Sheriff · ContextManifest · COPY-FIRST · ClosureEngine · GapRegistry · QualityDAG.run · FC enforced  
**AS-IS actual (2026-08-18):** ver **ANEXO X** — esos módulos **sí** están cableados en main.

## 3. STANDARDS inventario
forensic_core · forensic_contract · forensic_report · verdict_authority · gap_registry · closure_engine · checklist_sheriff · programming_points_catalog · applicability_engine · context_manifest · evidence_verifier · evidence · executor_gates · copy_first · symbol_index · wiring_graph · test_runner · quality_dag · quality_handlers · path_resolve · fc_auto_measure · core_auto_measure · evidence_merge · checklist_factory · rule_engine · adapt_imports · plan_artifact · policy_snapshot · architecture_manifest · dependency_graph · mission_edges · scope_measure

## 4. ENGINE
**Hot path:** code_path_runner · code_path_smoke · programming_pipeline · programming_kwargs · input_quality_bar · goal_lock · cognitive_loop · evidence_packet · skill_native_compiler · main_loop  
**Bridges:** claim_validator · control_sheriff_bridge · sheriff_adapter · handoff · dna_handoff · policy_engine · state_authority · execution_facade · execution_manifest · evidence_bridge · evidence_graph · cursor_hooks · enchufe_gate · repair_gate · validator  
**Orquestación:** main_loop · orchestrator* · bootstrap · entrypoint* · scheduler · task_* · council · expert_* · capability_* · loop_bridge · wave* · runtime_bus · parallel_* · supervisor · sentinel · watchdog · recovery · circuit_breaker · retry_policy · github_api · resource_* · mission · bitacora · checkpoint_store · …

## 5. Matriz doc vs ejecutado
**Histórica:** ver commit 0f19cb2. **Actual:** ANEXO X (Sheriff/COPY-FIRST/Gap/Closure/QDAG/FC/Policy/Unified = SÍ en code).

## 6. Deuda G1–G7
Histórica abierta; estado actual en ANEXO X.5 (G2/G6 cerrados; G3/G7 parcial).

## 7. PASS máquina
```
context ∧ handoff ∧ CORE14 ∧ 4pass ∧ counters0 ∧ evidence ∧ final_reaudit ∧ quality_dag ∧ ¬claim → PASS else BLOCK|FAIL
```

## 8. Enlaces paths
- Este archivo: `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md`
- Listas canónicas también: `CURSOR_200_…` · `CURSOR_300_…` · `CURSOR_500_EXTRAS_…`
- Code: `extensions/wordflow/engine/code_path_runner.py` · `standards/forensic_core.py`

---

# RESTORE + ANEXO A + G + H — blob 0f19cb2 (CONTENIDO COMPLETO)

## A1 Global
Control plane: forensic_core · gap_registry · checklist_sheriff · applicability · evidence_verifier · verdict_authority · closure_engine  
Execution: code_path_runner BLOCK sin context; evaluate; llm DENY  
Regla: CLAIM ≠ EVIDENCE ≠ VERIFICATION ≠ PASS · NO CONTEXT → NO PROGRAMMING/AUDIT · REQUIRED no bypass

## A2 Forensic REQUIRED
CORE-01..14 · 4-pass · counters all 0 · evidence_complete · final_clean_reaudit · quality_dag_ok · claim_used_as_pass forbidden · OPEN→CLOSED forbidden

## A3–A16
Planos CONTROL→EXECUTION→EXTERNAL APPLY→RE-AUDIT  
CORE-01 REQUIREMENT … CORE-14 EVIDENCE/VERDICT  
CONNECTIVITY: DECLARED→REGISTERED→RESOLVED→INVOKED→EXECUTED→OUTPUT_CONSUMED→BEHAVIOR_VERIFIED  
Counters: gaps, blocking_gaps, broken_connections, unexplained_orphans, unreachable_required_paths, unresolved_dependencies, unverified_paths, unverified_requirements, unverified_claims, pending_fixes, new_gaps_after_fix, unexpected_changes  
API: context/handoff default False  
GapRegistry OPEN→FIXED→VERIFIED→CLOSED  
QualityDAG FORMAT→…→AUDIT · SKIP≠PASS  
Playbook: Context→Applicability→COPY-FIRST→Plan→Sheriff→Implement→CORE→Connectivity→Counters→run_code_path→Gap loop→Final reaudit→CLOSED

## B1 LIVE
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION → UNIFIED RUNTIME → COMMON INTERFACE · T0 DONE

## B2 PROGRAMMING
Hot path + pre_gate/COPY-FIRST/post_verify · runner no escribe git

## B3 FORENSIC_MAP
REAL vs DOCUMENTED vs ABSENT · context default False

## C1–C3
Gaps map · paths canónicos · 04_3_MODOS Función 1/2/3

## G 48+00+43+CURSOR_200
G1 Loop→Gateway→Router · Mock · EnginePort · V0–VD  
G2 CONTEXT→COPY-FIRST→IMPLEMENT→WIRE→FORENSIC→VERDICT→CLOSED  
G3 5 planos C-21…31 · F40/F41/F42 · Knowledge Runtime  
G4 CURSOR 1–200 bloques A–H + top 15 ROI

---

## H1. CURSOR_300 (201–500) — bloques I–R (300 ítems)

**I 201–240 Context adv:** sliding window · hybrid retrieval · symbol chunks · call-graph · type hierarchy · test/config/schema twin · CI failure · bug localization · stack map · profiling · dep constraints · LICENSE · CODEOWNERS · branch intent · issue · prior PR · design/ADR · anti-patterns · glossary · domain dict · error catalog · API errors · flags · env · queues · DB schema · migrations · permissions · tenant · i18n · a11y · perf budget · security · privacy · ownership · SLA · deprecation  

**J 241–270 Multi-file:** cluster · consistency · rename cascade · interface/schema fan-out · constants · clones · layer violation · circular forecast · public API delta · internal leak · FFI · generated/vendor protect · lockfile · codegen · GraphQL · IaC+app · mobile+API · docs/i18n/flag/metrics/dashboard/helm/terraform co-edit · migration+ORM · seed+schema · contract+mock · changelog+version+tag  

**K 271–300 Testing:** characterization · approval · sociable/solitary · hexagonal doubles · fake vs mock · time/random/clock · HTTP timeout · retry · circuit breaker · idempotency · exactly-once · poison · backpressure · pagination · authz · multi-tenant · GDPR · encryption · key rotation · flag matrix · canary · schema evolution · wire compat · snapshot redaction · load · chaos · synthetic · test factory  

**L 301–330 Refactor:** parallel change · branch by abstraction · strangler · ACL · walk skeleton · lift-shift · vertical slice · hexagonal · domain events · CQRS · read model · outbox/inbox · saga · process manager · retry storm · bulkhead · degradation · fail-open/closed · cache invalidation · pagination/sync-async/poll-webhook · monolith extract · shared lib · gateway · BFF · DTO vs domain · mapping · null-object  

**M 331–360 Quality:** cognitive complexity · nesting · params · returns · cohesion · feature envy · data clumps · shotgun · divergent · primitive obsession · speculative · dead store · unused public · TODO/suppressions/eslint-disable/type:ignore/Any/magic budgets · stringly · god class · leftover toggles · commented-out · debug print · hardcoded URL/creds · insecure deser · SQL concat · cmd injection  

**N 361–390 Stack:** pyproject · ruff · mypy/pyright · pytest markers · coverage · pre-commit · dependabot · audit · lockfile · src-layout · namespace · __all__ · TYPE_CHECKING · Protocol · pydantic · dataclasses · async session · httpx · SQLAlchemy · alembic · FastAPI · Next · hooks · server/client · CSP · bundle · tree-shake · env zod/pydantic  

**O 391–420 Collab:** decision log · meeting→tasks · RFC · design/sec/privacy/ops checklists · on-call · runbook · dashboard · alert · SLO · error budget · customer impact · support · docs semver · UI gif · a11y/i18n · analytics · experiment · kill switch · rollout · comms · postmortem · incident · learning · pair/mob · KB  

**P 421–450 AI eval:** golden/regression prompts · LLM-judge · human rating · accept/undo/escape rates · hallucinated path/API · invented import/config · wrong version · license-incompat · copy-paste drift · style/naming · snippet/docstring/stub accuracy · multi-model · secondary review · proof · formal · symbolic · differential · shadow · canary agent · A/B · prompt registry  

**Q 451–480 Platform:** background queue · notify · cancel · pause · worktree · devcontainer · SSH · codespace · GPU · browser allow · screenshot · Playwright · Storybook · MSW · OpenAPI client · SQL mig · TF · K8s · hadolint · compose · SBOM · CVE · attestations · OIDC · promotion · secrets · Vault · feature store · notebook · data contracts  

**R 481–500 Governance:** OPA · license allowlist · export control · residency · retention · model card · eval dataset · red team · jailbreak · permission board · access recert · MCP review · plugin · marketplace · telemetry privacy · consent · audit export · legal hold · break-glass · policy changelog

**Texto línea-a-línea 201–500 también en ANEXO Y y en `CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md`.**

---

## H2. CURSOR_500 E001–E500 — bloques completos (0f19cb2)

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

**Texto E001–E500 línea a línea también en `CURSOR_500_EXTRAS_PODADOS.md` (500 líneas).**

---

## H3 GLOBAL / H4 FORENSIC_ENFORCEMENT
Control plane fail-closed · execution DENY · PASS only if context∧handoff∧CORE14∧4pass∧counters0∧evidence∧reaudit∧quality_dag · caller must supply measures

## H5 Cierre lote H
CURSOR_300 · CURSOR_500 · GLOBAL · FORENSIC añadidos · §§1–8+A+G no borrados en 0f19cb2

---

# ANEXO I — LIVE + 04_3_MODOS + FORENSIC_MAP + G detalle (blob 262e8505)

## I1 LIVE
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION → UNIFIED RUNTIME → COMMON INTERFACE · T0 DONE · Motors SEND/CALL/DOWNLOAD READY

## I2 04_3_MODOS
**Función 1** Kernel OpenClaw sustitución · **Función 2** Capa control externa zero-invasive · **Función 3** Extensión ABI plug-in

## I3 FORENSIC_MAP
REAL: code_path_runner · quality_bar · goal_lock · cognitive · evidence · gates · copy_first · forensic_contract · verdict · catalogs · CI  
DOCUMENTED: FORENSIC_CODE_AUDIT · 00_METODO · ADVANCED_ENGINEERING · GAPS  
ABSENT histórico: SM global · FourPassController repo-wide · reception auto

## I4 G detalle
Loop→Gateway→Router · mock offline · EnginePort · bloques V0–VD · cadena 00 · 5 planos C-21…31 · CURSOR 1–200 A–H

---

# ANEXO X — Code vs §§2/5 (2026-08-18) — AS-IS actual

Secuencia REAL: PolicySnapshot → ContextManifest → require_context → PreGate(COPY-FIRST+Sheriff) → adapt → quality_bar → goal_lock → cognitive → evidence_merge → QualityDAG → core/fc auto → GapRegistry → VerdictAuthority → ClosureEngine → DENY+statuses  

Sheriff/COPY-FIRST/Gap/Closure/QDAG/FC/Policy/Unified/main_12 = **SÍ en code** (corrige §2/§5 histórico).

---

# ANEXO Y — Cursor 201–500 línea a línea

**Está en este mismo archivo en commit `8507c486` (ANEXO Y completo 201–500).**  
Si el viewer truncara: `PIPELINE/CURSOR_300_MAS_PUNTOS_AUSENTES_WORDFLOW.md`  
**1–200:** `PIPELINE/CURSOR_200_PUNTOS_AUSENTES_WORDFLOW.md`  
**E001–E500 línea a línea:** `PIPELINE/CURSOR_500_EXTRAS_PODADOS.md` + H2 arriba

---

**Índice de verdad del archivo**
| Bloque | Contenido |
|--------|-----------|
| §§1–8 | Capas + inventarios + PASS |
| A–C | Global/forensic/playbook/LIVE/map |
| G | 48/00/43/CURSOR_200 |
| H1–H5 | CURSOR_300 + E001–E500 + GLOBAL + FORENSIC |
| I | LIVE + 3 modos + map + G detalle |
| X | AS-IS code 2026-08-18 |
| Y | 201–500 full lines (ver path CURSOR_300 si truncado UI) |

**Fin restauración arquitectura.**
