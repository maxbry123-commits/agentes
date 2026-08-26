# ORIGIN_MAP — contrato S3 (Paso 3 del Director)

**Fuente:** `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`  
**Regla:** cada fila = origen → destino → acción. Sin filas inventadas.

## Hallazgos ancla

| Origen | Destino | Acción |
|--------|---------|--------|
| wordflow_kernel/gateway/intelligence.py + router_http.py | execution-engine-pool/adapter-layer | ORGANIZAR + LLENAR adapters |
| engines/openclaw_stub.py, hermes_stub.py, port.py | execution-engine-pool/auxiliary-role-agents | LLENAR |
| code_path_runner.py / programming-modular-v1 | code-programming-engine/code-path-execution | CABLEAR p01→p12 |
| goal_lock.py | execution-orchestration/goal-lock | REF única (lego) |
| cognitive_loop.py | execution-orchestration/mission-planning | REF única (lego) |
| evidence_packet.py | observability/evidence-packet | REF única (lego) |

## Top-level extensions/wordflow

| Origen | Destino | Acción |
|--------|---------|--------|
| component_catalog.json + connect_catalog.json | definition-registry/declared-dependency-catalog | MOVER_INTACTO |
| ficha.v2.json / manifest.yaml | kernel-principal/extension-kernel/capability-registry | MOVER_INTACTO |
| accounts/ | deploy-publish/multi-account-registry | MOVER_INTACTO |
| codegen/dag.py | execution-orchestration/dag-executor | MOVER_INTACTO |
| connectors/ | deploy-publish/push-injection | MOVER_INTACTO |
| context/builder.py | execution-orchestration/dependency-injection-context | MOVER_INTACTO |
| contracts/ | definition-registry/domain-specific-contracts | MOVER_INTACTO |
| docs_templates/ | PIPELINE/ | MOVER_DOC |
| motors/ (call, download, send) | code-programming-engine/external-motor-bridge | MOVER_INTACTO |
| motors/kernel_ext | puente code-programming-engine ↔ kernel-principal | MOVER_INTACTO |
| planner/ | execution-orchestration/mission-planning | MOVER_INTACTO |
| policies/engine_attach | kernel-principal/extension-kernel/abi-mount | MOVER_INTACTO |
| policies/sentinel + sheriff | control-governance/sentinel + sheriff-bridge | MOVER_INTACTO |
| reception/ | input-layer/reception | MOVER_INTACTO |
| state/ | state-events-durability/run-state-store | MOVER_INTACTO |
| store/main_12.yaml | definition-registry/workflow-definition | MOVER_INTACTO |
| store/goals, store/council | execution-orchestration / control-governance/council | MOVER_INTACTO |
| tests/ | viaja con cada módulo | — |

## engine/ C-19

| Origen | Destino | Acción |
|--------|---------|--------|
| code_path_runner.py | code-programming-engine/code-path-execution | CABLEAR |
| programming_pipeline.py | code-programming-engine/engine-modules | MOVER_INTACTO |
| programming_kwargs.py | code-programming-engine/engine-modules | MOVER_INTACTO |
| input_quality_bar.py | code-programming-engine/engine-modules | MOVER_INTACTO |
| skill_native_compiler.py | code-programming-engine/engine-modules | MOVER_INTACTO (gap stub) |
| code_path_smoke.py | code-programming-engine/module-tests | MOVER_INTACTO |
| main_loop.py | runner-host + programming-engine-binding | SPLIT |

## engine/ resto (prefijos)

| Origen | Destino | Acción |
|--------|---------|--------|
| acquire_12, analyze_12, reuse_12 | extensions/source-evolution-module | MOVER_INTACTO |
| artifact_pin, bitacora, checkpoint_store, state_*, workflow_dna, reasoning_ledger, dna_* | state-events-durability/run-state-store | MOVER_INTACTO |
| bootstrap, microkernel_install, entrypoint*, engine_abi, engine_attach, extension_registry | kernel-principal/extension-kernel | MOVER_INTACTO |
| build_plan_only, mission, objective_echo, planning_proposal, fetch_planner, goals_* | execution-orchestration/mission-planning | MOVER_INTACTO |
| capability_* | capability-registry / capability-passport | MOVER_INTACTO |
| circuit_breaker, retry_policy, watchdog, lease_manager, resource_* | kernel-principal/resource-governance | MOVER_INTACTO |
| claim_validator, evidence_*, write_evidence | observability/evidence-packet | MOVER_INTACTO |
| contract_router, sheriff_*, sentinel, council, refute_repair, repair_gate, validator, structured_questions | control-governance | MOVER_INTACTO |
| credential_store | security-auth/secret-isolation | MOVER_INTACTO |
| docker_transport, sandbox_manager, ssh_orchestrator, remote_workers | execution-orchestration/container-pod-isolation | MOVER_INTACTO |
| dual_compiler | code-programming-engine/engine-modules | MOVER_INTACTO |
| enchufe_gate | input-layer/reception | MOVER_INTACTO |
| environment_scan | resource-governance | MOVER_INTACTO |
| execution_* | execution-orchestration | MOVER_INTACTO |
| expert_*, role_analyzer | reasoning-kernel/expert-panel-router | MOVER_INTACTO |
| github_*, hf_*, publish_path, push_ping*, project_mirror | deploy-publish | MOVER_INTACTO |
| handoff | agent-fleet-parallelism | MOVER_INTACTO |
| kimi_policy | execution-engine-pool/capability-matching | MOVER_INTACTO |
| list_connections | declared-dependency-catalog | MOVER_INTACTO |
| loop_bridge | programming-engine-binding | MOVER_INTACTO |
| orchestrator* | execution-orchestration | MOVER_INTACTO |
| parallel_*, wave4/5_runtime | agent-fleet-parallelism | MOVER_INTACTO |
| policy_engine | control-governance/policy-engine | MOVER_INTACTO |
| ports/ | execution-engine-pool/adapter-layer | MOVER_INTACTO |
| runtime_bus | kernel-principal/internal-bus | MOVER_INTACTO |
| scheduler, task_* | task-classifier-scheduler | MOVER_INTACTO |
| supervisor | agent-fleet-parallelism | MOVER_INTACTO |
| version_selector | source-evolution-module | MOVER_INTACTO |
| engines/fake_engine.py | execution-engine-pool | FAKE |

## standards/

| Origen | Destino | Acción |
|--------|---------|--------|
| executor_gates.py | control-governance/pre-post-gates | MOVER_INTACTO |
| verdict_authority.py | control-governance/verdict-authority | MOVER_INTACTO |
| forensic_core.py, forensic_contract.py | control-governance/forensic-core | MOVER_INTACTO |
| closure_engine.py | control-governance/closure-engine | MOVER_INTACTO |
| quality_dag.py, quality_handlers.py | control-governance/quality-dag | MOVER_INTACTO |
| gap_registry.py | control-governance | MOVER_INTACTO |
| copy_first.py, adapt_imports.py | control-governance | MOVER_INTACTO |
| checklist_* | control-governance/sheriff-bridge | MOVER_INTACTO |
| core_auto_measure, fc_auto_measure | control-governance/forensic-core | MOVER_INTACTO |
| context_manifest.py | control-governance | MOVER_INTACTO |
| symbol_index.py | control-governance/symbol-index-wiring-graph | MOVER_INTACTO |
| programming_points_catalog.py + resto | control-governance | MOVER_INTACTO |

## schemas/

| Origen | Destino | Acción |
|--------|---------|--------|
| 32 schemas | definition-registry/schema-contracts | MOVER_INTACTO |
| code_output + goal_lock schemas | + REF en schema-contracts-io | REF (no copiar) |
| gaps stage C-19 | code-programming-engine/schema-contracts-io | CREAR cuando existan |

## wordflow_kernel/

| Origen | Destino | Acción |
|--------|---------|--------|
| workflow.py | kernel-principal | MOVER_INTACTO |
| instance.py, instance_store.py | multi-workflow-engine/shared-services | MOVER_INTACTO |
| bootstrap_* | kernel-principal/extension-kernel | MOVER_INTACTO |
| checkpoint.py | state-events-durability/checkpoint-recovery | MOVER_INTACTO |
| context_pack.py | dependency-injection-context | MOVER_INTACTO |
| fail_closed.py, llm_control.py | control-governance/llm-control-deny | MOVER_INTACTO |
| ficha_loader, engine_registry | abi-mount / capability-registry | MOVER_INTACTO |
| forensic*, gap_tasks | control-governance/forensic-core | MOVER_INTACTO |
| knowledge_index.py | knowledge-retrieval-rag | MOVER_INTACTO |
| ledger.py | run-state-store | MOVER_INTACTO |
| memory.py, memory_slot/ | memory-microservices | MOVER_INTACTO |
| preflight, validator | workflow-validation | MOVER_INTACTO |
| repo_truth.py | codebase-intelligence/codebase-graph | MOVER_INTACTO |
| runtime.py, spawn.py | kernel-principal / agent-fleet | MOVER_INTACTO |
| trace.py | observability/trace-history | MOVER_INTACTO |
| bridge/* | execution-orchestration | MOVER_INTACTO |
| gateway/* | execution-engine-pool/adapter-layer | ORGANIZAR |
| engines/openclaw, hermes, port | auxiliary-role-agents | LLENAR |
| reception/* | input-layer / deploy-publish | MOVER_INTACTO |
| resources/* | resource-broker-gate | MOVER_INTACTO |
| router_slot/*, stages/* | kernel-principal | MOVER_INTACTO |
| slots/kimi + placeholder | execution-engine-pool | PLACEHOLDER |
| ui_gateway/* | fuera DOC-UI00 | EXCLUIDO |

## Gaps (S10)

| Gap | Destino |
|-----|--------|
| SYMBOL_INDEX_PROGRAMMING.md | symbol-index-wiring-graph |
| schemas stage C-19 | schema-contracts-io |
| test→asserts index | module-tests |
| log CI real | trace-history |
| p01→p12 E2E | code-path-execution |
| adapters reales | adapter-layer |
| contenido openclaw/hermes | auxiliary-role-agents |

**S3 status: PASS** — filas = documento Director en repo.
