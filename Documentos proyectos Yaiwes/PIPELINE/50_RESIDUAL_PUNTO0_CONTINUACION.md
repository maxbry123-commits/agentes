# PIPELINE 50 — Residual Punto 0 (continuación post V1)

**Repo:** https://github.com/maxbry123-commits/agentes  
**Regla:** GitHub = única fuente de verdad. Prohibido usar sandbox como almacenamiento de código/claims.  
**Estado V1:** núcleo operativo (kernel + loop + gateway + accounts + HF PLAN_ONLY + acquire OFF + slots Router/Memory/UI).  
**Este documento:** todo lo pendiente para programar en la siguiente ronda, con trazabilidad y criterios de cierre.

---

## 0. Cómo retomar (cualquier instancia Grok)

1. Leer este archivo completo.  
2. Leer `extensions/wordflow_kernel/README_V1.md`.  
3. Leer `PIPELINE/49_V1_CIERRE_README_Y_RESIDUAL.md`.  
4. No reimplementar lo ya montado: verificar paths en árbol `extensions/` y `control-layer/`.  
5. Una tarea = una salida; commit real; claim con path + sha si se audita.

---

## 1. Ya entregado (NO rehacer)

| Área | Path principal |
|------|----------------|
| IntelligenceGateway + RouterHTTP + Mock | `extensions/wordflow_kernel/gateway/` |
| EnginePort OpenClaw/Hermes stubs | `extensions/wordflow_kernel/engines/` |
| Forensic + RepoTruth + CrossVerifier + forensic_api | `extensions/wordflow_kernel/{forensic,repo_truth,crosscheck,forensic_api}.py` |
| Models/runtime/workflow/ledger/trace/checkpoint/memory | `extensions/wordflow_kernel/` |
| 12-stage loop | `extensions/wordflow_kernel/stages/` |
| Goal/gap bridges | `extensions/wordflow_kernel/bridge/` |
| Continuous loop maxbry_v2 | `extensions/maxbry_loop/` |
| AccountRegistry + Resolver | `extensions/wordflow/accounts/` |
| GitDataAPIPort Fake/Real | `extensions/github_deploy/git_data_port.py` |
| HF ResourceContract + Skill/Dataset/Space + Factory | `extensions/wordflow_kernel/resources/` |
| Acquire Engine OFF + OpenClaw recipe example | `control-layer/subsheriffs/acquire_os/` |
| Router slot + Memory slot + UI gateway | `router_slot/` `memory_slot/` `ui_gateway/` |
| README connect | `extensions/wordflow_kernel/README_V1.md` |

---

## 2. Residual programable (R2 / siguiente sprint)

### R2-01 Kimi / Minimax fusion loops
- **Qué:** plugin extensión kernel con contratos + handlers; **no** sustituye maxbry_loop.  
- **Docs origen:** fusiones Minimax/Kimi, NCT loops (Director).  
- **Criterio cierre:** `extensions/wordflow_kernel/plugins/kimi_minimax/` + ficha.v2 + tests offline; activación por config.  
- **Tareas sugeridas:** KM-01 scaffold · KM-02 stage map · KM-03 tests · KM-04 PIPELINE claim.

### R2-02 Fetch real HF / GitHub
- **Qué:** ejecutar DatasetLoader/Acquire cuando `FETCH_ENABLED=1` + policy + credential_ref.  
- **Hoy:** PLAN_ONLY.  
- **Criterio:** FakePort tests + un camino real detrás de flag; sin token en journal.

### R2-03 CI suite completa
- **Qué:** workflows que ejecuten tests de wordflow_kernel, maxbry_loop, github_deploy, accounts.  
- **Hoy:** workflows parciales históricos.  
- **Criterio:** Actions verde reproducible + link run_id en claim.

### R2-04 Acquire ON + OpenClaw binario
- **Qué:** con `ACQUIRE_OS_ENABLED=true` y recipe pin SHA; verificar checksum; no promover si FAILED.  
- **Hoy:** config OFF + recipe example.  
- **Criterio:** mission state.json + manifest sin secretos.

### R2-05 Router / Osquestador real
- **Qué:** servicio FastAPI Router Universal + Memory Orchestrator (Tencent/Graphiti/Graphify providers).  
- **Hoy:** adapters HTTP + local memory.  
- **Criterio:** contrato `/v1/route` documentado; Wordflow solo cliente.

### R2-06 UI host real
- **Qué:** montar `UIGatewayPlugin` en OpenClaw webui o chat host.  
- **Hoy:** stub ACK.  
- **Criterio:** session → GoalLock → loop arranque demostrado.

### R2-07 Code-path C-01…C-20 hardening
- **Qué:** alinear diagrama auditado (~70–75%) al 100% con Input Sentinel, RepoTruthPort en code_path, C10 deploy post-promote.  
- **Docs:** salidas code-path / NCT / deploy Wordflow.  
- **Criterio:** lista R0–R3 de auditoría ingenieros cerrada item a item.

### R2-08 Project documents native templates (9+)
- **Qué:** plantillas nativas proyecto (PROFILE, ARCHITECTURE, WORKFLOW, …) generables por Wordflow.  
- **Hoy:** specs en historial; verificar `extensions/project_bootstrap` y docs PIPELINE 12/13.  
- **Criterio:** generación determinista desde InputBlock + tests.

---

## 3. Invariantes (no romper)

1. Loop **nunca** llama OpenAI/Anthropic directo → solo IntelligenceGateway.  
2. `llm_control: DENY` en paths kernel deterministas.  
3. Token solo `credential_ref` / env; no body workflow.  
4. Deploy: no force_push; expected_head conflict → HOLD.  
5. SKIPPED_EXPECTED ≠ PASS.  
6. Promote bloqueado si hay FAILED.  
7. Claim COMPLETED requiere existencia material en GitHub.

---

## 4. Orden recomendado próxima ronda

```text
R2-03 CI
  → R2-07 code-path harden
  → R2-02 fetch flags
  → R2-05 router service (si hay host)
  → R2-01 kimi plugin
  → R2-04 acquire enable (Director)
  → R2-06 UI host
  → R2-08 templates audit
```

---

## 5. Enlaces canónicos

- Repo: https://github.com/maxbry123-commits/agentes  
- Kernel: https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel  
- Loop: https://github.com/maxbry123-commits/agentes/tree/main/extensions/maxbry_loop  
- PIPELINE dir: https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE  

**Fin V1 lista tareas operativas 38/38.** Residual queda en este punto 0 para auditoría y continuación.
