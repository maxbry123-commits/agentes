# Evolution Engine v3 · AUDIT (100% del núcleo programado)

## Objetivo
Fuente externa → License → AST/Architecture → Authority → EVO-IR → Policy → Placement → Universal Plugin → Simulation → Capability Registry.

Kernel solo consume UniversalPlugin.invoke(capability, input).

## Módulos
| Path | Función |
|------|---------|
| acquisition/license_auditor.py | S27 licencia PASS/DIRECTOR/STOP |
| acquisition/source_store.py | sources/ + SOURCE_RECEIPT sha |
| analysis/ast_scanner.py | AST Python |
| analysis/architecture.py | ArchitectureMap + fingerprint |
| analysis/authority_graph.py | 5 authorities |
| evo_ir.py | IR única |
| planning/policy_engine.py | Policy DSL |
| planning/placement.py | Taxonomía extensions/ |
| plugin/universal_plugin.py | UCC + Plugin |
| simulation/engine.py | structural sim |
| registry/capability_registry.py | register/resolve/invoke |
| controller.py | evolve_path pipeline |
| recipes/*.yaml | code_agent + workflow |

## Test local
ok=True phase=REGISTERED plugin_id=absorbed.demo_code_agent
generate_code→cognitive/preserve · agent_loop→control/subordinate · run_git_diff→execution/adapt
