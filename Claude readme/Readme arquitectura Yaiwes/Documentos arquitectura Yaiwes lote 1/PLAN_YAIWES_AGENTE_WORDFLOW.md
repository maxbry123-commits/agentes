# README PLAN YAIWES v1

**Nombre oficial:** README PLAN YAIWES v1  
**Fuentes (únicas):**
1. Estructura raíz: `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md` + README canónico
2. Organización del código real: **Paso 3 — Mapa origen → destino** (documento del Director)

**Repo:** maxbry123-commits/agentes · main  
**Agente:** Yaiwes v1  
**GitHub = truth.** 1 tarea = 1 salida. Binary PASS only with evidence. Fail-closed.

---

## 0. BLOQUE DE PROTECCIÓN

```text
PROHIBIDO:
- Inventar otro plan paralelo.
- Reescribir hot path monolítico (code_path_runner en main) sin paridad de tests.
- Duplicar módulos compartidos (regla lego).
- PASS sin checkpoint nuevo + evidencia.

OBLIGATORIO:
- Seguir el mapa Paso 3 (origen → destino).
- Materializar primero la estructura raíz (PLAN_100).
- Monolito en main sigue operativo hasta que code-path-execution pase los mismos tests.
```

---

## HALLAZGOS CRÍTICOS (Paso 3 — no negociables)

1. **`wordflow_kernel/gateway/intelligence.py` + `router_http.py`** = punto de enchufe real.  
   Destino: `execution-engine-pool.adapter-layer`.  
   No crear enchufe nuevo: ya existe; faltan adapters reales (Claude Code, Codex, OpenHands, OpenCode, Aider, Cline).

2. **`openclaw_stub.py` + `hermes_stub.py`** = Nivel 3 (agentes paralelo/supervisión).  
   Destino: `execution-engine-pool.auxiliary-role-agents`.  
   No crear desde cero: **llenar**.

3. **Rama `programming-modular-v1` (p01…p12)** = prototipo de `code-path-execution`.  
   Hoy `runner` bridgea al legacy. Hay que **terminar de cablear** p01→p12, no rehacer.

4. **Regla lego (una sola vez):**

| Módulo | Vive una sola vez en | code-programming-engine |
|--------|----------------------|-------------------------|
| `goal_lock.py` | `execution-orchestration.goal-lock` | referencia/import, **no copia** |
| `cognitive_loop.py` | `execution-orchestration.mission-planning` | referencia |
| `evidence_packet.py` | `observability.evidence-packet` | referencia |

5. **Intocable hasta paridad:** monolito `code_path_runner.py` en main sigue siendo la fuente operativa. No apagar hasta que la versión dividida pase `test_code_path_runner.py`, `test_unified_programming.py`, etc.

---

## TOTAL DE SALIDAS

# **TOTAL DE SALIDAS = 12**

Orden de ejecución obligatorio:

| Orden | ID | Nombre |
|-------|-----|--------|
| 1º | **S1** | Estructura raíz completa (árbol PLAN_100) |
| 2º | **S2** | DESPLIEGUE 1 |
| 3º | **S3** | ORIGIN_MAP + COPY_MANIFEST (contrato del mapa Paso 3) |
| 4º | **S4** | Organizar `extensions/wordflow/` top-level → destinos |
| 5º | **S5** | Organizar `engine/` C-19 (hot path programación) |
| 6º | **S6** | Organizar `engine/` resto (~70 módulos por función) |
| 7º | **S7** | Organizar `standards/` → control-governance |
| 8º | **S8** | Organizar `schemas/` → definition-registry (+ refs C-19) |
| 9º | **S9** | Organizar `wordflow_kernel/` completo |
| 10º | **S10** | Cablear p01→p12 + adapter-layer + llenar stubs (gaps) |
| 11º | **S11** | Enganche LEGACY + no apagar monolito |
| 12º | **S12** | Cierre 100% (árbol = README + mapa Paso 3 cumplido) |

Cada salida **CREA** archivo nuevo:  
`PIPELINE/checkpoints/SALIDA_SN_YYYY-MM-DD.md`  
(**12 checkpoints** al final.)

---

## S1 — Estructura raíz (PLAN_100)

Materializar **todo** el árbol de `PLAN_100_ESTRUCTURA_DEFINITIVA.md` bajo `agente-yaiwes/`:

- code-programming-engine/ (subnodos)
- kernel-principal/ (extension-kernel, reasoning-kernel, resource-governance, internal-bus, …)
- input-layer/
- definition-registry/
- control-governance/
- multi-workflow-engine/
- execution-orchestration/
- execution-engine-pool/
- deploy-publish/
- state-events-durability/, observability/, agent-fleet-parallelism/, etc. (nodos del árbol completo)
- PLACEHOLDER.md solo en ESQ sin body; SOURCE.md en REF

**Sin inventar implementación.**

---

## S2 — DESPLIEGUE 1

Según `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`:
- capability registration (catalogs)
- pool / instance / metering
- classifier_hook
- deployment_01.yaml + verification.yaml

---

## S3 — Contrato del mapa (ORIGIN_MAP + COPY_MANIFEST)

Registrar **cada fila** del Paso 3: origen → destino → acción (MOVER INTACTO / REF / LLENAR / CABLEAR).  
Evidencia: archivos `agente-yaiwes/ORIGIN_MAP.md` + `COPY_MANIFEST.json`.

---

## S4 — Mapa top-level `extensions/wordflow/`

| Origen | Destino | Acción |
|--------|---------|--------|
| component_catalog.json + connect_catalog.json | definition-registry.declared-dependency-catalog | Mover intacto |
| ficha.v2.json / manifest.yaml | kernel-principal.extension-kernel.capability-registry | Mover intacto |
| accounts/ | deploy-publish.multi-account-registry | Mover intacto |
| codegen/dag.py | execution-orchestration.dag-executor | Mover intacto |
| connectors/ | deploy-publish.push-injection | Mover intacto |
| context/builder.py | execution-orchestration.dependency-injection-context | Mover intacto |
| contracts/ | definition-registry.domain-specific-contracts | Mover intacto |
| docs_templates/ | PIPELINE/ | Mover (documental) |
| motors/ (call, download, send) | code-programming-engine.external-motor-bridge | Mover intacto |
| motors/kernel_ext | puente code-programming-engine ↔ kernel-principal | Mover intacto |
| planner/ | execution-orchestration.mission-planning | Mover intacto |
| policies/engine_attach | kernel-principal.extension-kernel.abi-mount | Mover intacto |
| policies/sentinel + sheriff | control-governance.sentinel / .sheriff-bridge | Mover intacto |
| reception/ | input-layer.reception | Mover intacto |
| state/ | state-events-durability.run-state-store | Mover intacto |
| store/main_12.yaml | definition-registry.workflow-definition | Mover intacto |
| store/goals, council | execution-orchestration / control-governance.council | Mover intacto |
| tests/ | viaja con cada módulo | — |

---

## S5 — Mapa engine/ C-19 (hot path)

| Archivo | Destino | Nota |
|---------|---------|------|
| code_path_runner.py | code-programming-engine.code-path-execution | Target = p01→p12 wireado |
| programming_pipeline.py | code-programming-engine.engine-modules | Mover intacto |
| programming_kwargs.py | code-programming-engine.engine-modules | Mover intacto |
| input_quality_bar.py | code-programming-engine.engine-modules | Mover intacto |
| skill_native_compiler.py | code-programming-engine.engine-modules | Gap: hoy stub determinista |
| code_path_smoke.py | code-programming-engine.module-tests | Mover intacto |
| main_loop.py | Split: S01–S12 → multi-workflow-engine.shared-services.runner-host; S08b → programming-engine-binding | Bisagra |

**goal_lock / cognitive_loop / evidence_packet:** NO copiar aquí — solo referencia (regla lego).

---

## S6 — Mapa engine/ resto (agrupado)

| Prefijo/real | Destino |
|--------------|--------|
| acquire_12, analyze_12, reuse_12 | extensions.source-evolution-module |
| artifact_pin, bitacora, checkpoint_store, state_*, workflow_dna, reasoning_ledger, dna_* | state-events-durability.run-state-store |
| bootstrap, microkernel_install, entrypoint*, engine_abi, engine_attach, extension_registry | kernel-principal.extension-kernel |
| build_plan_only, mission, objective_echo, planning_proposal, fetch_planner, goals_* | execution-orchestration.mission-planning |
| capability_* | extension-kernel.capability-registry / .capability-passport |
| circuit_breaker, retry_policy, watchdog, lease_manager, resource_* | kernel-principal.resource-governance |
| claim_validator, evidence_*, write_evidence | observability.evidence-packet |
| contract_router, control_sheriff_bridge, sheriff_adapter, sentinel, council, refute_repair, repair_gate, validator, structured_questions | control-governance |
| credential_store | security-auth.secret-isolation |
| docker_transport, sandbox_manager, ssh_orchestrator, remote_workers | execution-orchestration.container-pod-isolation |
| dual_compiler | code-programming-engine.engine-modules |
| enchufe_gate | input-layer.reception |
| expert_*, role_analyzer | reasoning-kernel.expert-panel-router |
| github_*, hf_*, publish_path, push_ping*, project_mirror | deploy-publish |
| handoff | agent-fleet-parallelism.agent-handoff |
| kimi_policy | execution-engine-pool.capability-matching |
| loop_bridge | multi-workflow-engine.instances.programming-engine-binding |
| orchestrator* | execution-orchestration |
| parallel_*, wave4/5_runtime | agent-fleet-parallelism |
| ports/ | execution-engine-pool.adapter-layer |
| runtime_bus | kernel-principal.internal-bus |
| scheduler, task_* | execution-orchestration.task-classifier-scheduler |
| supervisor | agent-fleet-parallelism.dispatch-lifecycle |
| fake_engine.py | execution-engine-pool — **FAKE explícito** |

---

## S7 — Mapa standards/ → control-governance

| Archivo | Destino |
|---------|--------|
| executor_gates.py | control-governance.pre-post-gates |
| verdict_authority.py | control-governance.verdict-authority |
| forensic_core.py + forensic_contract.py | control-governance.forensic-core |
| closure_engine.py | control-governance.closure-engine |
| quality_dag.py + quality_handlers.py | control-governance.quality-dag |
| gap_registry.py | control-governance (con gap_tasks) |
| copy_first.py + adapt_imports.py | control-governance |
| checklist_* | control-governance.sheriff-bridge |
| symbol_index.py | control-governance.symbol-index-wiring-graph |
| resto utilidades | control-governance |

---

## S8 — Mapa schemas/

- Los **32** → `definition-registry.schema-contracts`
- `code_output.schema.json` + `goal_lock.schema.json` → además **referenciados** por `code-programming-engine.schema-contracts-io` (no duplicar)
- Gaps de schemas por stage C-19 → crear solo en `code-programming-engine.schema-contracts-io` cuando se generen

---

## S9 — Mapa wordflow_kernel/

| Origen | Destino |
|--------|--------|
| workflow.py | kernel-principal |
| instance.py, instance_store.py | multi-workflow-engine.shared-services |
| bootstrap_* | kernel-principal.extension-kernel |
| checkpoint.py | state-events-durability.checkpoint-recovery |
| fail_closed.py, llm_control.py | control-governance.llm-control-deny |
| forensic*, gap_tasks | control-governance.forensic-core |
| **gateway/intelligence.py, router_http.py** | **execution-engine-pool.adapter-layer** |
| **engines/openclaw_stub, hermes_stub, port.py** | **execution-engine-pool.auxiliary-role-agents** |
| memory_slot/, memory.py | tools-models-memory-knowledge |
| reception/* | input-layer.reception / deploy-publish.push-injection |
| resources/* | kernel-principal.resource-governance.resource-broker-gate |
| slots/kimi_minimax + placeholder | execution-engine-pool — PLACEHOLDER fusion:false |
| stages/* | kernel-principal |
| ui_gateway/* | fuera (DOC-UI00) |

---

## S10 — Gaps a rellenar (destino ya fijado)

| Gap | Destino |
|-----|--------|
| Adapters reales en intelligence_gateway | execution-engine-pool.adapter-layer |
| Contenido real openclaw/hermes stubs | execution-engine-pool.auxiliary-role-agents |
| p01→p12 wireado end-to-end | code-programming-engine.code-path-execution |
| Schemas por stage C-19 | code-programming-engine.schema-contracts-io |
| Export SYMBOL_INDEX_PROGRAMMING.md | control-governance.symbol-index-wiring-graph |
| Índice test→asserts | code-programming-engine.module-tests |
| Log CI real | observability.trace-history |

---

## S11 — Enganche LEGACY

- Marker LEGACY en paths viejos si aplica
- **No apagar** monolito `code_path_runner` hasta paridad de tests
- Hot path en main sigue siendo fuente operativa

---

## S12 — Cierre 100%

- [ ] Árbol `agente-yaiwes/` = PLAN_100 completo
- [ ] Cada fila del mapa Paso 3 ejecutada (MOVER/REF/LLENAR/CABLEAR)
- [ ] Regla lego respetada (sin duplicar goal_lock, cognitive_loop, evidence_packet)
- [ ] Monolito intacto o cutover solo con evidencia de tests
- [ ] Despliegue 1 auditado
- [ ] 12 checkpoints creados

---

## DSL DAG (todas las salidas)

Cada S1–S12:
- sheriff (NO_SKIP, NO_ASSUME, NO_HALLUCINATION, NO_FAKE_PASS, NO_REWRITE_SIN_PARIDAD)
- validador (evidence + binary PASS)
- verificación + verificación cruzada (tree / mapa / tests / catalogs)
- guardián fail-closed
- **checkpoint file NUEVO obligatorio**

---

## ESTADO

| Ítem | Estado |
|------|--------|
| README PLAN YAIWES v1 (este doc) | **HECHO** |
| Fuentes: PLAN_100 + Paso 3 mapa | **Integradas** |
| S1…S12 | PENDIENTE de ejecución |

**Siguiente:** ejecutar **S1** (estructura raíz), luego **S2** (Despliegue 1), luego **S3** (contrato del mapa) y seguir el orden.

**TOTAL DE SALIDAS = 12**  
**TOTAL DE CHECKPOINTS = 12**
