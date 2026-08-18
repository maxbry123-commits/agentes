# X-Ray seed STATUS real — S04 / T04
**Fecha:** 2026-08-17
**Fuente:** árbol GitHub real (get_repository_tree)

## extensions/wordflow/
| Path | Estado | Nota |
|------|--------|------|
| engine/ (main_loop, goal_lock, accounts, …) | IMPLEMENTED | code_path materializado |
| accounts/ | IMPLEMENTED | registry + resolver |
| connectors/ | IMPLEMENTED | github_external |
| docs_templates/ | IMPLEMENTED | generador + plantillas |
| motors/ | IMPLEMENTED | T0 send/call/download/kernel_ext |
| reception/ | IMPLEMENTED | T0 + knowledge |
| schemas/ | IMPLEMENTED | múltiples .schema.json |
| state/ | PARTIAL | blackboard + ledger |
| store/ | PARTIAL | goals, council, techniques |
| tests/ | IMPLEMENTED | suite amplia |
| ficha.v2.json | IMPLEMENTED | |
| manifest.yaml | IMPLEMENTED | |
| component_catalog.json | IMPLEMENTED | |

## extensions/wordflow_kernel/
| Path | Estado | Nota |
|------|--------|------|
| bootstrap_v1.py | IMPLEMENTED | |
| gateway/ | PARTIAL | intelligence + router_http |
| engines/ | PARTIAL | stubs hermes/openclaw + port |
| resources/ | PARTIAL | contract, loaders, factory |
| stages/ | PARTIAL | default_handlers, engine |
| bridge/ | PARTIAL | gap_bridge, goal_bridge |
| memory_slot/ | PARTIAL | adapter + contracts |
| router_slot/ | PARTIAL | adapter + contracts |
| ui_gateway/ | PARTIAL | plugin |
| tests/ | PARTIAL | varios test_v* |
| ficha.v2.json | IMPLEMENTED | |

## Resumen
- IMPLEMENTED: majority of wordflow/ engine + accounts + motors + reception + schemas
- PARTIAL: wordflow_kernel runtime pieces (stubs, no full multi-instance yet)
- MISSING formal: WordflowInstance registry (T07), HTML mapas (T41/T42)
