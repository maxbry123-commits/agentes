# PIPELINE/29 — YAIWES Runtime · Gaps · Plan T1–T40 · Trazabilidad

**Fecha:** 2026-08-14  
**Estado:** PLAN ACTIVO (post Capa Control + Runtime modern ideas)  
**Regla:** 1 tarea = 1 salida · ≤300 LOC/archivo · Fake ports · commit real  
**Techo:** YAIWES (TEAM) brain + Wordflow gobierno + runtime_bus + Parallel FULL

---

## 0 · Arquitectura fijada

```
YAIWES (TEAM kernel)
  └── Wordflow (goals · loops · sheriff · contracts)
        ├── control-layer/          [EXISTE GH]
        ├── runtime_bus/            [T1–T5]
        ├── parallel_runtime/       [T10–T16] N07 FULL
        ├── resource_gate/          [T6–T9]  HF pins
        ├── expert_panel/           [T21–T24]
        ├── packages/ (KER)         [T28]
        └── publish/ github_gw      [T27]
Engines: OpenClaw + Hermes (full) · resto stubs ABI
```

**Capa Control docs** = normas Sheriff / R21–R30 / Mission Contract / evidence×2  
**NO** prohíben Parallel (conflicto "no scheduler" → subordinado a YAIWES).

---

## 1 · Not Now / Deferred Architecture

| Ítem | Decisión |
|------|----------|
| DSL propio (lexer/parser) | ❌ DEFER — YAML/JSON + Schema |
| Auto-recovery 200 estrategias | ❌ DEFER — solo retry/timeout/restore/fallback/reconnect |
| "No crear scheduler" | ❌ RECHAZADO — N07 exige scheduler nativo |
| controller.py god-object | ❌ RECHAZADO — microkernel + extensiones |
| Semantic lock / symbol graph | ❌ DEFER |
| RQL query language | ❌ DEFER |
| Blockchain-like ledger | ❌ DEFER — EventStore append-only sí |
| IVM completa | ❌ DEFER — Micro-IVM / WorkflowPackage Runtime |
| Genome completo + 500 agents | Genome v1 sí · escala = config no hardcode |

---

## 2 · Incorporaciones de alto impacto (filtradas 10×)

### P0 — integrar en waves actuales
1. **Execution Manifest firmado** (pre-dispatch obligatorio)  
2. **Handoff Protocol** (contrato entre engines)  
3. **Task Lease + Heartbeat** (anti tareas zombie)  
4. **Workflow DNA / Genome v1** (objeto inmutable de ejecución)  
5. **Kernel ABI** (= Engine ABI + Scheduler/Sandbox/Event APIs)  
6. **Capability Passport** (permisos/límites por job)  
7. **Runtime Hooks mínimos** (BeforeDispatch / AfterExecution / BeforeCheckpoint)  
8. **State Machine por Task** (CREATED→…→ARCHIVED, no running=True)  
9. **Resource Broker** (motores piden recursos, no abren SSH directo)  
10. **Cost/Budget gate** (tokens·cpu·ram·time antes de allocate)

### P1 — después de Parallel estable
- Capability Negotiation Protocol (CNP)  
- Engine Reputation + Health Monitor  
- Workspace Diff (no copiar workspace completo)  
- Predictive Warm Pool  
- Shared Artifact Cache (por ID)  
- Context Compressor / Incremental Context  
- Runtime Contract Compiler (IR ligero)  
- Decision Trace formal  
- Adaptive Worker Pool  

### P2 — diferido
- Semantic Planner / Symbol Index  
- Sandbox Snapshot clone  
- Event Replay full  
- Capability Evolution auto-score  
- RQL / Reflection API avanzada  

---

## 3 · Gaps actualizados

| ID | Gap | Pri | Wave |
|----|-----|-----|------|
| G1 | Runtime Bus + Engine ABI + Fake engines | P0 | W1 |
| G2 | ArtifactPin + HFPort + Index + ResourceGate | P0 | W2 |
| G3 | Parallel Runtime FULL (scheduler·queue·pool·sandbox·SSH·ckpt·bus) | P0 | W3 |
| G-MAN | **Execution Manifest** firmado pre-dispatch | P0 | W1/W3 |
| G-HO | **Handoff Protocol** contract | P0 | W1 |
| G-LEASE | **Task Lease + Heartbeat** | P0 | W3 |
| G4 | Agent/Capability Registry + Harness | P1 | W6 |
| G5 | Failure contract · EventStore · Mission Contract · R21–R30 | P1 | W4 |
| G-SH | Sheriff 22-check catalog + E00x | P1 | W4 |
| G-EP | Expert Panel multi-API + Decision Gate | P1 | W5 |
| G9 | GitHub Gateway + token_ref | P1 | W6 |
| G-KER | Workflow/Knowledge Package loader | P2 | W7 |
| G-CC | Capability Compiler prototype | P2 | W7 |
| G-GEN | Genome / Workflow DNA v1 | P2 | W7 |
| G-HOOK | Runtime Hooks mínimos | P1 | W3 |
| G-PASS | Capability Passport | P1 | W2/W3 |
| G-SEN | Sentinela (método) | P3 | later |
| G-LG | LangGraph adapter | P3 | later |

---

## 4 · Lista de tareas T1–T40

```
── WAVE-1 · Runtime Bus + Manifest + Handoff ─────────
T1  Engine ABI (execute/stream/checkpoint/cancel/health/negotiate?)
T2  RuntimeBus + no-bypass policy
T3  OpenClawAdapter + HermesAdapter (full mínimo)
T4  Stubs engines (Codex/Cline/Aider/OpenHands/…) mismo ABI
T5  Execution Manifest schema + signer + pre-dispatch gate
T6  Handoff Package schema + validate/reject/replan
T7  Tests FakeEngine + Manifest DENY sin firma

── WAVE-2 · Resource Layer + Passport ────────────────
T8  ArtifactPin schema + Index (skill/dataset/adapter)
T9  HFPort + local cache + reinstall plan
T10 ResourceGate + MandatoryResourceSet
T11 Capability Passport (limits/ttl/tools) emit+validate
T12 Resource Broker (request ssh/docker/gpu → grant/deny)
T13 Tests pin mismatch / passport expired → DENY

── WAVE-3 · Parallel FULL N07 ────────────────────────
T14 Scheduler + DAG deps + priority queue
T15 Worker pool reutilizable + adaptive basic
T16 Sandbox persistente (workspace/state/checkpoints)
T17 SSH adapter + reconnect
T18 Task Lease + Heartbeat + reclaim expired
T19 Checkpoint/restore + backpressure
T20 Event bus mínimo + Decision Trace append
T21 Runtime Hooks: BeforeDispatch/AfterExecution/BeforeCheckpoint
T22 State Machine Task (CREATED…ARCHIVED) enforced
T23 Budget gate (tokens/cpu/ram/time) pre-allocate
T24 Tests: 10+ jobs, lease expire, restore, cancel, manifest required

── WAVE-4 · Sheriff + Wordflow depth ─────────────────
T25 Sheriff catalog 22 checks + E00x + output schema
T26 Mission Contract inmutable + R21–R30 policy
T27 Failure contract + Evidence ≥2 sources
T28 EventStore / Task Journal append-only

── WAVE-5 · Expert Panel ─────────────────────────────
T29 Opinion schema + Decision Gate
T30 Multi-API providers (≥3) parallel eval
T31 Consensus engine basic
T32 Triggers: architecture / stuck / new doc

── WAVE-6 · Registry + Publish ───────────────────────
T33 Capability/Engine Registry + fingerprint hash
T34 Harness contract install/verify/test/rollback/report
T35 GitHub Gateway (token_ref, tree/commit, idempotent)

── WAVE-7 · KER + Genome + Compiler proto ────────────
T36 WorkflowPackage + KnowledgePackage loader
T37 Capability compile prototype (normalize scores)
T38 Genome / Workflow DNA v1 schema + attach to run

── WAVE-8 · Cierre ───────────────────────────────────
T39 PIPELINE update + claim DSL CHAT_A
T40 CI workflows por extensión + evidencia runs
```

**Total:** 40 tareas · 1 salida cada una · orden por dependencias.

---

## 5 · Trazabilidad documentos → tareas

| Documento / fuente | Tareas |
|--------------------|--------|
| SALIDA_1_CAPA_CONTROL P1–P3 | T25–T28, Mission, R21–R30, evidence×2 |
| YAIWES final + ley OC/Hermes | T1–T4 |
| Parallel / respuesta P2 | T14–T24 |
| HF / DESPLIEGUE / SE | T8–T13, T35 |
| Expert Panel docs | T29–T32 |
| KER extensión | T36 |
| Runtime modern ideas (WPE/Handoff/Manifest/Lease/DNA/Hooks/Passport) | T5–T6, T11–T12, T18, T21–T22, T38 |
| control-layer GH existente | base Sheriff/Contract Router — no rehacer |
| Deferred list (DSL/200 recovery/god controller) | explícito §1 |

---

## 6 · Simulaciones (resumen)

**SIM-A** skill install: Manifest firmado → Passport → ResourceGate pin → Bus.dispatch(OC) → evidence×2 → CERTIFY.  
Sin Manifest → DENY antes de engine.

**SIM-B** 40 jobs + 1 SSH fail: Lease expire → reclaim → restore checkpoint → Handoff a fallback engine → continue.  
Sin Lease → tarea zombie.

**SIM-C** doc arquitectura: Input Contract → Expert Panel multi-API → Decision Gate → Manifest → Parallel allocate.  
Sin Gate → merge sin consenso (prohibido).

---

## 7 · Criterio de cierre por wave

| Wave | Cierre |
|------|--------|
| W1 | ABI + Manifest DENY test + Handoff reject path |
| W2 | Pin mismatch DENY + Passport TTL |
| W3 | 10 jobs + lease reclaim + restore + hooks fired |
| W4 | Sheriff REJECT + evidence rule |
| W5 | 3 APIs + Gate APPROVE/REJECT |
| W6 | Publish idempotent + registry fingerprint |
| W7 | Package load + DNA hash stable |
| W8 | Claim DSL + CI green |

---

## 8 · Anti-sobreingeniería (ley)

- No Lexer/Parser propio.  
- No 200 recovery strategies.  
- No god controller.py.  
- No motores acoplados al kernel.  
- No workflows hardcode en Python (declarativos).  
- ≤300 LOC/archivo.  
- 1 tarea = 1 commit.  
- Fake ports obligatorios en tests.

---

**SIGUIENTE PUERTA:** Ok → **T1 Engine ABI**  
O reorder si Director mueve Expert Panel antes de Parallel.
