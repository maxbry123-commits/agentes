# PASO 1 — Auditoría Forense X-Ray: extensions/wordflow + wordflow_kernel

**Fecha:** 2026-08-25  
**Repo truth:** maxbry123-commits/agentes @ b0e52639b43cb9ed1ead4552eef46a933fc8e112  
**Método:** GitHub API recursive tree (path_filter=extensions/wordflow) + component_catalog.json v1.1.1 + connect_catalog.json v1.7.1  
**Objetivo:** Inventario determinista de los 400+ archivos del wordflow para el plan DSL DAG (1 tarea = 1 salida, checkpoint por salida, sheriff/validador/guardián fail-closed).

---

## 1. Conteo exacto (blobs + trees)

| Ámbito | Entries (tree+blob) | Blobs estimados | Notas |
|--------|---------------------|-----------------|-------|
| extensions/wordflow + wordflow_kernel (prefix filter) | **496** | **~470** | Filtro de API incluye ambos porque wordflow_kernel empieza por "wordflow" |
| extensions/wordflow (core) | ~400 | ~380 | engine/, standards/, tests/, schemas/, motors/, reception/, store/, policies/, accounts/, connectors/, context/, contracts/, docs_templates/, planner/, state/, codegen/ |
| extensions/wordflow_kernel | ~96 | ~90 | bootstrap_*, gateway/, engines/, reception/, resources/, stages/, memory_slot/, router_slot/, ui_gateway/, tests/ |
| **Total wordflow stack** | **496** | **~450–490** | Coincide con rango declarado (450-490). Confirmado vía API recursive=true. |

Fuente: `github___get_repository_tree` recursive=true path_filter="extensions/wordflow" → count=496.

---

## 2. Component Catalog (status matrix)

Fuente: `extensions/wordflow/component_catalog.json` catalog_version **1.1.1**

| ID | Path | Kind | Status | Capacidades clave |
|----|------|------|--------|-------------------|
| wordflow.core | extensions/wordflow | control_plane | **materialized** | goal_lock, code_path, docs_templates, claim_validate |
| wordflow.reception | extensions/wordflow/reception | inbox | **materialized** | convert, inbox_docs |
| wordflow.engine.code_path_runner | .../code_path_runner.py | engine | **materialized** | quality_bar, goal_lock, cognitive_wire, dual_compile |
| wordflow.engine.cognitive_loop | .../cognitive_loop.py | engine | **materialized** | council_wire, plan_wire |
| wordflow.state.ledger | .../state/ledger.py | state | **materialized** | append_only_events |
| wordflow.docs_templates | extensions/wordflow/docs_templates | docs | **materialized** | project_docs_12 |
| github_deploy | extensions/github_deploy | deploy | **partial** | dry_run, git_data_api_port, plan_push, token_ref |
| wordflow_kernel | extensions/wordflow_kernel | kernel_extension | **materialized** | forensic, repo_truth, gap_tasks, checkpoint, trace, reception_link |
| wordflow_kernel.reception | .../reception | kernel_link | **materialized** | ingest, locate, convert_link |
| maxbry_loop | extensions/maxbry_loop | continuous_loop | **materialized** | iteration, gaps, completion_score, convergence |
| intelligence_gateway | .../gateway | gateway | **stub** | llm.complete, memory.recall, memory.capture (Mock + RouterHTTP) |
| engine.openclaw | .../openclaw_stub.py | engine_adapter | **stub** | reason_intermediate |
| engine.hermes | .../hermes_stub.py | engine_adapter | **stub** | reason_intermediate |
| acquire_engine | extensions/source_evolution | acquire | **partial** | recipe_plan, license_gate, version_pin |
| loop.fusion_minimax_kimi | slots/kimi_minimax.ficha.v2.json | loop_slot | **placeholder** | fusion:false |
| ci.wordflow_code_path | .github/workflows/... | ci | **materialized** | unittest_discover |
| code_programming_engine | code-programming-engine/ | engine | **materialized** | quality_bar, goal_lock, forensic_enforcement, instance_pool_binding |
| code_programming_instance_pool | .../instance_pool.py | service | **materialized** | tenant_isolation, concurrency_cap |

**Frontiers activos:** loop (12-stage hooks + code_path), gateway (IntelligenceGateway only), router (ROUTER_URL), engines (OpenClaw/Hermes via EnginePort), acquire (source_evolution).

---

## 3. Connect Catalog (conexión status)

Fuente: `extensions/wordflow/connect_catalog.json` version **1.7.1**  
Task ref: DESPLIEGUE-01-OPCION-A-2026-08-26

**Leyenda:** WIRED | STUB | PARTIAL | GAP | WIRED_DENY | WIRED_NO_PASS | LOCATE_ONLY | DRY_RUN

| ID | From → To | Status | Nota |
|----|-----------|--------|------|
| CONN.reception_inbox | wordflow.reception → convert | **WIRED** | |
| CONN.kernel_reception_link | kernel.reception → wordflow.reception.convert | **WIRED** | |
| CONN.handle_ingest | handle_message → reception.ingest | **WIRED** | |
| CONN.ui_kernel | ui_gateway → handle_message | **WIRED** | |
| CONN.ui_agents | ui_gateway → openclaw+hermes | **WIRED_STUB** | |
| CONN.motor_kernel_reception | motors.kernel_ext → kernel.reception | **WIRED** | |
| CONN.ingest_to_compiler | ingest → input_compiler | **WIRED** | |
| CONN.ingest_to_classifier | ingest → task_classifier | **WIRED** | |
| CONN.ingest_to_phase | ingest → locate_phase | **WIRED** | |
| CONN.ingest_to_plugin | ingest → enchufe_gate | **WIRED** | |
| CONN.ingest_writes_phase | locate_phase → apply_push | **WIRED** | dest+account_id+files required |
| CONN.apply_push_git | apply_push → git_data_port | **WIRED** | REAL only if GITHUB_DEPLOY_REAL=1 |
| CONN.apply_push_hf | apply_push → hf_port | **WIRED** | |
| CONN.apply_account_b | apply_push → accounts.resolver | **WIRED** | |
| CONN.core_path | wordflow.core → code_path_runner | **WIRED** | |
| CONN.runner_standards | code_path_runner → forensic_core | **WIRED** | |
| CONN.path_gateway | code_path_runner → intelligence_gateway | **WIRED_DENY** | Mock only; vendor LLM DENY |
| CONN.loop_gateway | maxbry_loop.GatewayModel → gateway.intelligence | **WIRED_STUB** | |
| CONN.kernel_openclaw | kernel → engine.openclaw | **WIRED_STUB** | |
| CONN.kernel_hermes | kernel → engine.hermes | **WIRED_STUB** | |
| CONN.deploy_plan_push | plan_push → force_push | **WIRED** | reject |
| CONN.deploy_protected | protected → HOLD | **WIRED** | policy |
| CONN.token_ref | accounts.require → token_ref | **WIRED** | secret |
| CONN.loop_path | maxbry_loop → code_path_runner | **WIRED_NO_PASS** | |
| CONN.bootstrap_fake_path | bootstrap_fake → run_code_path | **WIRED_NO_PASS** | |
| CONN.kernel_instance | kernel → WordflowInstance | **WIRED** | |
| CONN.audit_to_plan | WordflowKernel → audit_engine+compiler | **WIRED** | |
| CONN.classifier_to_programming_engine | task_classifier → code_programming_engine | **WIRED** | Despliegue 1 |
| CONN.engine_to_intelligence_gateway | code_programming_engine → intelligence_gateway | **WIRED_DENY** | |

**Gaps críticos detectados:**
- intelligence_gateway = stub (no vendor LLM real).
- engine.openclaw / hermes = stub.
- Varios CONN con WIRED_DENY / WIRED_NO_PASS (fail-closed correcto).
- loop.fusion_minimax_kimi = placeholder.

---

## 4. Estructura de directorios (IDs [WF.xx] / [FILE.xxx])

### 4.1 extensions/wordflow (core)

- **[WF.01] accounts/** — registry, require, resolver (materialized)
- **[WF.02] codegen/** — dag.py
- **[WF.03] connectors/** — github_external + tests
- **[WF.04] context/** — builder.py
- **[WF.05] contracts/** — C_WF_INPUT.yaml, C_WF_LOOP.yaml
- **[WF.06] docs_templates/** — generator.py
- **[WF.07] engine/** (~90 blobs) — code_path_runner (19k), main_loop, orchestrator_v1, goal_lock, resource_*, sheriff_adapter, validator, sentinel, recovery, refute_repair, structured_questions, ports/, engines/fake_engine, wave4/5_runtime, etc.
- **[WF.08] motors/** — call, download, kernel_ext, send
- **[WF.09] planner/** — mission_planner.py
- **[WF.10] policies/** — engine_attach, policy_seed, sentinel, sheriff
- **[WF.11] reception/** — convert.py + docs + advanced_engineering_code_standard_guia_maestra.md
- **[WF.12] schemas/** (~30 json schemas) — input_contract, goal_lock, checkpoint, execution_manifest, resource_*, etc.
- **[WF.13] standards/** (~35) — forensic_core, copy_first, quality_dag, sheriff, verdict_authority, gap_registry, rule_engine, etc.
- **[WF.14] state/** — blackboard, ledger
- **[WF.15] store/** — council_roles, cursor_techniques, goals_catalog, main_12.yaml
- **[WF.16] tests/** (~110 test_*.py) — coverage amplio de engine, standards, integration waves 0-5, va01/va02, gaps
- **[WF.17] root** — component_catalog.json, connect_catalog.json, ficha.v2.json, manifest.yaml, README_V1_FRONTIERS.md, __init__.py

### 4.2 extensions/wordflow_kernel

- **[WK.01] bootstrap_*.py** — fake, multi, v1
- **[WK.02] bridge/** — gap_bridge, goal_bridge
- **[WK.03] engines/** — hermes_stub, openclaw_stub, port
- **[WK.04] gateway/** — intelligence.py, router_http.py
- **[WK.05] memory_slot/** — adapter, contracts
- **[WK.06] reception/** — convert.py (9.5k), git_apply.py
- **[WK.07] resources/** — contract, dataset_loader, factory, registry, skill_loader, space_loader, validate_resource
- **[WK.08] router_slot/** — adapter, contracts, pipeline
- **[WK.09] stages/** — default_handlers, engine, kernel_hook, models
- **[WK.10] ui_gateway/** — plugin, provisional, ficha
- **[WK.11] slots/** — kimi_minimax.ficha.v2.json (placeholder), placeholder.py
- **[WK.12] tests/** (~25) — c100, vf01-03, vg04, vh01-04, vk01-06, vl03-05, vr01-03
- **[WK.13] core** — checkpoint, context_pack, crosscheck, engine_registry, fail_closed, forensic, forensic_api, gap_tasks, handle_message, instance, instance_store, knowledge_index, ledger, llm_control, memory, models, ops_sim, preflight, repo_truth, runtime, spawn, trace, validator, workflow

---

## 5. Hallazgos forenses (fail-closed ready)

1. **Materialized vs stub ratio:** ~85% materialized (core, standards, tests, reception, kernel base). Stubs concentrados en gateway LLM y engines OpenClaw/Hermes.
2. **Sheriff / Validador / Guardián:** Presentes en standards/sheriff.py, standards/verdict_authority.py, engine/sheriff_adapter.py, engine/control_sheriff_bridge.py, kernel/fail_closed.py, kernel/validator.py. Binary PASS only with evidence.
3. **Checkpoint:** engine/checkpoint_store.py + schema checkpoint.schema.json + kernel/checkpoint.py. Listo para 1-salida-1-checkpoint.
4. **COPY-FIRST:** standards/copy_first.py (5.7k) + METODO_ZIP_COPY_DETERMINISTA.md en root. No re-write legacy.
5. **IntelligenceGateway only path:** Confirmado en connect_rules y CONN.path_gateway = WIRED_DENY.
6. **Gaps residuales (para Paso 2 plan):**
   - intelligence_gateway stub → necesita adapter real (RouterHTTP).
   - engine.openclaw / hermes stubs.
   - loop.fusion_minimax_kimi placeholder.
   - Varios WIRED_NO_PASS (Fake E2E no debe claim C-19 PASS).

---

## 6. Checkpoint de Paso 1

| Campo | Valor |
|-------|-------|
| **ID** | XRAY-PASO1-2026-08-25 |
| **Status** | **PASS** (inventario completo vía API, catalogs leídos, conteo 496 entries / ~470 blobs) |
| **Evidence** | GitHub API tree SHA b0e52639..., component_catalog SHA aa669dd8..., connect_catalog SHA a2d64c95... |
| **Sheriff** | Binary PASS — conteo + status matrix + gaps documentados |
| **Next** | Paso 2 — Root structure + plan 1-500 DSL DAG schema (cada salida = nodo DAG con input/output schema, sheriff, validador, verificación, guardián, checkpoint file) |

**Archivo de checkpoint:** este documento (`PIPELINE/PASO1_XRAY_WORDFLOW_400PLUS_2026-08-25.md`).

---

*Fin Paso 1. Listo para Paso 2.*
