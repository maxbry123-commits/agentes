# PIPELINE 47 — Wordflow V1 plan · forense loops · residual programable

**Fecha:** 2026-08-15  
**Repo:** maxbry123-commits/agentes  
**Fuente de verdad:** GitHub only  
**Claim:** NO 100% sistema · plan V1 operativa 6 puntos + forensic + continuous loop  
**Cualquier Grok:** leer este doc + PIPELINE 46 + 45 antes de code

---

## A. FORENSE LOOPS (claim vs realidad)

### A.1 Qué SÍ existe en GitHub (wordflow actual)

| Path / pieza | Qué es | Qué NO es |
|--------------|--------|-----------|
| `engine/cognitive_loop.py` | Wire context→council→plan→evidence | No es fusión Minimax/Kimi |
| `engine/code_path_runner.py` | quality→lock→cognitive→compile | Un shot path, no bucle continuo |
| `engine/repair_gate.py` | max_repair + fail_closed | No continuous loop engine |
| `state/ledger.py` + blackboard | Historial / estado vivo | No mission continuous loop |
| `planner/mission_planner.py` | Council→TaskGraph | No 12-stage continuous |
| Project bootstrap KTP states | Estados bootstrap | No maxbry_loop |

**Veredicto forense:**  
**NO se cerró el loop de trabajo continuo tipo Kimi/Minimax/maxbry_loop.**  
Se cerró un **code-path determinista + cognitive wire mínimo**.  
Cualquier claim previo de “loops F4 cerrados” = **REFUTADO**.

### A.2 Qué traen los zips del Director (attachments, aún no en repo)

| Zip | Contenido clave | Uso en V1 |
|-----|-----------------|-----------|
| `wordflow_kernel_extension_code.zip` | forensic.py, repo_truth, gap_tasks, memory, ledger, runtime, workflow, deploy, checkpoint, trace, sandbox, resources, tests, CI yml | **Montar** en `extensions/wordflow_kernel/` |
| `wordflow_kernel_12_stage_loop.zip` | 12-stage loop package | Conectar a GoalLock + TaskGraph |
| `maxbry_continuous_loop.zip` / `_v2` | engine, gaps, integrity, persistence, adaptive, convergence, recovery, config/loop.yaml | **Loop de trabajo continuo** nativo V1 |

### A.3 Diferencia conceptual (obligatoria)

```
A) Code-path loop (YA parcial en repo)
   Input → analyze → compile → claim → deploy dry-run

B) Continuous work loop (FALTA — zips maxbry_loop)
   Goal markers → plan → task → execute → gap → repair → converge → until DONE

C) Kimi/Minimax fusion strategy loops (R2)
   Enjambre/estrategias de fusión de agentes — NO es B; diferido R2 salvo slots
```

V1 monta **B** desde zips + conecta a planner/goal del kernel.  
**C** queda residual R2 (solo YAML slots si hay tiempo).

---

## B. Wordflow V1 — definición DONE (6 puntos + extras)

| # | Punto | DONE mínimo |
|---|--------|-------------|
| 0 | PIPELINE residual | Este doc + 46 + lista tareas con anclas |
| 1 | Docs→code→deploy + project docs + **continuous loop** | maxbry_loop o 12-stage cableado a goals/tasks |
| 2 | Multi GitHub account + HF resource modes | AccountRegistry + ResourceContract + loaders |
| 3 | ACQUIRE-OS download agentes/software | core/verify/build/promote + ficha testing |
| 4 | README + catalog + self-connect | component_catalog + README mapa |
| 5 | Kernel ext Router/Osquestador/engines ports | wordflow_kernel from zip + ports |
| 6 | Gateway UI | submit/state/events/approve |
| + | Forensic auditor | forensic + repo_truth + gap→task (zip) |
| + | Continuous loop | maxbry_loop_v2 montado + GoalLock markers |

**Flags default:** FETCH=false, ACQUIRE_OS_ENABLED=false, dry_run_default=true

---

## C. Lista de tareas V1 (ejecución) — ~36 salidas

**Método:** 1 tarea=1 salida · ≤300 LOC/archivo · GitHub only · sin pycache en commit

### Bloque 0 — Base (3)
| ID | Tarea |
|----|-------|
| V0-01 | CI `test-wordflow-code-path.yml` (repo raíz) |
| V0-02 | `component_catalog.json` |
| V0-03 | Sync PIPELINE 47 residual table |

### Bloque K — Kernel extension desde zip (7)
| ID | Tarea |
|----|-------|
| VK-01 | Montar package `extensions/wordflow_kernel/` (models, runtime, workflow) sin pycache |
| VK-02 | repo_truth + forensic engine |
| VK-03 | gap_tasks compiler (GAP→Task) |
| VK-04 | memory/checkpoint/ledger/trace hooks |
| VK-05 | resources + validator stubs |
| VK-06 | deploy bridge (dry_run) alineado github_deploy existente |
| VK-07 | tests kernel offline + ficha.v2 |

### Bloque L — Continuous loop (5)
| ID | Tarea |
|----|-------|
| VL-01 | Montar `extensions/maxbry_loop/` desde v2 (engine, gaps, persistence) |
| VL-02 | config/loop.yaml + task.schema |
| VL-03 | Bridge: GoalLock goals_in → loop tasks |
| VL-04 | Bridge: loop gaps → gap_tasks → mission_planner |
| VL-05 | Markers objetivo/tarea (identificadores fijos, sin depender de emoji UI) + tests |

### Bloque F — Forensic capability (3)
| ID | Tarea |
|----|-------|
| VF-01 | RepoTruthPort local + GitHub (list/sha/exists) |
| VF-02 | CrossVerifier IMPLEMENTED/PARTIAL/MISSING |
| VF-03 | `forensic.audit()` → EvidencePacket + recommended_tasks |

### Bloque A — Accounts + Deploy real (4)
| ID | Tarea |
|----|-------|
| VA-01 | AccountRegistry multi-cuenta |
| VA-02 | Workspace→repo→account DENY mismatch |
| VA-03 | GitDataAPIPort real (flag) |
| VA-04 | Tests Fake + dry_run |

### Bloque H — HF resources (4)
| ID | Tarea |
|----|-------|
| VH-01 | ResourceContract |
| VH-02 | SkillLoader IR |
| VH-03 | Dataset modes + Space agents.md parse mínimo |
| VH-04 | Factory + PLAN_ONLY default |

### Bloque Q — ACQUIRE-OS (5)
| ID | Tarea |
|----|-------|
| VQ-01 | acquire_os_core core/verify/build/promote |
| VQ-02 | ficha.v2 + state.schema + config OFF |
| VQ-03 | Recipe Graphify ejemplo |
| VQ-04 | OpenClaw recipe ref (instancia, no motor) |
| VQ-05 | Tests SKIPPED_EXPECTED |

### Bloque D — Docs/README/Gateway (4)
| ID | Tarea |
|----|-------|
| VD-01 | Wire docs_templates + code_path + loop |
| VD-02 | README raíz mapa |
| VD-03 | Gateway mission API |
| VD-04 | Claim V1 OPERATIVO + PIPELINE bitácora commits |

**Total salidas V1:** 3+7+5+3+4+4+5+4 = **35**

---

## D. Residual R2 (NO V1) — programable por otro Grok

| ID | Qué falta | Ancla doc | Prioridad |
|----|-----------|-----------|-----------|
| R2-01 | Fusión loops Minimax/Kimi (enjambre) | fusión docs | Alta producto |
| R2-02 | Router Universal 49 endpoints + UI 5 paneles | resumen router | Alta |
| R2-03 | Osquestador Graphiti/Kanboard/OCR real | osquestador resumen | Alta |
| R2-04 | Memory providers Tencent/Graphiti full + RRF | memory docs | Media |
| R2-05 | 85 contratos L2–L8 | SALIDA4 | Media |
| R2-06 | FETCH=true + HF 1TB storage microkernel | HF arch | Media |
| R2-07 | Tribunal 6 roles en 3 puntos Acquire | A6 | Media |
| R2-08 | Parallel sandbox 50 jobs + SSH bridge | runtime docs | Media |
| R2-09 | MCP HF tools full | HF MCP | Baja |
| R2-10 | Code graph AST multi-lang completo | forensic doc | Baja |
| R2-11 | Post-deploy re-audit automático | forensic ciclo | Media |
| R2-12 | gpg_key_id real → ficha active | enchufe | Alta ops |

Cada R2 item al ejecutar: crear `PIPELINE/R2_<id>.md` + tests + claim.

---

## E. Orden de arranque

```
V0 → VK (kernel zip) → VL (continuous loop) → VF (forensic)
  → VA (accounts/deploy) → VH (HF) → VQ (acquire) → VD (readme/gateway)
```

## F. Microdiagrama V1

```
INPUT/markers → GoalLock → maxbry_loop (continuous)
  → forensic.audit (RepoTruth) → gaps → tasks
  → code_path / dual_compile
  → HF resource resolve (PLAN_ONLY)
  → EnginePort stub
  → Deploy dry_run|GitData
  → Acquire Sub-Sheriff (flag OFF)
  → Evidence+Ledger+Checkpoint
  → Gateway events
```

## G. Confirmaciones

- Loops Kimi/Minimax ≠ continuous loop ≠ code-path wire  
- Zips = fuente a montar; no dejar pycache  
- V1 operativa ≠ universo 100%  
- R2 listado para continuidad en cualquier entorno Grok  
