# ARQUITECTURA REAL — Wordflow Programming (post verificación cruzada)

**Fecha:** 2026-08-18  
**Base:** listado GitHub `extensions/wordflow/engine/` + `standards/` + `code_path_runner.py` + `forensic_core.py`  
**MASTER único (listas 1–500 / E001–E500):** `PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md`

**RESTAURADO desde commit 8507c486 (ANEXO Y 201–500 línea a línea). NO borrar este cuerpo.**
**RESTORE 6e8a91a2:** ANEXO X X.1–X.7 + ANEXO Y 201–500. NO truncar.

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

1. ForensicProgrammingEnforcer.require_context → BLOCK si falta  
2. admit_or_reject (quality_bar)  
3. lock_goals  
4. run_cognitive_loop  
5. compile_skill_to_code (si skill)  
6. build/verify evidence_packet  
7. CORE-01..14 desde core_measures (default False)  
8. Connectivity + ClosureCounters  
9. ForensicProgrammingEnforcer.evaluate  
10. Return ok, verdict, forensic, llm_control=DENY  

### NO en snapshot §2
ChecklistSheriff · ContextManifest object · COPY-FIRST · executor_gates · ClosureEngine · GapRegistry · QualityDAG.run · FC enforced  
**AS-IS:** ANEXO X abajo.

---

## 3. Inventario STANDARDS
forensic_core · forensic_contract · forensic_report · verdict_authority · gap_registry · closure_engine · checklist_sheriff · programming_points_catalog · applicability_engine · context_manifest · evidence_verifier · evidence · executor_gates · copy_first · symbol_index · wiring_graph · test_runner · quality_dag · rule_engine · sheriff · schema · adapt_imports · plan_artifact · policy_snapshot · architecture_manifest · dependency_graph · mission_edges · scope_measure · path_resolve · quality_handlers · fc_auto_measure · core_auto_measure · evidence_merge · __init__

## 4. Inventario ENGINE
Hot: code_path_runner · code_path_smoke · programming_pipeline · programming_kwargs · input_quality_bar · goal_lock · cognitive_loop · evidence_packet · skill_native_compiler · main_loop  
Bridges: claim_validator · control_sheriff_bridge · sheriff_adapter · handoff · dna_handoff · policy_engine · state_authority · execution_facade · execution_manifest · evidence_bridge · evidence_graph · cursor_hooks · enchufe_gate · repair_gate · validator  
Orquestación: main_loop · orchestrator* · bootstrap · entrypoint* · scheduler · task_* · council · expert_* · capability_* · loop_bridge · wave* · runtime_bus · parallel_* · supervisor · sentinel · watchdog · recovery · circuit_breaker · retry_policy · github_api · resource_* · mission · bitacora · checkpoint_store

## 5–7. PASS / G → ANEXO X
## 8. Enlaces CURSOR_200 · CURSOR_300 · CURSOR_500_EXTRAS

---

# ANEXO Y — 201–500 COMPLETA (300 ítems) — NO BORRAR

201–240 Context: sliding window · hybrid retrieval · symbol chunks · call-graph · type hierarchy · test/config/schema twin · CI failure · bug localization · stack map · profiling · dep constraints · LICENSE · CODEOWNERS · branch intent · issue · prior PR · design/ADR · anti-patterns · glossary · domain · error catalog · API errors · flags · env · queues · DB schema · migrations · permissions · tenant · i18n · a11y · perf · security · privacy · ownership · SLA · deprecation

241–270 Multi-file: cluster · consistency · rename cascade · interface/schema fan-out · constants · clones · layer violation · circular · public API delta · internal leak · FFI · generated/vendor · lockfile · codegen · GraphQL · IaC · mobile+API · docs/i18n/flag/metrics/dashboard/helm/terraform · migration+ORM · seed · contract+mock · changelog+version+tag

271–300 Testing: characterization · approval · sociable/solitary · hexagonal · fake/mock · time/random/clock · HTTP timeout · retry · circuit · idempotency · exactly-once · poison · backpressure · pagination · authz · multi-tenant · GDPR · encryption · key rotation · flag matrix · canary · schema evolution · wire · snapshot · load · chaos · synthetic · factory

301–330 Refactor: parallel change · branch by abstraction · strangler · ACL · walk skeleton · lift-shift · vertical slice · hexagonal · domain events · CQRS · read model · outbox/inbox · saga · process manager · retry storm · bulkhead · degradation · fail-open/closed · cache · pagination/sync-async/poll-webhook · monolith extract · shared lib · gateway · BFF · DTO · mapping · null-object

331–360 Quality: cognitive complexity · nesting · params · returns · cohesion · feature envy · data clumps · shotgun · divergent · primitive obsession · speculative · dead store · unused public · TODO/suppressions/eslint/type:ignore/Any/magic · stringly · god class · toggles · commented-out · debug · hardcoded URL/creds · insecure deser · SQL concat · cmd injection

361–390 Stack: pyproject · ruff · mypy/pyright · pytest · coverage · pre-commit · dependabot · audit · lockfile · src-layout · namespace · __all__ · TYPE_CHECKING · Protocol · pydantic · dataclasses · async · httpx · SQLAlchemy · alembic · FastAPI · Next · hooks · server/client · CSP · bundle · tree-shake · env schema

391–420 Collab: decision log · meeting→tasks · RFC · design/sec/privacy/ops · on-call · runbook · dashboard · alert · SLO · error budget · customer impact · support · docs semver · UI gif · a11y/i18n · analytics · experiment · kill switch · rollout · comms · postmortem · incident · learning · pair/mob · KB

421–450 AI eval: golden/regression · LLM-judge · human rating · accept/undo/escape · hallucinated path/API · invented import/config · wrong version · license · copy-paste drift · style/naming · snippet/docstring/stub · multi-model · secondary · proof · formal · symbolic · differential · shadow · canary · A/B · prompt registry

451–480 Platform: queue · notify · cancel · pause · worktree · devcontainer · SSH · codespace · GPU · browser · screenshot · Playwright · Storybook · MSW · OpenAPI · SQL mig · TF · K8s · hadolint · compose · SBOM · CVE · attestations · OIDC · promotion · secrets · Vault · feature store · notebook · data contracts

481–500 Governance: OPA · license allowlist · export · residency · retention · model card · eval dataset · red team · jailbreak · permission board · access recert · MCP · plugin · marketplace · telemetry · consent · audit export · legal hold · break-glass · policy changelog

**Línea a línea 201–500 también:** CURSOR_300_MAS_PUNTOS + commit 6e8a91a2 historial.

---

# ANEXO X — X.1–X.7 (COPY 0cf4f6a1)

## X.1 Secuencia REAL
0 PolicySnapshot → 1 ContextManifest → 2 require_context BLOCK → 3 PreGate COPY-FIRST+Sheriff → 4 apply_adapt+ast → 5 quality → 6 goal_lock → 7 cognitive → 8 evidence_merge → 9 QualityDAG → 10 core/fc auto → 11 GapRegistry → 12 VerdictAuthority → 13 ClosureEngine → 14 DENY

## X.2 Matriz: ContextManifest/Sheriff/COPY-FIRST/Gap/Closure/QDAG/FC/Policy/Unified/main_12 = SÍ en code

## X.3–X.4 path_resolve · quality_handlers · fc/core_auto · evidence_merge · checklist_factory · programming_kwargs · run_unified · main_loop programming_path

## X.5 G2/G6 cerrados · G3/G7 parcial · G4/G5 doc-light

## X.6 TYPE/BUILD CI · FC subset caller

## X.7 CODE ahead §§2/5 · wire CLOSED · PASS ley intacta

Fuente: 0cf4f6a1 · _COPY_BLOB_0cf4f6a1_ARQUITECTURA_REAL.md

---

# ANEXO faa6 A+B+C — COPY desde _COPY_BLOB_faa6d95_ANEXOS_ABC.md (NO reescribir; leer + este bloque)

**Copia íntegra obligatoria mismo branch:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/_COPY_BLOB_faa6d95_ANEXOS_ABC.md  
**Fuente commit:** faa6d95d597b87349ee1f8f1e5a45924b08859b7

A1–A17: Global · Forensic REQUIRED · planos · CORE-01..14 · CONNECTIVITY · counters · RULES · 4-pass · evaluate · API · GapRegistry · catalog C-* · trace · QualityDAG · playbook · qué es/no es  
B1–B4: LIVE · PROGRAMMING · FORENSIC_MAP · listas 500+  
C1–C4: gaps mapa · paths canónicos · 04_3_MODOS F1/F2/F3 · cierre

# Pendiente: append H2 E001–E500 desde 0f19cb2 (mismo método COPY file + pegar final)
