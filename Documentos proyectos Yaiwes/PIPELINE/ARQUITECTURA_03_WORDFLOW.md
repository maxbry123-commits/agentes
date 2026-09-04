# ARQUITECTURA 03 — WORDFLOW PRODUCTO (code)

**Path:** `extensions/wordflow/`  
**Ficha:** `extensions/wordflow/ficha.v2.json`  
Esto es el motor de programación / ciclo. El kernel no sustituye esta carpeta.

---

## 1. Reception (el link que pediste)

Carpeta: https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/reception

| Archivo | Bytes | Rol |
|---------|-------|-----|
| `RECEPTION_agentes.md` | 818 | Inbox canónico repo agentes |
| `RECEPTION_TEMPLATE.md` | 794 | Plantilla otros repos |
| `KNOWLEDGE_RECEPTION_LINKS.md` | 1055 | Si se pierde el link, el agente lo regenera |
| `advanced_engineering_code_standard_guia_maestra.md` | 29630 | Guía maestra |
| `convert.py` | 1633 | T2–T2.3: normalize + sdpa/mcr stubs + max_context=20_000_000 |

Contrato de `convert(input_block)`:
- Input: dict con `raw_text` | `text` | `content`
- Output: `{ok, normalized{text,keys,source}, use_sdpa, branch, max_context, sdpa_stub, mcr_stub}`
- `run_mcr()` fuerza `branch=mcr`

**Qué NO hace todavía:** no mueve el .md a una fase, no escribe code en ruta exacta, no enchufa PLUGIN solo. Eso está descrito en el inbox; el code solo normaliza.

Motor 4: `extensions/wordflow/motors/kernel_ext/motor.py`  
`get_reception_link("agentes")` → blob RECEPTION_agentes.md  
`dispatch("reception_link"|"send"|"call"|"download")`

## 2. Flujo de un input (code que existe)

```
reception.convert / input_normalizer / input_compiler / input_quality_bar
        → goals_extractor → goals_compiler → goal_lock
        → mission + planner/mission_planner
        → task_classifier + task_queue + scheduler
        → programming_pipeline / code_path_runner
        → loop_bridge (Fake T14) ↔ maxbry_loop
        → evidence_packet + write_evidence + claim_validator
        → publish_path / github_publisher / github_deploy
```

Entry:
- `engine/entrypoint.py`
- `engine/entrypoint_v1.py`
- `engine/orchestrator.py` + `orchestrator_v1.py`
- `engine/main_loop.py` (9836 B)

## 3. Engine — grupos reales (archivos)

### 3.1 Input / goals / mission
`input_compiler.py` `input_normalizer.py` `input_quality_bar.py`  
`goals_extractor.py` `goals_compiler.py` `goal_lock.py`  
`mission.py` `objective_echo.py` `structured_questions.py`  
`workflow_dna.py` `dna_bundle.py` `dna_handoff.py` `handoff.py`

### 3.2 Programación / code path
`code_path_runner.py` (17742 B) `code_path_smoke.py`  
`programming_pipeline.py` `programming_kwargs.py`  
`dual_compiler.py` `skill_native_compiler.py`  
`codegen/dag.py`  
`build_plan_only.py` (T36 PLAN_ONLY HF)

### 3.3 Loop / runtime
`loop_bridge.py` (T14 Fake stages+evidence)  
`main_loop.py` `cognitive_loop.py` `cognitive_registers.py`  
`runtime_bus.py` `wave4_runtime.py` `wave5_runtime.py`  
`parallel_runtime.py` `parallel_runtime_guarded.py` `parallel_facade.py`  
`execution_facade.py` `execution_manifest.py`

### 3.4 Recursos / acquire
`resource_catalog.py` `resource_broker.py` `resource_gate.py`  
`resource_runtime.py` `resource_trace.py`  
`acquire_12.py` `analyze_12.py` `reuse_12.py` `fetch_planner.py`  
`hf_index.py` `hf_resolver.py` `environment_scan.py`

### 3.5 Evidencia / sheriff / repair
`evidence_packet.py` `evidence_bridge.py` `evidence_graph.py` `write_evidence.py`  
`claim_validator.py` (T30 claim≠evidence)  
`bitacora.py` `reasoning_ledger.py`  
`validator.py` `repair_gate.py` `refute_repair.py`  
`sentinel.py` `sheriff_adapter.py` `control_sheriff_bridge.py`  
`policy_engine.py` `kimi_policy.py` `enchufe_gate.py`

### 3.6 Estado / recuperación
`state_authority.py` `state_store.py` `checkpoint_store.py`  
`recovery.py` `watchdog.py` `circuit_breaker.py` `retry_policy.py`  
`lease_manager.py` `sandbox_manager.py`  
`state/blackboard.py` `state/ledger.py`

### 3.7 Publish / GitHub
`github_api.py` `github_publisher.py` `publish_path.py`  
`push_ping.py` `push_ping_hooks.py`  
`artifact_pin.py` `project_mirror.py` `list_connections.py`  
`credential_store.py` `docker_transport.py` `ssh_orchestrator.py` `remote_workers.py`

### 3.8 Expertos / consejo
`council.py` `expert_panel.py` `expert_router.py` `expert_decision.py`  
`role_analyzer.py` `capability_brain.py` `capability_intent.py` `capability_passport.py`  
`focus_monitor.py` `cursor_hooks.py`

### 3.9 Engine attach
`engine_abi.py` `engine_attach.py` `extension_registry.py`  
`contract_router.py` `microkernel_install.py`  
`engines/fake_engine.py`  
`ports/memory_port.py` `ports/planning_port.py`

## 4. Accounts + deploy (fuera del engine, mismos contratos)

Wordflow:
- `accounts/registry.py` `resolver.py` `require.py` (T38)

Deploy:
- `extensions/github_deploy/plan_push.py` (T32 force reject)
- `protected.py` (T33 HOLD)
- `token_ref.py` (T39) — nunca PAT en logs
- `deployer.py` `git_data_port.py`

## 5. Standards (calidad, no runtime hot)

`standards/copy_first.py` `adapt_imports.py` `sheriff.py` `checklist_sheriff.py`  
`forensic_core.py` `forensic_contract.py` `forensic_report.py`  
`rule_engine.py` `quality_dag.py` `wiring_graph.py` `dependency_graph.py`

## 6. Tests

`extensions/wordflow/tests/` — un test por módulo + waves 0–5 + v1_e2e.  
Prueban Fake / contratos. No equivalen a C100.
