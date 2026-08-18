# X-Ray seed STATUS real — S04 / T04
**Fecha:** 2026-08-18  
**Regla:** STATUS solo por **existencia en árbol GitHub** (list dir/file + size). No implica tests E2E ni claim C100 cerrado.  
**Estados:** IMPLEMENTED | PARTIAL | MISSING | PENDING | PLACEHOLDER | UNKNOWN

## Resumen por paquete

| ID | Path | Observación (lista GH) | STATUS seed |
|----|------|------------------------|-------------|
| WF.01 | extensions/wordflow/ | engine, standards, motors, reception, accounts, connectors, catalogs | IMPLEMENTED (paquete) |
| WF.02 / WF.00 | extensions/wordflow_kernel/ | bootstrap_v1, instance*, spawn, fail_closed, gateway/, engines/, tests/ | PARTIAL (multi-instancia formal T07–T12) |
| WF.05 | extensions/maxbry_loop/ | engine.py, model.py, gaps.py, tests/ | PARTIAL |
| WF.06 | extensions/audit_forensic/ | presente en árbol | PARTIAL |
| WF.07 | extensions/github_deploy/ | presente | PARTIAL |
| WF.08 | extensions/github_publisher/ | presente | PARTIAL |
| WF.09 | extensions/project_bootstrap/ | presente | PARTIAL |
| WF.10 | extensions/source_evolution/ | presente | PARTIAL |
| WF.11 | extensions/adapters/ | presente | PARTIAL |
| WF.12 | extensions/knowledge/ | presente | PARTIAL |

## extensions/wordflow/ (detalle árbol)

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

## Hot path programación (wordflow/engine) — seed

| Path | size≈ | STATUS seed |
|------|-------|-------------|
| code_path_runner.py | ~17KB | IMPLEMENTED (archivo; cableado formal = C100/T13+) |
| programming_pipeline.py | ~5.5KB | IMPLEMENTED (archivo) |
| goal_lock.py | ~4KB | IMPLEMENTED (archivo) |
| cognitive_loop.py | ~2.4KB | IMPLEMENTED (archivo) |
| evidence_packet.py | ~3KB | IMPLEMENTED (archivo) |
| main_loop.py | ~9KB | IMPLEMENTED (archivo) |
| list_connections.py | ~0.8KB | PARTIAL (stub T06) |
| publish_path.py | ~2KB | PARTIAL |

## extensions/wordflow_kernel/ (detalle)

| Path | Estado | Nota |
|------|--------|------|
| bootstrap_v1.py | IMPLEMENTED | Verify E2E = T13 |
| bootstrap_multi.py | PARTIAL | Existe; no claim N instancias producción |
| gateway/ | PARTIAL | intelligence + router_http |
| engines/ | PARTIAL | stubs hermes/openclaw + port |
| resources/ | PARTIAL | contract, loaders, factory |
| stages/ | PARTIAL | default_handlers, engine |
| bridge/ | PARTIAL | gap_bridge, goal_bridge |
| memory_slot/ | PARTIAL | adapter + contracts |
| router_slot/ | PARTIAL | adapter + contracts |
| ui_gateway/ | PARTIAL | plugin |
| tests/ | PARTIAL | varios test_v* |
| instance.py | PARTIAL | T07 |
| instance_store.py | PARTIAL | T08 |
| spawn.py | PARTIAL | T09 |
| ficha_loader.py | PARTIAL | T10 |
| fail_closed.py | PARTIAL | T12 |
| ficha.v2.json | IMPLEMENTED | |
| WordflowInstance registry formal API | PENDING | T07 criterio cierre |

## maxbry_loop — seed

| Path | STATUS seed |
|------|-------------|
| engine.py | PARTIAL |
| model.py | PARTIAL |
| gaps.py | PARTIAL |
| tests/ | PARTIAL |

## Qué NO afirma este seed
- No C100 100%  
- No tests Fake pasados en esta tarea  
- No IMPLEMENTED de runtime multi-instancia completo  
- T43 actualizará matriz post-code  

## Anclas
XRAY_SEED · T04 · NO_INVENT_IMPLEMENTED · extensions/wordflow/engine · wordflow_kernel · maxbry_loop
