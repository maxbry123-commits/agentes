# PIPELINE 46 — Opción 1 OPERATIVA (6 puntos) + residual audit

**Fecha:** 2026-08-15  
**Repo:** maxbry123-commits/agentes  
**Decisión:** Opción 1 = Wordflow usable esta semana con 6 puntos operativos; mejoras profundas en ronda 2.  
**Fuente de verdad:** GitHub only · LLM_CONTROL=DENY en path determinista  
**Claim:** OPERATIVO_6PUNTOS (no claim “universo documental 100%”)

---

## 0. Forense code-path y loops (estado real)

| Componente | Estado GitHub | Nota |
|------------|---------------|------|
| C-01…C-31 code-path | MATERIALIZADO | goal_lock, dual_compiler, deploy FakePort, smoke C-31 |
| Project docs templates (C-11) | MATERIALIZADO | 12 plantillas |
| cognitive_loop / main pieces | PARCIAL | wire existe; no es fusión Minimax/Kimi completa |
| Loops F4 main/retry/recovery/evolution/watchdog | **NO cerrado** | Solo residual; slots pendientes en esta ola |
| ACQUIRE-OS genérico 28 nodos | **NO en repo** | Código en attachments Director; montar en O1 |
| Router Universal / Osquestador | **NO montados** | Spec; extensión kernel los recibe por contrato |
| Multi-account GitHub | **NO** | CredentialStore simple; falta AccountRegistry |
| HF Skill/Dataset/Space resolvers | PARCIAL | hf_resolver PLAN_ONLY; falta ResourceContract + modes |
| Engine adapters OpenClaw/Hermes | **NO** | Solo contratos anotados |
| Gateway WebUI plugin | **NO** | Pendiente |
| CI suite unificada code-path | **NO** | Workflows parciales |

---

## 1. Los 6 puntos operativos (definición de DONE)

### Punto 1 — Code docs → deploy + project docs + loop de trabajo
**DONE si:**  
- Input docs → quality_bar → GoalLock → analyze → dual_compile → claim → deploy contract (dry-run o real según flag)  
- generate_project_docs (12) invocable  
- Loop de misión: stages con MemoryMiddleware hooks + checkpoint (mínimo)  
- README documenta el flujo  

### Punto 2 — GitHub multi-cuenta + HF nativo
**DONE si:**  
- AccountRegistry (account_id → credential_ref + allowed_repos + policy)  
- Workspace → repo → account_id → DENY si mismatch  
- HF ResourceContract + modes: REMOTE | CACHE | SNAPSHOT | STREAM | FILE  
- Skill IR (SKILL.md → contract, no ejecutar MD crudo)  
- Space agents.md → SpaceContract (parse mínimo)  
- Fetch real solo si `POST_WORDFLOW_FETCH_ENABLED` + policy  

### Punto 3 — Download agentes/software (ACQUIRE-OS)
**DONE si:**  
- `control-layer/subsheriffs/acquire_os/` con core/verify/build/promote + ficha.v2  
- Recipe-driven; SKIPPED_EXPECTED; no token en journal  
- OpenClaw como **instancia Recipe**, no motor  
- Registrado Sub-Sheriff testing  

### Punto 4 — README + PIPELINE + auto-conexión componentes
**DONE si:**  
- README raíz: mapa paths + cómo montar extensión + cómo añadir motor  
- PIPELINE 46+ actualizado  
- Component catalog JSON legible por Wordflow (id, path, ficha, capabilities)  

### Punto 5 — Extensión kernel Router + Osquestador + engines
**DONE si:**  
- `extensions/wordflow_kernel/` manifest + adapter + contracts  
- Stubs tipados: router.resolve, memory.recall/capture, audit.verify  
- EngineAdapter registry (openclaw/hermes placeholders)  
- ExecutionContext viaja por stages  

### Punto 6 — Plugin Gateway WebUI / OpenClaw UI
**DONE si:**  
- Gateway HTTP mínimo: mission.submit / state / events / approve / cancel  
- Eventos con mission_id + checkpoint  
- Sin que UI controle el kernel  

### Punto 0 — PIPELINE auditoría residual
**DONE si:** este documento + lista de tareas residual R2 con anclas de doc  

---

## 2. Trazabilidad documental (anclas)

| Doc / origen | Ancla en plan |
|---------------|---------------|
| A1–A12 ACQUIRE-OS, core/verify/build/promote | Punto 3, tareas AQ-* |
| OpenClaw acquire 40 nodos (instancia) | AQ-OC-* |
| Enchufe Universal v2 / ficha.v2 | KER-*, AQ-* |
| DESPLIEGUE determinista / github_publish | DEP-* |
| Router Universal resumen | KER-RTR-* |
| Osquestador Auditor/Memoria | KER-MEM-* |
| HF Skills/Dataset/Space/MCP notes | HF-* |
| Memory transversal + AccountRegistry | MEM-*, ACC-* |
| Code path C-01…C-31 / PIPELINE 45 | BASE |
| Project docs native 12 | DOC-* |

---

## 3. Lista de tareas Opción 1 operativa (orden de ejecución)

**Regla:** 1 tarea = 1 salida · ≤300 LOC por archivo nuevo · commit+push · claim path+sha  
**Total estimado:** 28 salidas

### Bloque 0 — Auditoría y CI base (3)
| ID | Tarea | Path | Doc ancla |
|----|-------|------|-----------|
| O0-01 | CI workflow test-wordflow-code-path | `.github/workflows/test-wordflow-code-path.yml` | PIPELINE 45 |
| O0-02 | Component catalog JSON | `extensions/wordflow/component_catalog.json` | Punto 4 |
| O0-03 | Actualizar PIPELINE 46 residual R2 table | este file | Punto 0 |

### Bloque 1 — Kernel Extension Runtime (6)
| ID | Tarea | Path |
|----|-------|------|
| KER-01 | manifest + ficha.v2 wordflow_kernel | `extensions/wordflow_kernel/` |
| KER-02 | ExecutionContext dataclass | `.../runtime/execution_context.py` |
| KER-03 | StageRunner hooks memory/audit/trace | `.../runtime/stage_runner.py` |
| KER-04 | Contracts: RouterPort MemoryPort AuditPort EnginePort | `.../contracts/` |
| KER-05 | Engine registry + stub openclaw/hermes | `.../engines/` |
| KER-06 | Tests kernel runtime offline | `.../tests/` |

### Bloque 2 — Cuentas GitHub + Deploy (4)
| ID | Tarea | Path |
|----|-------|------|
| ACC-01 | AccountRegistry multi-cuenta | `extensions/wordflow/accounts/registry.py` |
| ACC-02 | Workspace→repo→account resolve + DENY mismatch | `.../accounts/resolver.py` |
| DEP-01 | GitDataAPIPort real detrás Deployer (flag dry_run) | `extensions/github_deploy/git_data_port.py` |
| DEP-02 | Wire token_ref + account_id en deploy contract | deployer + tests |

### Bloque 3 — HF Resource Runtime (5)
| ID | Tarea | Path |
|----|-------|------|
| HF-01 | ResourceContract frozen | `extensions/wordflow_kernel/resources/contract.py` |
| HF-02 | SkillLoader SKILL.md → IR contract | `.../resources/skill_loader.py` |
| HF-03 | DatasetLoader modes file/snapshot/stream plan | `.../resources/dataset_loader.py` |
| HF-04 | SpaceAgentsLoader parse agents.md mínimo | `.../resources/space_loader.py` |
| HF-05 | AdapterFactory + registry + tests | `.../resources/factory.py` |

### Bloque 4 — ACQUIRE-OS montaje (5)
| ID | Tarea | Path |
|----|-------|------|
| AQ-01 | Package acquire_os_core core/verify/build/promote | `control-layer/subsheriffs/acquire_os/` |
| AQ-02 | ficha.v2 + state.schema + config flag OFF | same |
| AQ-03 | Recipe ejemplo Graphify + OpenClaw recipe ref | `recipes/` |
| AQ-04 | Tests offline SKIPPED_EXPECTED paths | tests |
| AQ-05 | PIPELINE note Sub-Sheriff testing | PIPELINE |

### Bloque 5 — Docs loop + project + README (3)
| ID | Tarea | Path |
|----|-------|------|
| DOC-01 | Mission loop runner (stages + checkpoint mínimo) | `extensions/wordflow/engine/mission_loop.py` |
| DOC-02 | Wire docs_templates → code_path_runner | integration |
| DOC-03 | README raíz mapa + cómo conectar motor/HF/Acquire | `README.md` |

### Bloque 6 — Gateway plugin UI (2)
| ID | Tarea | Path |
|----|-------|------|
| GW-01 | Gateway API mission submit/state/events/approve | `extensions/wordflow_kernel/gateway/` |
| GW-02 | README gateway + OpenClaw UI event schema | docs |

---

## 4. Residual R2 (NO en Opción 1 — ronda 2)

| ID | Item | Doc ancla |
|----|------|-----------|
| R2-01 | Loops F4 Minimax/Kimi full | fusión docs |
| R2-02 | Router Universal completo 49 endpoints | resumen router |
| R2-03 | Osquestador Graphiti/Kanboard real | osquestador resumen |
| R2-04 | Memory providers Tencent/Graphiti full | memory docs |
| R2-05 | 85 contratos L2–L8 | SALIDA4 |
| R2-06 | Fetch flag ON + microkernel install HF 1TB | HF arch |
| R2-07 | Tribunal 6 roles full en 3 puntos Acquire | A6 |
| R2-08 | MCP server HF tools full | HF MCP |

---

## 5. Microdiagrama operativo objetivo Opción 1

```
INPUT → quality_bar → GoalLock → ExecutionContext
  → MemoryPort.recall (stub|store)
  → analyze/compile/docs
  → ResourceResolver (HF contract PLAN|fetch if flag)
  → EnginePort (stub openclaw/hermes)
  → Deploy (dry_run|GitDataAPI if authorize)
  → Acquire Sub-Sheriff (testing flag)
  → Evidence+Claim → Checkpoint
  → Gateway events (UI)
```

---

## 6. Criterio “100% operativo Opción 1”

- Los 6 puntos tienen código en GitHub + tests offline + README  
- Flags: ACQUIRE_OS_ENABLED=false, dry_run_default=true, FETCH=false por defecto  
- Director puede: correr code-path, generar docs proyecto, dry-run deploy, registrar ficha Acquire testing, ver gateway events  
- Residual R2 explícito en este PIPELINE  

**Prohibido claim:** “Wordflow universo 100%” o “Router/Osquestador full production”.
