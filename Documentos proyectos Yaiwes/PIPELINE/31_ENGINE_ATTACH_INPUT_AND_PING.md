# PIPELINE/31 — OpenClaw + Hermes en Input Gateway y Push/Ping

**Fecha:** 2026-08-14  
**Estado:** PLAN INTEGRADO (no sustituye 29/30; los amplía)  
**Decisión Director:** motores OpenClaw/Hermes se usan en (1) inicio planificación objetivo/tareas y (2) cadena Push/Ping para contexto/memoria persistente vía Hermes.

---

## 1 · Análisis (qué sí / qué no)

### Qué pidió el Director
1. En el **primer inicio** de YAIWES (input → planificación → objetivo → definición de tareas) se pueden usar motores **OpenClaw** y **Hermes**.
2. En la cadena **Push/Ping** se puede volver a usar **Hermes** para mantener contexto y memoria persistente.

### Qué NO debe pasar (anti-alucinación)
| Prohibido | Razón |
|-----------|--------|
| Que OpenClaw/Hermes reemplacen T0a–T0d | T0a–T0d son 0% LLM y ya están cerrados |
| Que el Ping lo ejecute el LLM | Ping es supervisor determinista (T0f) |
| Que Hermes reescriba GoalLock | GoalLock es inmutable (T0e) |
| Que el modelo orqueste el Wordflow | YAIWES/Wordflow gobiernan; engines ejecutan |
| Llamar engines sin Task Classifier | T0k decide DETERMINISTIC vs REASONING |

### Principio
```
Deterministic core (Input/Questions/Goals/Lock/Ping)
        │
        ├── siempre corre
        │
        └── Engine ports (OpenClaw / Hermes)
              solo cuando Classifier = REASONING|HYBRID|MEMORY_REFRESH
              salida = PROPOSAL o MEMORY_PACK, nunca hechos sin gate
```

---

## 2 · Punto A — Input Gateway (planificación inicial)

```
raw input
  → T0a InputCompiler          (literal, 0% LLM)
  → T0b StructuredQuestions    (form Q01–Q12)
  → si form INCOMPLETE o policy planning_enrich=true:
        T0k Classifier
          DETERMINISTIC → no engine; Director completa Q o defaults policy
          REASONING|HYBRID → PlanningPort
              ├─ OpenClaw engine: desglose tareas / arquitectura propuesta
              └─ Hermes engine: contexto proyecto / memoria previa
        → PlanningProposal (schema)
        → merge SOLO como respuestas candidatas a Q* (status=PROPOSED)
        → resolve_gate sigue exigiendo ANSWERED (auto o Director)
  → T0d GoalsCompiler          (solo form resolved)
  → T0e GoalLock               (inmutable desde goals COMPILED)
```

**Contrato PlanningProposal (mínimo):**
```yaml
planning_proposal:
  schema_version: "1.0"
  contract_id: str
  engine_id: openclaw|hermes|both
  proposed_answers:   # keys subset Q01–Q12
    Q01_objective: str?
    Q02_expected_result: str?
  task_breakdown: [ {id, title, depends_on[]} ]
  confidence: 0.0–1.0
  evidence_refs: []
  status: PROPOSAL   # nunca COMPILED
```

**Reglas:**
- Proposal no marca resolved=true.
- Policy auto_accept_proposals: false por defecto (Director o council).
- Si auto_accept_proposals: true solo campos no-required de bajo riesgo.

---

## 3 · Punto B — Push/Ping + Hermes memoria

```
T0f Push/Ping (determinista, 15s + post-tool)
  → lee GoalLock, state, lease, checkpoint, resource_trace
  → FocusMonitor score
  → escribe bitácora append-only
  → SI focus degradado OR episode_boundary OR memory_refresh_due:
        MemoryPort(Hermes)
          input: GoalLock id + checkpoint + last N bitácora hashes
          output: MemoryPack (facts, open_loops, constraints_echo)
          → inyecta en Cognitive Register File (R5/R7/R8/R9)
          → NUNCA modifica GoalLock ni goals_hash
  → SI focus < umbral: STOP → REPLAN (nuevo ciclo Input/Manifest)
```

**Hermes aquí = Memory Adapter**, no orquestador.
OpenClaw no es obligatorio en cada ping (coste); solo en REPLAN/planning.

**MemoryPack mínimo:**
```yaml
memory_pack:
  schema_version: "1.0"
  goal_lock_id: str
  engine_id: hermes
  facts: [str]
  open_loops: [str]
  constraints_echo: [str]
  checkpoint_ref: str
  pack_hash: str
```

---

## 4 · Microdiagrama horizontal

```
Input → Compiler0% → Questions → [Classifier] → (OpenClaw|Hermes PlanningPort)? → Goals0% → GoalLock
                                                                                        |
Dispatch ← Manifest ← Registers(R0–R15) ←──────────────────────────────────────────────┘
         |
         v
    Workers/Engines
         |
    Push/Ping 15s → Focus → Bitácora
         |
         └─(degraded?)─→ Hermes MemoryPort → Registers refresh → continue|REPLAN
```

---

## 5 · Tareas nuevas / ajustes

| ID | Entrega | Depende | Nota |
|----|---------|---------|------|
| T0a–T0d | DONE | — | Sin engines |
| T0e | GoalLock | T0d | Siguiente código |
| T0f | Push/Ping 15s+post-tool | T0e | Sin LLM |
| T0g | Focus Monitor | T0f | |
| T0h | Bitácora | T0f | |
| T0k | Task Classifier | T0e | Rutas PLANNING/MEMORY |
| T0n | PlanningProposal schema + merge-to-Q (no auto-resolve) | T0b,T0k | NUEVA |
| T0o | PlanningPort interface + FakeOpenClaw/FakeHermes | T0n,T1 | NUEVA; real adapters en T3 |
| T0p | MemoryPack schema + Hermes MemoryPort Fake | T0f,T0j | NUEVA |
| T0q | Ping hook: optional memory_refresh_due policy | T0f,T0p | NUEVA |
| T3 | OpenClaw + Hermes adapters reales | T1,T0o,T0p | WAVE-1 |
| T0j | Register File load/store | T0e | MemoryPack escribe regs |

**No se reabre T0a–T0d.** Engines se enganchan después del compiler y alrededor del ping.

---

## 6 · Policies (futuro policies/engine_attach.yaml)

```yaml
input_gateway:
  planning_enrich: true
  engines: [openclaw, hermes]
  auto_accept_proposals: false
  max_engine_calls_per_input: 2

push_ping:
  interval_s: 15
  post_tool: true
  memory_refresh:
    engine: hermes
    on_focus_degraded: true
    on_episode_boundary: true
    interval_multiples: 4
  openclaw_on_ping: false
```

---

## 7 · Orden de ejecución actualizado (inmediato)

```
T0e GoalLock
T0f Push/Ping
T0g Focus
T0h Bitácora
T0i Objective Echo
T0j Register File
T0k Classifier (+ rutas PLANNING/MEMORY_REFRESH)
T0n PlanningProposal schema + merge
T0o PlanningPort Fake engines
T0p MemoryPack + Hermes Memory Fake
T0q Ping memory_refresh hook
T0l Reasoning Ledger
T0m Tests anclas + engine attach fakes
… luego WAVE-1 T1–T7 (adapters reales)
```

**Total salidas plan activo:** 61 + T0n–T0q (+4) = **65**

---

## 8 · Criterio de aceptación

1. Input path compila sin engines.
2. Engines solo vía Classifier + Port.
3. Proposal ≠ Goals COMPILED.
4. Ping no llama LLM por defecto; Hermes solo MemoryPort bajo policy.
5. GoalLock inmutable ante MemoryPack.
6. Adapters reales en T3; fakes en T0o/T0p.

---

**SIGUIENTE CÓDIGO:** T0e GoalLock (sin engines).
