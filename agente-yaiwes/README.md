# Agente YAIWES — Guía maestra de estructura (yaiwes-omega)

**Repo:** maxbry123-commits/agentes  
**Rama operativa:** `main`  
**SHA de referencia al escribir este documento:** `2bd2600c`  
**Regla de trabajo:** NO reescribir código existente. Solo copiar (M1–M5) o crear PLACEHOLDER si el nodo no existe.  
**Wordflow de programación de code operativo (sigue vivo en main):**  
- Hot path: [`extensions/wordflow/engine/code_path_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py)  
- Pipeline: [`extensions/wordflow/engine/programming_pipeline.py`](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/programming_pipeline.py)  
- Tests: [`extensions/wordflow/tests/`](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/tests)  
- Docs PIPELINE: [`PIPELINE/`](https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE)

**Método de copia obligatorio:** [`METODO_ZIP_COPY_DETERMINISTA.md`](https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md)

---

## 0. Propósito de esta raíz `agente-yaiwes/`

Esta raíz es la **arquitectura en cascada** del Agente YAIWES (estructura lógica **yaiwes-omega**):

1. Organiza lo ya construido en el repo sin apagar el monolito operativo.
2. Separa el **motor de programación de code** (`code-programming-engine`) como pieza única compartida.
3. Deja nodos ausentes como carpetas + `PLACEHOLDER.md` (escalable, sin inventar implementación).
4. Sirve de guía de verificación cruzada: esqueleto 1 + esqueleto 2 + raíces reales de wordflow.

**Intocable durante reorganización:** el monolito en `main` (`code_path_runner.py` tal como está) sigue siendo la única fuente operativa real hoy. La rama `programming-modular-v1` es prototipo (bridge a legacy), no reemplazo.

---

## 1. Leyenda de estado por nodo

| Marca | Significado |
|-------|-------------|
| `[REAL]` | Existe código/archivos en el repo actual |
| `[ESQ]` | Solo en el esqueleto; aún no hay implementación |
| `[MIX]` | Parte real + parte esqueleto / gap documentado |
| `[REF]` | Debe referenciar otro nodo (no duplicar) |
| `[DOC]` | Documental |

---

## 2. Explicaciones de diseño (texto completo — no resumido)

### 2.1 Cómo se decide una tarea (task_classifier → reasoning)

```
task llega → task_classifier evalúa
     │
     ├─ hay una capacidad clara y única para esto → se usa directo
     │
     └─ hay ambigüedad o varias formas posibles de resolverlo
              → reasoning-kernel.expert-panel-router distribuye la decisión
              → si sigue sin resolverse → consensus-trigger activa
                comparación entre las opciones disponibles en capability-registry
              → gana la que pase por control-governance (sentinel/council),
                no la que "suene mejor" — el veredicto sigue siendo verificable,
                nunca autodeclarado
```

### 2.2 Cómo se monta una habilidad nueva (sin reescribir el kernel)

1. La habilidad nueva (un motor de code distinto, una forma nueva de resolver algo, una extensión) se construye por fuera, como pieza independiente.

2. Se monta a través de `extension-kernel.abi-mount`  
   → `mount-guard` verifica que no reescribe nada del núcleo.

3. Se registra en `extension-kernel.capability-registry`  
   → queda con `capability-passport` (qué tiene permitido hacer, con evidencia).

4. `reasoning-kernel` ahora "sabe" que existe, porque consulta el registro cada vez que necesita decidir cómo resolver algo — no porque se le reprogramó el razonamiento, sino porque el catálogo creció.

5. `native-learning` permite que esta habilidad se refuerce/ajuste con uso, siempre como capa acoplada, nunca reescribiendo `reasoning-kernel` en sí.

### 2.3 Cómo se añade un workflow-N (aislamiento)

1. Se crea `workflow-N/` con la MISMA forma exacta que `workflow-1/2/3`  
   (`definition-binding`, `execution-state`, `task-queue`, `engine-pool-binding`, `programming-engine-binding`).

2. Se registra en `multi-workflow-engine.shared-services.workflow-registry`  
   → esto NO modifica workflow-1/2/3, solo añade una entrada nueva al catálogo.

3. `runner-host` lo activa cuando llega una tarea con destino a ese proyecto  
   → le asigna handle único, su propio budget-slot, su propia cola.

4. Desde ese momento `workflow-N` funciona en paralelo a los demás, sin que ninguno se entere del otro (aislamiento ya garantizado).

### 2.4 Decisión code vs no-code

```
task_classifier (dentro de execution-orchestration, ya existente)
       │
       ├─ ¿la tarea requiere programar código?
       │
       ├─ SÍ → workflow-N.programming-engine-binding
       │         → invoca code-programming-engine (motor compartido, único)
       │         → si necesita ejecutar con un motor real (Claude Code, Codex, etc.)
       │            → delega a execution-engine-pool
       │
       └─ NO → workflow-N sigue su propio camino normal
                 (ej: investigación, orquestación de tarea no-code, research-evidence, etc.)
```

### 2.5 Por qué `code-programming-engine` NO va dentro de cada workflow-N

El sistema de programación de code (~80 módulos: loop principal, ejecutor de path de código, bloqueo de objetivos, standards forenses, schemas, motores, reception) es pesado y es **el mismo motor** para cualquier proyecto. Si lo metes dentro de `workflow-1/`, tendrías que copiarlo también en `workflow-2/` y `workflow-3/` — rompe la regla de lego (nada se duplica, todo se referencia).

### 2.6 Por qué NO va tragado dentro de `extension-kernel/`

`extension-kernel` es el **mecanismo genérico de montaje** (el ABI, el registro de capacidades, la guardia anti-reescritura) — es la puerta, no lo que entra por la puerta. El sistema de programación de code es una capacidad concreta y enorme (~80 módulos con lógica de negocio real). Meterlo ahí dentro convertiría a `extension-kernel` en un monolito otra vez.

### 2.7 Ubicación correcta del motor de programación

```
├── code-programming-engine/          → motor de programación de code, PIEZA ÚNICA compartida
│   ├── engine-modules/
│   ├── code-path-execution/
│   ├── standards-forensic/
│   ├── schema-contracts-io/
│   ├── external-motor-bridge/
│   ├── multi-account-bridge/
│   ├── inbox-normalization/
│   └── module-tests/
│
├── kernel-principal/
│   └── extension-kernel/
│       └── capability-registry/   → REGISTRA code-programming-engine (apunta, no contiene)
│
├── multi-workflow-engine/
│   └── instances/
│       └── workflow-N/
│           └── programming-engine-binding/  → referencia liviana al motor único
```

Cómo se conecta en la práctica:

1. `code-programming-engine` existe **una sola vez** en la raíz.
2. `extension-kernel.capability-registry` lo **registra** como capacidad disponible.
3. Cada `workflow-N` tiene un `programming-engine-binding/` — referencia, no copia.
4. Cuando el motor necesita un ejecutor concreto (Claude Code, Codex, etc.), llama a `execution-engine-pool` — también compartido.

### 2.8 Hallazgos críticos del código real (antes del mapa)

1. **`wordflow_kernel/gateway/intelligence.py`** (`make_request`) + **`router_http.py`** (`RouterHTTPGateway`) es el **stub central** que el catálogo marca como `intelligence_gateway: stub`, con adapters `Mock` y `RouterHTTP` únicamente. **Este es el punto donde entra `execution-engine-pool.adapter-layer`** con motores reales. No hay que crear el punto de enchufe — ya existe; faltan adapters reales.

2. **`wordflow_kernel/engines/openclaw_stub.py` y `hermes_stub.py`** — son los stubs de agentes de paralelo/supervisión. No se crean desde cero: se llenan.

3. **La rama `programming-modular-v1`** (`p01_context_gate.py` … `12_return.py`) ya intenta dividir `code_path_runner.py` en stages. El problema: `runner.py` **bridgea al legacy** en vez de orquestar p01→p12. Es el prototipo del estado final: hay que **terminar de cablearlo**, no rehacerlo.

### 2.9 Regla de módulos compartidos (lego — nada se duplica)

`goal_lock.py`, `cognitive_loop.py`, `evidence_packet.py` están cableados **tanto al loop general** (S02/S09 de `main_loop`) **como al hot path C-19**. Viven **una sola vez** en su nodo general; `code-programming-engine` los **referencia**, no los copia.

| Módulo | Vive en (única vez) | `code-programming-engine` lo usa vía |
|--------|---------------------|--------------------------------------|
| `goal_lock.py` | `execution-orchestration.goal-lock` | referencia/import |
| `cognitive_loop.py` | `execution-orchestration.mission-planning` | referencia |
| `evidence_packet.py` | `observability.evidence-packet` | referencia |

### 2.10 Regla de intocable

El monolito en `main` (`code_path_runner.py`) sigue siendo la única fuente operativa real hoy. Organizar/mover carpetas y referencias primero; no apagar ni reemplazar el hot path monolítico hasta que la versión dividida pase los mismos tests (`test_code_path_runner.py`, `test_unified_programming.py`, etc.) con el mismo resultado.

### 2.11 Métodos de copia permitidos (sin reescribir)

| # | Método | Uso |
|---|--------|-----|
| M1 | Contents API (get + put mismo content) | 1 archivo |
| M2 | Push files batch | Varios archivos, mismo content |
| M3 | Pointer / SOURCE.md | Declara path canónico sin duplicar body |
| M4 | PLACEHOLDER.md | Nodo del esqueleto sin origen real |
| M5 | COPY_MANIFEST.json | Lista origen→destino→método→verificación |

---

## 3. Estructura completa unificada (esqueleto 1 + esqueleto 2 + wordflow real)

```text
agente-yaiwes/
│
├── code-programming-engine/                                    [MIX]
│   ├── engine-modules/                                         [REAL]
│   ├── code-path-execution/                                    [MIX]
│   ├── standards-forensic/                                     [REAL]
│   ├── schema-contracts-io/                                    [MIX]
│   ├── external-motor-bridge/                                  [REAL]
│   ├── multi-account-bridge/                                   [REAL]
│   ├── inbox-normalization/                                    [REAL]
│   └── module-tests/                                           [REAL]
│
├── kernel-principal/                                           [MIX]
│   ├── control-layer/                                          [REAL]
│   ├── extension-kernel/
│   │   ├── abi-mount/                                          [MIX]
│   │   ├── capability-registry/                                [MIX]
│   │   ├── capability-passport/                                [ESQ]
│   │   ├── native-learning/                                    [ESQ]
│   │   └── mount-guard/                                        [ESQ]
│   ├── reasoning-kernel/
│   │   ├── decision-on-demand/                                 [ESQ]
│   │   ├── expert-panel-router/                                [MIX]
│   │   ├── consensus-trigger/                                  [ESQ]
│   │   ├── goal-dual-driver/                                   [ESQ]
│   │   └── workflow-capacity/                                  [ESQ]
│   ├── resource-governance/
│   │   ├── resource-broker-gate/                               [MIX]
│   │   ├── lease-management/                                   [MIX]
│   │   ├── watchdog/                                           [MIX]
│   │   ├── circuit-breaker/                                    [MIX]
│   │   └── retry-policy/                                       [MIX]
│   ├── internal-bus/                                           [MIX]
│   └── execution-manifest/                                     [ESQ]
│
├── input-layer/                                                [MIX]
│   ├── cli-entry/ … route-entry/                               [ESQ]
│   ├── cross-tool-session-import/                              [ESQ]
│   └── reception/                                              [REAL]
│
├── definition-registry/                                        [MIX]
│   ├── workflow-definition/ (yaml-dag, step-template, source-hierarchy)
│   ├── agent-definition/ task-definition/ tool-definition/
│   ├── skill-definition/
│   ├── schema-contracts/                                       [REAL]
│   ├── domain-specific-contracts/                              [REAL]
│   ├── declared-dependency-catalog/                            [REAL]
│   └── authorization-model/                                    [ESQ]
│
├── control-governance/                                         [MIX]
│   ├── contracts-base / contracts-C00-C85/
│   ├── sheriff-bridge/ sentinel/ council/
│   ├── forensic-core/ verdict-authority/
│   ├── symbol-index-wiring-graph/
│   ├── workflow-validation/ policy-engine/
│   ├── guardrails-validation/ structured-output-validation/
│   ├── evaluation-scoring-report/ permission-check-engine/
│   ├── refute-repair/ llm-control-deny/
│   ├── pre-post-gates/ closure-engine/ quality-dag/
│   └── gap_tasks / gap_registry
│
├── multi-workflow-engine/
│   ├── shared-services/ (registry, runner-host, dashboard, budget, control-ops)
│   └── instances/workflow-{1,2,3,N}/
│       ├── definition-binding/
│       ├── execution-state/
│       ├── task-queue/
│       ├── engine-pool-binding/
│       └── programming-engine-binding/
│
├── execution-orchestration/
│   ├── state-machine-executor/ dag-executor/
│   ├── sequential-parallel-loop-route/ container-pod-isolation/
│   ├── task-generation/ deterministic-execution/
│   ├── mission-planning/ goal-lock/
│   ├── task-classifier-scheduler/
│   ├── dependency-injection-context/
│   └── programming-pipeline/  [REF → code-programming-engine]
│
├── agent-fleet-parallelism/
├── execution-engine-pool/
│   ├── adapter-layer/          [REAL STUB gateway + PLACEHOLDER motores reales]
│   ├── capability-matching/
│   ├── parallel-dispatch/ worktree-isolation/ result-normalization/
│   └── auxiliary-role-agents/  [REAL openclaw_stub, hermes_stub]
│
├── mesh-routing-collaboration/
├── pipeline-runtime/
├── codebase-intelligence/
├── session-resilience/
├── identity-config/
├── human-in-the-loop/
├── communication-notifications/
├── control-plane-ui/
├── state-events-durability/   (+ dead-letter-handling)
├── tools-models-memory-knowledge/  (+ mcp-transport)
├── research-evidence/
├── security-auth/
├── observability/
├── multi-project-orchestration/
├── artifact-output-storage/
├── deploy-publish/            (+ deployment-target-selector)
│
├── extensions/
│   ├── wordflow-engine-module/
│   ├── wordflow-kernel-module/
│   ├── source-evolution-module/
│   ├── project-bootstrap-module/
│   ├── audit-forensic-module/
│   ├── maxbry_loop /
│   ├── github_deploy / github_publisher /
│   ├── adapters / knowledge/
│
├── PIPELINE/                  [DOC REAL]
├── agents/                    [REAL]
├── .github-workflows-refs/    [DOC índice; no mueve .github real]
├── ORIGIN_MAP.md              (pendiente en siguiente fase)
└── COPY_MANIFEST.json         (pendiente en siguiente fase)
```

### 3.1 Raíces reales que ya existen en `main` (deben quedar representadas)

```text
/
├── .github/workflows/
├── PIPELINE/
├── agents/
├── control-layer/
├── docs/
├── extensions/
│   ├── wordflow/
│   ├── wordflow_kernel/
│   ├── maxbry_loop/
│   ├── source_evolution/
│   ├── project_bootstrap/
│   ├── audit_forensic/
│   ├── github_deploy/
│   ├── github_publisher/
│   ├── adapters/
│   └── knowledge/
├── groups/
├── memory/
├── scripts/
├── tools/
├── wordflow/   (top-level además de extensions/wordflow)
└── METODO_ZIP_COPY_DETERMINISTA.md + guías
```

---

## 4. Verificación cruzada — checklist de no-omisión

### 4.1 Nodos del esqueleto largo que el corto omitía (DEBEN existir)

- [x] `capability-passport`
- [x] `expert-panel-router`
- [x] `goal-dual-driver`
- [x] `resource-broker-gate` / `lease-management` / `watchdog` / `circuit-breaker` / `retry-policy`
- [x] `internal-bus` + `execution-manifest`
- [x] `cross-tool-session-import`
- [x] `declared-dependency-catalog` + `domain-specific-contracts`
- [x] `symbol-index-wiring-graph`
- [x] `human-in-the-loop` completo
- [x] `communication-notifications`
- [x] `control-plane-ui`
- [x] `dead-letter-handling`
- [x] `mcp-transport`
- [x] `artifact-output-storage`
- [x] `deployment-target-selector`
- [x] `code-programming-engine` como raíz propia compartida
- [x] `programming-engine-binding` en cada workflow-N

### 4.2 Piezas REALES del wordflow que el esqueleto debe mapear

- [x] `code_path_runner.py` C-19
- [x] `programming_pipeline.py` + `programming_kwargs.py`
- [x] `input_quality_bar.py` / `skill_native_compiler.py` / `main_loop.py` / `store/main_12.yaml`
- [x] `standards/*` forense completo
- [x] `schemas/*` (32) + `component_catalog.json` + `connect_catalog.json`
- [x] `wordflow_kernel` gateway + engines stubs + stages + reception + resources
- [x] `maxbry_loop/code_path_bridge.py`
- [x] tests C-19 listados en auditoría
- [x] workflows `test-wordflow-code-path.yml`, `wordflow-full-verification.yml`, `forensic-gates.yml`
- [x] `control-layer/` top-level
- [x] rama modular `programming-modular-v1` stages p01–p12

### 4.3 Gaps explícitos (destino ya fijado)

| Gap | Destino |
|-----|---------|
| Export `SYMBOL_INDEX_PROGRAMMING.md` | `control-governance.symbol-index-wiring-graph` |
| Schemas por stage C-19 | `code-programming-engine.schema-contracts-io` |
| Log real de CI capturado | `observability.trace-history` |
| p01→p12 wireado end-to-end | `code-programming-engine.code-path-execution` |
| Adapters reales en gateway | `execution-engine-pool.adapter-layer` |
| Contenido real openclaw/hermes | `execution-engine-pool.auxiliary-role-agents` |

---

## 5. Mapa I/O del wordflow de PROGRAMACIÓN DE CODE

**Convención:** `Archivo` ➡️ qué hace ➡️ a qué conecta ➡️ **INPUT** ➡️ **OUTPUT**

Verificado contra código en `main` SHA `2bd2600c` (bodies leídos en auditoría).  
Paths canónicos bajo `extensions/wordflow/` salvo donde se indica.

---

### 5.1 Entrada al path (quién llama a C-19)

**`engine/main_loop.py` → `run_main_12`**  
➡️ Ejecuta loop S01–S12; si `programming_path=True`, tras council invoca `default_pipeline().run_unified` (S08b).  
➡️ Conecta: `load_main_12` ← `store/main_12.yaml`; → `programming_pipeline.run_unified` → `run_code_path`.  
➡️ **INPUT:** `raw` (bloque normalizado), `programming_path`, `programming_kwargs`, `programming_full_pass`.  
➡️ **OUTPUT:** `state` con `status` (FAILED|COMPLETED|REJECTED|RUNNING), opcional `programming` dict, `stop_reason` posible `PROGRAMMING_PATH_FAIL`.

**`store/main_12.yaml`**  
➡️ Definición declarada del loop (12 steps, on_fail stop).  
➡️ Conecta: leído solo por `load_main_12`.  
➡️ **INPUT:** archivo YAML.  
➡️ **OUTPUT:** dict `loop_id=main_12`, `steps[]`, `on_fail`, `on_reject`.

**`extensions/maxbry_loop/code_path_bridge.py` → `dispatch_run_code_path`**  
➡️ Puente loop → C-19; **no claim PASS**; default context False → BLOCK.  
➡️ Conecta: → `run_code_path`.  
➡️ **INPUT:** `text`, `mission_id`, `context_verified=False`, `handoff_verified=False`.  
➡️ **OUTPUT:** `{ok, invoked, c19_ok, verdict, llm_control, stage?}` siempre `llm_control=DENY`.

**`engine/programming_pipeline.py` → `ProgrammingPipeline.run_unified`**  
➡️ Valida kwargs conocidos (U2); orquesta pre/copy/post + `run_code_path`.  
➡️ Conecta: → `run_code_path`; `pre_implement` / `copy_existing` / `post_verify`.  
➡️ **INPUT:** `raw_input` + kwargs de `KNOWN_KW` (o BLOCK stage kwargs).  
➡️ **OUTPUT:** resultado de `run_code_path` + `u_status` / `policy` según flujo; unknown kwargs → `{ok:false, stage:kwargs}`.

**`engine/programming_kwargs.py`**  
➡️ Kwargs canónicos fail-closed.  
➡️ Conecta: usado por tests y callers de pipeline.  
➡️ **INPUT:** `full_pass_kwargs(ci_attestation=True, …)` o `minimal_block_kwargs()`.  
➡️ **OUTPUT:** dict kwargs; sin attestation → **RuntimeError**.

---

### 5.2 Hot path C-19 — `engine/code_path_runner.py`

**`consult_path_gateway(mission_id, raw_input)`**  
➡️ Consulta gateway con policy vendor DENY (CONN.path_gateway WIRED_DENY).  
➡️ Conecta: → `wordflow_kernel.gateway.intelligence.make_request` + `RouterHTTPGateway.execute`.  
➡️ **INPUT:** mission_id, raw_input (prompt truncado 200).  
➡️ **OUTPUT:** `{ok, invoked, status, provider, llm_control:DENY, contract:WIRED_DENY|GAP, vendor_call:false, …}`.

**`run_code_path(raw_input, **kwargs)`**  
➡️ Única orquestación operativa del path de code (UNIFIED_RUNNER_V1).  
➡️ Conecta (secuencia real en código):

1. `ContextManifest` / `ContextValidator` (si require_context_manifest)  
2. `VerdictAuthority.require_context`  
3. `ExecutorPreImplementGate.check` (+ opcional `copy_file_deterministic` / `adapt_file`)  
4. `admit_or_reject` (quality bar)  
5. `lock_goals`  
6. `PolicySnapshot.freeze`  
7. `run_cognitive_loop`  
8. `compile_skill_to_code` (si skill)  
9. `consult_path_gateway`  
10. `build_evidence_packet` + `verify_evidence_packet` + `merge_evidence`  
11. `QualityDAG` + handlers  
12. `auto_measure_core` / `auto_measure_fc`  
13. `VerdictAuthority.decide` (forensic state)  
14. `ClosureEngine.decide`  

➡️ **INPUT principal:**  
`raw_input: str`  
kwargs: `context_verified`, `handoff_verified`, `core_measures`, `connectivity`, `counters`, `evidence_complete`, `final_clean_reaudit_passed`, `quality_dag_ok`, `context_manifest`, `require_context_manifest`, `symbol_or_stem`, `dest`, `checklist`, `require_pre_gate`, `require_checklist`, `run_quality_dag`, `fc_results`, `require_fc`, `auto_measure_core`, `auto_measure_fc`, `apply_adapt`, `import_mapping`, `profile`, `scan_paths`, `plan_steps`, `skill`, `mission_id`, `consult_gateway`.

➡️ **OUTPUT (keys reales):**  
`ok`, `mission_id`, `lock`, `cognitive`, `skill_compile`, `evidence`, `evidence_merged`, `evidence_ok`, `forensic`, `pre_gate`, `closure`, `gaps`, `core_measures`, `fc_measures`, `quality_dag`, `policy`, `path_gateway`, `wire_trace`, `llm_control` (=DENY), `verdict`, `path` (=UNIFIED_RUNNER_V1), `gc_status`, `gr_status`, `c_status`, `s_status`, `t_status`, `u_status`.

➡️ **Early-return stages posibles:** `context_manifest`, `context`, `pre_gate`, `post_adapt`, `quality_bar`, `goal_lock`.

---

### 5.3 Módulos engine llamados por el hot path

**`engine/input_quality_bar.py` → `admit_or_reject` / `evaluate_input_quality`**  
➡️ Barra de admisión de texto (min 40 chars, never_mvp, señal de objetivo).  
➡️ Conecta: llamado por `run_code_path` stage quality_bar.  
➡️ **INPUT:** `text`, `min_chars=40`, `require_objective=True`.  
➡️ **OUTPUT:** `{ok, reason_codes, chars, min_chars, thresholds, llm_control:DENY, policy:never_mvp}` o raise `QualityBarError`.

**`engine/goal_lock.py` → `lock_goals` / `create_goal_lock` / `validate_against_lock`**  
➡️ Contrato de objetivo inmutable post-sentinel.  
➡️ Conecta: `normalize_input_block`, `extract_goals_in`, `run_sentinel`; consumido por runner y main_loop.  
➡️ **INPUT:** raw dict/text; o goals COMPILED para `create_goal_lock`.  
➡️ **OUTPUT:** `{ok, lock, sentinel, reason_codes}` o lock schema-compatible con `lock_hash`.

**`engine/cognitive_loop.py` → `run_cognitive_loop`**  
➡️ Wire de plan/council determinista en path code.  
➡️ Conecta: desde `run_code_path`.  
➡️ **INPUT:** `topic`, `plan_steps`, `mission_id`, `goal_lock`, `task_class="CODE"`.  
➡️ **OUTPUT:** dict cognitive (ok / plan wire); no autoriza PASS forense solo.

**`engine/skill_native_compiler.py` → `compile_skill_to_code` / `compile_and_promote_skill`**  
➡️ Skill package → seed `code_output` (stub determinista, 0% LLM).  
➡️ Conecta: `dual_compiler.compile_output`, `promote_12`.  
➡️ **INPUT:** skill dict (`package_id`|`skill_id`), opcional `version_pin`.  
➡️ **OUTPUT:** `{ok, skill_id, code_output, content_map, validation, llm_control:DENY}`.

**`engine/evidence_packet.py` → `build_evidence_packet` / `verify_evidence_packet`**  
➡️ Paquete de evidencia de claim.  
➡️ Conecta: runner; merge en standards.  
➡️ **INPUT:** task_id, claim_status, paths, tests, doc_anchors, notes.  
➡️ **OUTPUT:** packet dict; verify → `{ok}`.

**`engine/code_path_smoke.py` → `run_smoke`**  
➡️ Integración offline del path.  
➡️ Conecta: ensambla steps hacia runner/pipeline.  
➡️ **INPUT:** (defaults internos).  
➡️ **OUTPUT:** `{ok, steps, llm_control:DENY}`.

---

### 5.4 Standards forenses (columna vertebral de veredicto)

**`standards/verdict_authority.py` → `VerdictAuthority`**  
➡️ Última palabra context + decide forensic.  
➡️ Conecta: `require_context` al inicio; `decide(state=ForensicEnforcementState)` al final.  
➡️ **INPUT:** flags context/handoff; state completo.  
➡️ **OUTPUT:** mensaje BLOCK opcional; o `{verdict: PASS|FAIL|BLOCK, …}`.

**`standards/executor_gates.py` → `ExecutorPreImplementGate` / `ExecutorPostVerifyGate`**  
➡️ Pre: copy-first + sheriff checklist; Post: verify contract/evidence.  
➡️ Conecta: pre en runner; post en pipeline.  
➡️ **INPUT:** context flags, symbol_or_stem, dest, checklist.  
➡️ **OUTPUT:** `{allow, reason, copy_first, checklist, …}`.

**`standards/forensic_core.py` → `ForensicProgrammingEnforcer` / state types**  
➡️ CORE-01..14, FC_*, CONNECTIVITY_CHAIN, 4-pass, evaluate.  
➡️ Conecta: tipos usados por authority y auto_measure.  
➡️ **INPUT:** `ForensicEnforcementState`.  
➡️ **OUTPUT:** pass results / verdict structure.

**`standards/closure_engine.py` → `ClosureEngine.decide`**  
➡️ Cierra misión solo si checklist+forensic+evidence+counters limpios.  
➡️ Conecta: final de `run_code_path`.  
➡️ **INPUT:** `ClosureInput` (flags + gap_registry).  
➡️ **OUTPUT:** `{closed: bool, …}`.

**`standards/quality_dag.py` + `quality_handlers.py`**  
➡️ Grafo de chequeos deterministas fail-closed.  
➡️ Conecta: `register_deterministic_handlers` + `dag.run`.  
➡️ **INPUT:** paths, quality_dag_ok hint.  
➡️ **OUTPUT:** results list; `passed` bool.

**`standards/gap_registry.py`**  
➡️ Registro de gaps bloqueantes.  
➡️ Conecta: pre_gate, fc, adapt, closure.  
➡️ **INPUT:** `Gap(...)`.  
➡️ **OUTPUT:** `to_list()`, `open_count()`.

**`standards/context_manifest.py`**  
➡️ Manifest de contexto de misión.  
➡️ Conecta: stage 1 opcional del runner.  
➡️ **INPUT:** ContextManifest fields.  
➡️ **OUTPUT:** validate → `{ok, …}`.

**`standards/core_auto_measure.py` / `fc_auto_measure.py`**  
➡️ Rellena medidas CORE/FC sin LLM.  
➡️ Conecta: runner auto_measure_*.  
➡️ **INPUT:** caller measures, paths, hints.  
➡️ **OUTPUT:** `{measures, evidence, …}`.

**`standards/copy_first.py` / `adapt_imports.py`**  
➡️ Copia determinista y reescritura de imports.  
➡️ Conecta: post pre_gate si apply_adapt.  
➡️ **INPUT:** src, dest, import_mapping.  
➡️ **OUTPUT:** wire adapt dict; post_adapt parse AST ok/fail.

**`standards/evidence_merge.py` / `evidence_verifier.py`**  
➡️ Merge y verificación de refs de evidencia.  
➡️ Conecta: runner evidence stage.  
➡️ **INPUT:** engine_packet, mission_id, task_id.  
➡️ **OUTPUT:** `{complete, merged, …}`.

**`standards/path_resolve.py`**  
➡️ Resuelve paths de repo.  
➡️ Conecta: dest_resolved, scan roots.  
➡️ **INPUT:** path string, must_exist.  
➡️ **OUTPUT:** Path resuelto o error.

**`standards/checklist_factory.py` / `checklist_sheriff.py`**  
➡️ Checklist de agente y claim.  
➡️ Conecta: pre_gate.  
➡️ **INPUT:** dict checklist / claim.  
➡️ **OUTPUT:** AgentChecklistClaim; passed flags.

**`standards/policy_snapshot.py`**  
➡️ Congela policy de misión.  
➡️ Conecta: tras goal_lock.  
➡️ **INPUT:** mission_id.  
➡️ **OUTPUT:** snapshot (mission_id, contract_version, frozen_at).

**`standards/symbol_index.py`**  
➡️ Índice AST de símbolos (cache disco opcional).  
➡️ Conecta: tooling G-W3; **no hay export materializado en árbol del repo**.  
➡️ **INPUT:** roots, limit_files.  
➡️ **OUTPUT:** `SymbolIndex` (by_name hits).

---

### 5.5 Schemas I/O

**`schemas/code_output.schema.json`**  
➡️ Contrato de artefacto de code.  
➡️ Conecta: skill_native / dual_compiler.  
➡️ **INPUT validado:** schema_version, artifact_id, files[], evidence_ref; llm_control const DENY.  
➡️ **OUTPUT:** validación ok/fail.

**`schemas/goal_lock.schema.json`**  
➡️ Contrato GoalLock inmutable.  
➡️ Conecta: `create_goal_lock` / Engine ABI.  
➡️ **INPUT validado:** lock_id, objective, success_criteria, constraints, forbidden, status, lock_hash (64), …  
➡️ **OUTPUT:** validación ok/fail.

**Resto `schemas/*` (hasta 32)**  
➡️ Contratos compartidos del wordflow general.  
➡️ Destino arquitectura: `definition-registry.schema-contracts`; code_output/goal_lock también referenciados desde `schema-contracts-io`.

---

### 5.6 Catálogos declarados

**`component_catalog.json`**  
➡️ Componentes y status (materialized/stub/partial).  
➡️ Conecta: documentación + connect_catalog source.  
➡️ **INPUT:** N/A (declarativo).  
➡️ **OUTPUT:** lista components + connect_rules (LLM solo vía gateway, etc.).

**`connect_catalog.json`**  
➡️ Aristas from→to con status WIRED / WIRED_DENY / WIRED_NO_PASS / STUB.  
➡️ Conecta: auditoría de cableado.  
➡️ **Claves C-19:** CONN.core_path, CONN.runner_standards, CONN.path_gateway (WIRED_DENY), CONN.loop_path (WIRED_NO_PASS), CONN.bootstrap_fake_path (WIRED_NO_PASS).

---

### 5.7 Kernel gateway (enchufe execution-engine-pool)

**`extensions/wordflow_kernel/gateway/intelligence.py` → `make_request`**  
➡️ Construye request de capability (llm.complete, memory.*).  
➡️ Conecta: `consult_path_gateway`.  
➡️ **INPUT:** task_id, capability, payload, policy.  
➡️ **OUTPUT:** request object.

**`extensions/wordflow_kernel/gateway/router_http.py` → `RouterHTTPGateway.execute`**  
➡️ Ejecuta request; en path C-19 policy DENY → no vendor call.  
➡️ Conecta: runner path_gateway.  
➡️ **INPUT:** request.  
➡️ **OUTPUT:** result status/provider/output/evidence_hash (DENY esperado en C-19).

**`engines/openclaw_stub.py` / `hermes_stub.py`**  
➡️ EnginePort.reason stubs.  
➡️ Conecta: catalog WIRED_STUB.  
➡️ **INPUT:** reason payload.  
➡️ **OUTPUT:** intermediate stub (no PASS C-19).

---

### 5.8 Modular branch (no operativo en main)

**`programming/p01_context_gate.py`**  
➡️ Extrae stage context_manifest + require_context.  
➡️ Conecta: debería ser stage 1 del runner modular; **hoy no orquestado** (bridge legacy).  
➡️ **INPUT/OUTPUT:** equivalentes a stages context del monolito.

**`programming/12_return.py` → `build_return`**  
➡️ Arma return UNIFIED_RUNNER_V1_MODULAR.  
➡️ Conecta: debería ser stage final; **no cableado en runner modular actual**.  
➡️ **OUTPUT:** mismas keys + `modular: true`.

**`programming/runner.py`**  
➡️ Entry modular que **bridgea 100% a legacy** `run_code_path`.  
➡️ **INPUT/OUTPUT:** igual que monolito.

---

### 5.9 Tests (comportamiento declarado)

| Test file | Qué verifica |
|-----------|----------------|
| `test_code_path_runner.py` | BLOCK sin context; reject short; fail sin CORE; PASS con medidas full; skill_compile; gateway DENY |
| `test_unified_programming.py` | kwargs unknown; minimal block; pass attested; main_12 signature flags; U1-U10 |
| `test_main12_programming.py` | load main_12; programming_path minimal DENY |
| `test_input_quality_bar.py` | good / MVP / short / empty |
| `test_skill_native_compiler.py` | compile / promote / missing id |
| `test_code_path_smoke.py` | smoke ok + DENY |

---

### 5.10 CI

**`.github/workflows/test-wordflow-code-path.yml`**  
➡️ unittest discover wordflow + wordflow_kernel + maxbry_loop.  
➡️ **INPUT:** push paths o workflow_dispatch.  
➡️ **OUTPUT:** pass/fail CI (log de run **no** versionado en git).

---

## 6. Enlaces canónicos de revisión (main)

| Recurso | URL |
|---------|-----|
| Este README | https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/README.md |
| code_path_runner | https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py |
| programming_pipeline | https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/programming_pipeline.py |
| forensic_core | https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/standards/forensic_core.py |
| component_catalog | https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/component_catalog.json |
| connect_catalog | https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/connect_catalog.json |
| tests wordflow | https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/tests |
| PIPELINE programming | https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE |
| Método copia | https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md |
| Rama modular | https://github.com/maxbry123-commits/agentes/tree/programming-modular-v1/extensions/wordflow/engine/programming |

---

## 7. Próximo cambio (solo tras tu confirmación)

1. Scaffold de carpetas `agente-yaiwes/**` con PLACEHOLDER en nodos `[ESQ]`.
2. Copia M1/M2 del bloque `code-programming-engine` (sin reescribir bodies).
3. ORIGIN_MAP.md + COPY_MANIFEST.json.
4. **No** apagar ni editar `extensions/wordflow` operativo.

**Estado actual:** solo existe este README bajo `agente-yaiwes/`. El resto del árbol aún no se ha materializado a la espera de tu OK.
