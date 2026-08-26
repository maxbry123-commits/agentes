# Paso 3 — Organización del código real dentro de YAIWES-OMEGA

**Fuente canónica del Director.** No inventar filas fuera de este documento.

## Hallazgo crítico antes del mapa

1. **`wordflow_kernel/gateway/intelligence.py`** (`make_request`) + `router_http.py` (`RouterHTTPGateway`) es el **stub central** que el propio catálogo marca como `intelligence_gateway: stub`, con adapters `Mock` y `RouterHTTP` únicamente. **Este es exactamente el punto donde entra `execution-engine-pool.adapter-layer`** con los motores reales (Claude Code, Codex, OpenHands, OpenCode, Aider, Cline). No hay que crear el punto de enchufe — ya existe, solo le faltan los adapters reales.

2. **`wordflow_kernel/engines/openclaw_stub.py` y `hermes_stub.py`** — son **literalmente** los stubs de Nivel 3 (agentes reales de paralelo/supervisión). No se crean desde cero: se llenan.

3. **La rama `programming-modular-v1`** (`p01_context_gate.py` … `12_return.py`) ya es un intento de dividir `code_path_runner.py` en stages separados — que es exactamente lo que pedimos para `code-programming-engine.code-path-execution`. El problema: `runner.py` **bridgea al legacy** en vez de orquestar p01→p12 él mismo. Es el prototipo del estado final, no algo que inventar — hay que **terminar de cablearlo**, no rehacerlo.

## Regla de módulos compartidos (lego: nada se duplica)

| Módulo | Vive en (única vez) | `code-programming-engine` lo usa vía |
|---|---|---|
| `goal_lock.py` | `execution-orchestration.goal-lock` | referencia/import, no copia |
| `cognitive_loop.py` | `execution-orchestration.mission-planning` | referencia |
| `evidence_packet.py` | `observability.evidence-packet` | referencia |

## Mapa — `extensions/wordflow/` (nivel superior)

| Origen real | Destino en yaiwes-omega | Acción |
|---|---|---|
| `component_catalog.json` + `connect_catalog.json` | `definition-registry.declared-dependency-catalog` | Mover intacto |
| `ficha.v2.json` / `manifest.yaml` | `kernel-principal.extension-kernel.capability-registry` | Mover intacto |
| `accounts/` (registry, require, resolver) | `deploy-publish.multi-account-registry` | Mover intacto |
| `codegen/dag.py` | `execution-orchestration.dag-executor` | Mover intacto |
| `connectors/` | `deploy-publish.push-injection` | Mover intacto |
| `context/builder.py` | `execution-orchestration.dependency-injection-context` | Mover intacto |
| `contracts/` (C_WF_INPUT, C_WF_LOOP) | `definition-registry.domain-specific-contracts` | Mover intacto |
| `docs_templates/` | `PIPELINE/` | Mover (documental) |
| `motors/` (call, download, send) | `code-programming-engine.external-motor-bridge` | Mover intacto |
| `motors/kernel_ext` | Puente `code-programming-engine` ↔ `kernel-principal` | Mover intacto |
| `planner/` | `execution-orchestration.mission-planning` | Mover intacto |
| `policies/engine_attach` | `kernel-principal.extension-kernel.abi-mount` | Mover intacto |
| `policies/sentinel` + `policies/sheriff` | `control-governance.sentinel` / `.sheriff-bridge` | Mover intacto |
| `reception/` | `input-layer.reception` | Mover intacto |
| `state/` (blackboard, ledger) | `state-events-durability.run-state-store` | Mover intacto |
| `store/main_12.yaml` | `definition-registry.workflow-definition` | Mover intacto |
| `store/goals`, `store/council` | `execution-orchestration` / `control-governance.council` | Mover intacto |
| `tests/` | Viaja con cada módulo | — |

## Mapa — `engine/` columna C-19

| Archivo | Destino | Nota |
|---|---|---|
| `code_path_runner.py` | `code-programming-engine.code-path-execution` | Target = p01→p12 wireado |
| `programming_pipeline.py` | `code-programming-engine.engine-modules` | Mover intacto |
| `programming_kwargs.py` | `code-programming-engine.engine-modules` | Mover intacto |
| `input_quality_bar.py` | `code-programming-engine.engine-modules` | Mover intacto |
| `skill_native_compiler.py` | `code-programming-engine.engine-modules` | Gap: stub determinista |
| `code_path_smoke.py` | `code-programming-engine.module-tests` | Mover intacto |
| `main_loop.py` | Split: S01–S12 → `multi-workflow-engine.shared-services.runner-host`; S08b → `programming-engine-binding` | Bisagra |

## Mapa — `engine/` resto

| Prefijo/nombre real | Destino |
|---|---|
| `acquire_12`, `analyze_12`, `reuse_12` | `extensions.source-evolution-module` |
| `artifact_pin`, `bitacora`, `checkpoint_store`, `state_*`, `workflow_dna`, `reasoning_ledger`, `dna_*` | `state-events-durability.run-state-store` |
| `bootstrap`, `microkernel_install`, `entrypoint*`, `engine_abi`, `engine_attach`, `extension_registry` | `kernel-principal.extension-kernel` |
| `build_plan_only`, `mission`, `objective_echo`, `planning_proposal`, `fetch_planner`, `goals_*` | `execution-orchestration.mission-planning` |
| `capability_*` | `kernel-principal.extension-kernel.capability-registry` / `.capability-passport` |
| `circuit_breaker`, `retry_policy`, `watchdog`, `lease_manager`, `resource_*` | `kernel-principal.resource-governance` |
| `claim_validator`, `evidence_*`, `write_evidence` | `observability.evidence-packet` |
| `contract_router`, `control_sheriff_bridge`, `sheriff_adapter`, `sentinel`, `council`, `refute_repair`, `repair_gate`, `validator`, `structured_questions` | `control-governance` |
| `credential_store` | `security-auth.secret-isolation` |
| `docker_transport`, `sandbox_manager`, `ssh_orchestrator`, `remote_workers` | `execution-orchestration.container-pod-isolation` |
| `dual_compiler` | `code-programming-engine.engine-modules` |
| `enchufe_gate` | `input-layer.reception` |
| `environment_scan` | `kernel-principal.resource-governance` |
| `execution_*` | `execution-orchestration` |
| `expert_*`, `role_analyzer` | `kernel-principal.reasoning-kernel.expert-panel-router` |
| `github_*`, `hf_*`, `publish_path`, `push_ping*`, `project_mirror` | `deploy-publish` |
| `handoff` | `agent-fleet-parallelism.agent-handoff` |
| `kimi_policy` | `execution-engine-pool.capability-matching` |
| `list_connections` | `definition-registry.declared-dependency-catalog` |
| `loop_bridge` (maxbry_loop) | `multi-workflow-engine.instances.programming-engine-binding` |
| `orchestrator*` | `execution-orchestration` |
| `parallel_*`, `wave4/5_runtime` | `agent-fleet-parallelism` |
| `policy_engine` | `control-governance.policy-engine` |
| `ports/` | `execution-engine-pool.adapter-layer` |
| `runtime_bus` | `kernel-principal.internal-bus` |
| `scheduler`, `task_*` | `execution-orchestration.task-classifier-scheduler` |
| `supervisor` | `agent-fleet-parallelism.dispatch-lifecycle` |
| `version_selector` | `extensions.source-evolution-module` |
| `engines/fake_engine.py` | `execution-engine-pool` — FAKE explícito |

## Mapa — `standards/`

| Archivo | Destino |
|---|---|
| `executor_gates.py` | `control-governance.pre-post-gates` |
| `verdict_authority.py` | `control-governance.verdict-authority` |
| `forensic_core.py` + `forensic_contract.py` | `control-governance.forensic-core` |
| `closure_engine.py` | `control-governance.closure-engine` |
| `quality_dag.py` + `quality_handlers.py` | `control-governance.quality-dag` |
| `gap_registry.py` | `control-governance` (con gap_tasks) |
| `copy_first.py` + `adapt_imports.py` | `control-governance` |
| `checklist_factory.py` + `checklist_sheriff.py` | `control-governance.sheriff-bridge` |
| `core_auto_measure.py` + `fc_auto_measure.py` | `control-governance.forensic-core` |
| `context_manifest.py` | `control-governance` |
| `symbol_index.py` | `control-governance.symbol-index-wiring-graph` |
| `programming_points_catalog.py` | `control-governance` |
| resto utilidades | `control-governance` |

## Mapa — `schemas/` (32)

- Los **32** → `definition-registry.schema-contracts`
- `code_output.schema.json` y `goal_lock.schema.json` → además referenciados por `code-programming-engine.schema-contracts-io` (no copiados)
- Gaps stage C-19 → `code-programming-engine.schema-contracts-io` cuando se generen

## Mapa — `wordflow_kernel/` completo

| Archivo/carpeta | Destino |
|---|---|
| `workflow.py` | `kernel-principal` |
| `instance.py`, `instance_store.py` | `multi-workflow-engine.shared-services` |
| `bootstrap_fake/multi/v1.py` | `kernel-principal.extension-kernel` |
| `checkpoint.py` | `state-events-durability.checkpoint-recovery` |
| `context_pack.py` | `execution-orchestration.dependency-injection-context` |
| `fail_closed.py`, `llm_control.py` | `control-governance.llm-control-deny` |
| `ficha_loader.py`, `engine_registry.py` | `kernel-principal.extension-kernel.abi-mount` / `.capability-registry` |
| `forensic.py`, `forensic_api.py`, `gap_tasks.py` | `control-governance.forensic-core` |
| `knowledge_index.py` | `tools-models-memory-knowledge.knowledge-retrieval-rag` |
| `ledger.py` | `state-events-durability.run-state-store` |
| `memory.py` | `tools-models-memory-knowledge.memory-microservices` |
| `preflight.py`, `validator.py` | `control-governance.workflow-validation` |
| `repo_truth.py` | `codebase-intelligence.codebase-graph` |
| `runtime.py`, `spawn.py` | `kernel-principal` / `agent-fleet-parallelism.dispatch-lifecycle` |
| `trace.py` | `observability.trace-history` |
| `bridge/gap_bridge.py`, `goal_bridge.py` | `execution-orchestration` |
| `engines/hermes_stub.py`, `openclaw_stub.py`, `port.py` | `execution-engine-pool.auxiliary-role-agents` |
| `gateway/intelligence.py`, `router_http.py` | `execution-engine-pool.adapter-layer` |
| `memory_slot/` | `tools-models-memory-knowledge.memory-microservices` |
| `reception/convert.py`, `git_apply.py` | `input-layer.reception` / `deploy-publish.push-injection` |
| `resources/*` | `kernel-principal.resource-governance.resource-broker-gate` |
| `router_slot/*` | `kernel-principal` |
| `slots/kimi_minimax.ficha.v2.json`, `placeholder.py` | `execution-engine-pool` — PLACEHOLDER fusion:false |
| `stages/*` | `kernel-principal` |
| `ui_gateway/*` | Fuera (DOC-UI00) |

## Gaps explícitos

| Gap | Destino |
|---|---|
| Export `SYMBOL_INDEX_PROGRAMMING.md` | `control-governance.symbol-index-wiring-graph` |
| Schemas por stage C-19 | `code-programming-engine.schema-contracts-io` |
| Índice test→asserts | `code-programming-engine.module-tests` |
| Log CI real | `observability.trace-history` |
| p01→p12 wireado end-to-end | `code-programming-engine.code-path-execution` |
| Adapters reales intelligence_gateway | `execution-engine-pool.adapter-layer` |
| Contenido real openclaw/hermes stubs | `execution-engine-pool.auxiliary-role-agents` |

## Regla de intocable

El monolito en `main` (`code_path_runner.py`) sigue siendo la única fuente operativa real hoy. Organiza/mueve carpetas y referencias primero; no apagues ni reemplaces el hot path monolítico hasta que `code-path-execution` pase los mismos tests con el mismo resultado.
