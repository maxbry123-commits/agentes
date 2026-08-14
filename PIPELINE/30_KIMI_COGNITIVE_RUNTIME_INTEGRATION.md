# PIPELINE/30 — Kimi Method · Cognitive Runtime · Push/Ping · Integración

**Fecha:** 2026-08-14  
**Estado:** PLAN ACTIVO (supersede parcial de huecos de 29; 29 sigue válido para waves)  
**Regla:** 1 tarea = 1 salida · ≤300 LOC/archivo · Fake ports · cada 3 tareas → auditoría PIPELINE  
**Techo:** YAIWES brain + Wordflow gobierno · LLM = coprocesor (5–30%) · Runtime determinista (70–95%)

---

## 0 · Confirmación de integración

| Fuente | Integrado en plan | Dónde |
|--------|-------------------|-------|
| PIPELINE 29 (T1–T40) | Sí base | waves W1–W8 |
| Capa Control Sheriff/R21/Mission | Sí | W4 |
| Execution Manifest + Handoff | Sí | T5–T6 |
| Resource Trace / Gate / HF | Sí | W2 |
| Parallel FULL N07 | Sí | W3 |
| **5 docs Kimi/Cognitive (este input)** | **Sí — este archivo** | WAVE-0 + ampliaciones |
| Push/Ping + Focus + bitácora | **Sí — nuevo P0** | T0e–T0h |
| Goal Lock | Sí (= Mission Contract reforzado) | T0i + T26 |
| Cognitive Register File | Sí — nuevo | T0j |
| Task Classifier pre-LLM | Sí — nuevo | T0k |
| Reasoning Ledger / Decision Memory | Sí — nuevo | T0l |
| Triple Runtime (Det/Cog/Conv) | Diseño — implementación por fases | §3 |
| Cada 3 tareas → audit PIPELINE | **Regla operativa** | §8 |

**Ubicaciones GH:**
- `PIPELINE/29_YAIWES_RUNTIME_GAPS_Y_PLAN.md` (commit d7827ed5)
- `PIPELINE/30_KIMI_COGNITIVE_RUNTIME_INTEGRATION.md` (este)

---

## 1 · Auditoría 1:1 de los 5 documentos de entrada

### Doc A — Investigación 10 pasadas Kimi K3
| Pasada | Idea | Decisión YAIWES |
|--------|------|-----------------|
| 1 Preserved thinking | Reasoning Ledger | **P0** T0l |
| 2 Reasoning effort | Budget Compiler low/high/max | **P0** en Manifest deliberation_level |
| 3 Long horizon | Context Segmentation no 1M tokens ciegos | **P1** Progressive Context |
| 4 Native agent | Agent Runtime ≠ LLM | **Ya** (YAIWES) |
| 5 Tool calls | Tool Ledger + replay | **P1** Tool Contract |
| 6 Context cache | Context Cache Compiler | **P1** |
| 7 Multimodal | Todo es Resource | **Ya** ResourceGate |
| 8 MoE experts | Workflow Expert Router (pocos engines) | **P1** CNP |
| 9 Coding harness | Execution Harness | **Ya** N07 + hooks |
| 10 Preserved+ | Decision+Evidence+Alt+Refute | **P0** Decision Memory |

### Doc B — Método Kimi → Runtime
Decision Pipeline, Execution Budget, Knowledge Layers, Episodes, Tool Contracts, Expert Market, Evidence Graph, Handoff Compiler, Planner Compiler, WOS 5 kernels → **filtrado**: Handoff/Planner/Decision Memory P0; Expert Market P1; WOS = mapa de waves no monólito.

### Doc C — Runtime Cognitivo Determinista
**Goal Lock, Push/Ping, Focus Monitor, Objective Echo, Literal Mode, Watchdog, Hallucination Detector, Confidence Gate, CLK** → **P0** Goal Lock + Push/Ping + Focus + Literal; resto P1/P2.

### Doc D — Cognitive OS / Register File
Tag Engine, KG, Context Compiler, **Cognitive Register File (16 regs)**, Memory Layers → **P0 Register File**; Tag/KG P1.

### Doc E — Triple Runtime + pre-LLM gate
Task Classifier, Deterministic-first, Native engines (Git/SSH/…), Decision Gate before LLM, Triple Runtime → **P0 Classifier + Gate**; native engines por adaptadores existentes; Triple = arquitectura objetivo.

---

## 2 · Piezas P0 nuevas (antes no explícitas)

### 2.1 Push/Ping + Focus + Bitácora persistente
```
loop (supervisor, no LLM):
  cada N segundos O post-tool:
    PING → leer GoalLock, state, lease, checkpoint, resource_trace
    si desviación (Focus score < umbral) → STOP → REPLAN → nuevo Manifest
    escribir BITACORA append-only (EventStore)
```
No depende del modelo. Evita alucinación por pérdida de objetivo.

### 2.2 Goal Lock (inmutable)
Objeto fuera del contexto LLM. Cada llamada: GoalLock → Prompt Builder → LLM → Goal Validator. Si viola → descartar salida.

### 2.3 Cognitive Register File (16)
R0 objetivo · R1 paso · R2 éxito · R3 constraints · R4 riesgos · R5 recursos · R6 tools · R7 state · R8 checkpoint · R9 evidencias · R10 hipótesis · R11 refutación · R12 next · R13 quality · R14 confidence · R15 exit_condition  
Se recargan en **cada** invocación de engine. El modelo no “recuerda”; el runtime inyecta.

### 2.4 Task Classifier + Decision Gate pre-LLM
```
Request → Classifier
  DETERMINISTIC | SEARCH | ANALYSIS | REASONING | HYBRID
Si DETERMINISTIC/SEARCH resoluble por reglas/índice/git/ssh → NO LLM
Si REASONING/HYBRID → Cognitive Runtime
```

### 2.5 Reasoning Ledger / Decision Memory
No guardar solo texto final. Frame: goal, evidence, decision, alternatives, refutations, tools, artifacts, confidence, checkpoint_id.

### 2.6 Input Gateway (WAVE-0) — ya propuesto
Audit literal → Analyze → Structured Questions (≤12) → Goals compile → Resource Trace → Manifest.

---

## 3 · Arquitectura objetivo (Triple Runtime)

```
┌─ Runtime Determinista ─┐  reglas, DAG, git, ssh, índices, templates
├─ Runtime Cognitivo ────┤  LLM solo si Gate dice REASONING
└─ Runtime Conversacional┘  progreso/estado al usuario (sin esperar LLM)
         ▲
    Wordflow + YAIWES kernel (GoalLock, Registers, Push/Ping, Manifest)
```

LLM = coprocesor. No orquestador.

---

## 4 · Lista de tareas actualizada T0–T48

```
── WAVE-0 · Input Gateway + Cognitive anchors ────────
T0a  input_contract.schema + Input Compiler (literal)
T0b  Structured Questions Engine Q01–Q12 + resolve gate
T0c  Resource Trace builder (inventory pre-plan)
T0d  Pre-Execution Protocol orchestrator
T0e  GoalLock schema + validator (immutable)
T0f  Push/Ping supervisor loop (interval + post-tool)
T0g  Focus Monitor (score goal vs step vs output)
T0h  Bitácora / EventStore append-only work journal
T0i  Objective Echo injector (pre-engine call)
T0j  Cognitive Register File (R0–R15) load/store
T0k  Task Classifier + Decision Gate pre-LLM
T0l  Reasoning Ledger / Decision Memory frames
T0m  Tests: literal mode, goal violation discard, ping reclaim

── WAVE-1 · Runtime Bus + Manifest + Handoff ─────────
T1   Engine ABI
T2   RuntimeBus no-bypass
T3   OpenClaw + Hermes adapters
T4   Stubs engines
T5   Execution Manifest sign + pre-dispatch gate
T6   Handoff Package compile/validate/reject
T7   Tests FakeEngine + Manifest DENY

── WAVE-2 · Resource + Passport + Broker ─────────────
T8–T13  (igual PIPELINE 29)

── WAVE-3 · Parallel FULL N07 ────────────────────────
T14–T24 (igual 29; T18 Lease integra con Push/Ping)

── WAVE-4 · Sheriff + Mission + Evidence ─────────────
T25–T28 (Mission = GoalLock enforcement)

── WAVE-5 · Expert Panel ─────────────────────────────
T29–T32

── WAVE-6 · Registry + Publish ───────────────────────
T33–T35

── WAVE-7 · KER + DNA + CC proto ─────────────────────
T36–T38

── WAVE-8 · Cierre + regla cada-3 ────────────────────
T39  PIPELINE sync
T40  CI
T41  Tool Contract schema (input/output/permissions/timeout/rollback)
T42  deliberation_level budget in Manifest (low/high/max)
T43  Episode/Chapter/Frame session structure
T44  Hallucination Detector stub (claim→evidence required)
T45  Confidence Gate (threshold policy)
T46  Literal Mode policy (temperature min, no infer)
T47  Native response templates (status without LLM)
T48  Claim DSL + evidencia auditoría Grok engineers
```

**Total:** 48 tareas (T0a–T0m + T1–T48).  
**Regla operativa:** cada 3 tareas COMPLETED → re-leer PIPELINE 29+30 + bitácora; si gap nuevo → actualizar plan antes de seguir.

---

## 5 · Trazabilidad documentos → tareas (para auditoría ingenieros)

| Documento / input | Tareas |
|-------------------|--------|
| PIPELINE 29 | T1–T40 base |
| SALIDA_1_CAPA_CONTROL | T25–T28, GoalLock |
| Doc A Kimi 10 pasadas | T0l, T42, T6, T41 |
| Doc B Runtime method | T0d, T6, T43, Decision pipeline |
| Doc C CLK / Push-Ping | **T0e–T0i**, T0g, T44–T46 |
| Doc D Register File | **T0j**, memory layers P1 |
| Doc E Triple + Classifier | **T0k**, T47, native engines via adapters |
| HF / DESPLIEGUE | T8–T13, T35 |
| Not Now (DSL/200 recovery/god controller) | sigue §1 de PIPELINE 29 |

---

## 6 · Not Now (refuerzo)

- Lexer/parser DSL propio completo  
- 200 recovery strategies  
- MoE del modelo  
- 1M context ciego  
- Expert auction completa v1  
- Knowledge Graph full v1  
- Background reasoning async complejo v1  

---

## 7 · Criterio de no-alucinación / foco

1. GoalLock inmutable fuera del LLM  
2. Registers R0–R15 inyectados cada llamada  
3. Push/Ping + Focus Monitor sin LLM  
4. Bitácora append-only (no reescribir historia)  
5. Manifest firmado antes de DISPATCH  
6. Decision Memory con evidence obligatoria cuando policy lo exige  
7. Classifier: si es determinista → no LLM  
8. Cada 3 tareas: auditoría PIPELINE anti-desvío  

---

## 8 · Regla operativa cada 3 tareas

```
ON task_count % 3 == 0:
  read PIPELINE/29 + PIPELINE/30 + BITACORA
  diff plan vs reality
  if new_gap: append gap + reorder OR escalate Director
  if incomplete_code: no avanzar wave
  write checkpoint en PIPELINE
```

---

**SIGUIENTE:** Ok → **T0a Input Compiler** (o T0e GoalLock si priorizas anclas cognitivas primero).
