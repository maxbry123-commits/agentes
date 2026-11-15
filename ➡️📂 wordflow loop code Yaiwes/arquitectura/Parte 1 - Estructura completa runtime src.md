PARTE 1 - Estructura completa de runtime/src (17 carpetas, auditoria real)

agent/
- agent_router.py (2KB) - router debil, A DEPRECAR segun decision ya tomada

conn/
- huggingface_bridge.py (7.5KB), manager.py (2.2KB), rate_limit.py (2.2KB),
  secrets.py (2.1KB) - credenciales fuera del codigo, confirmado

core/ (30 archivos, el kernel real)
- kernel.py (13KB) - nucleo, handler+idempotency+state
- dag_engine.py (5.3KB) - dependencias, ciclos, orden topologico
- state_machine.py (5.4KB) - FSM
- event_bus.py (13.9KB) - InMemory/Redis/NATS
- parallel_scheduler.py (6.2KB)
- crazywall_claim_gate.py (5.7KB) - claim+lease
- crazy_wall_concurrency.py (1.8KB)
- llm_boundary.py (2.8KB) - LLM propone, nunca autoriza
- reuse_selector.py (6.1KB) - REUSE>PATCH>ADAPT>GENERATE
- completion_gate.py (4.5KB)
- structured_action_gate.py (4.8KB)
- unsafe_behavior_gate.py (4.4KB)
- wordflow_global_audit.py (12.2KB)
- component_intake.py (13.9KB) - el mas grande de intake
- existing_code_intake.py (8.3KB)
- project_intake_pipeline.py (7.2KB)
- placement_classifier.py (4.5KB)
- source_truth_reconciler.py (4KB) + truth_reconciler.py (1.4KB) - DUPLICADO SOSPECHOSO
- file_audit_contract.py (10.9KB)
- code_task_graph.py (3.9KB), code_graph_workspace.py (6.5KB)
- goals12.py (6.9KB) - los 12 goals que usamos en esta conversacion, YA EXISTE
- security_rewriter.py (2.8KB)
- task_skill_selector.py (4.4KB)
- run_launcher.py (4KB)
- continuity_supervisor.py (3.5KB)
- no_value_gap.py (3.8KB)
- fables_binding_gate.py (5.1KB) - cableado con Fables, confirmado
- canonical_motor_gate.py (3.4KB)
- code_generation_policy.py (3.2KB)
- auto_loop_builder.py (7.8KB)
- architecture_chat_bridge.py (2.7KB)
- agent_memory_loader.py (1.8KB)
- agent_source_copy_runner.py (8.1KB)
- goose_official_acquisition_runner.py (17.9KB) - el mas grande de core
- graph_visual_projection.py (6.1KB)
- graphiti_temporal_adapter.py (10.1KB)

governance/ (runtime/src, distinto del de wordflow_loop/wordflow_loop)
- merkle_governance_core.py (5.4KB) - ledger encadenado con hash

install/
- deployment_gate.py (2.4KB), deterministic_deployer.py (6.7KB),
  installation_engine.py (5KB)

mission/
- sharder.py (4.1KB)

observability/
- engine.py (2.1KB)

parallel/
- mavis_parallel.py (6.5KB)

preflight/
- engine.py (2.6KB)

recovery/
- checkpoint.py (2KB) - SI EXISTE, corrige mi hallazgo previo erroneo
- circuit_breaker_sla.py (5.5KB)
- classifier.py (1.75KB)
- engine.py (2.2KB) - el Recovery Engine
- reconciliation.py (1.4KB)

research/
- engine.py (2.2KB)

spec/
- healing_engine.py (6.4KB)

storage/
- artifact_router.py (2.8KB) - SOLO esto, sin checkpoint aqui (vive en recovery/)

tribunal/
- tribunal.py (3.9KB) - EL ORACULO REAL
- constitutional.py (1.6KB)
- cross_validator.py (1.45KB)
- hmac_manager.py (4.7KB)
- budget_gate.py (1.2KB)

uek/ (Enchufe Universal, hallazgo mayor)
- universal_plugin_bus_v2_integrated.py (30KB) - EL MAS GRANDE DE TODO EL KERNEL
- ficha_contract_v2.py (11.7KB)
- sandbox_manager.py (7.6KB)
- sbom_adapter_factory.py (4.8KB)
- uek_cluster.py (2.8KB)
- boot_engine.py (1.2KB)

TOTAL VERIFICADO: 17 carpetas, 60+ archivos Python, todos leidos con nombre
y tamano exacto, no de memoria.
