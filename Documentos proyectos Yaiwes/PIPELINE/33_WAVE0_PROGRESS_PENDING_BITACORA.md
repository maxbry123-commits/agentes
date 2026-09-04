# PIPELINE/33 — WAVE-0 progreso · pendientes detallados · bitácora de recuperación

**Fecha:** 2026-08-14  
**Repo:** maxbry123-commits/agentes · branch main  
**HEAD al cerrar este doc:** 29dc6c95bc8da9db4e97e17b1afc11cfe3917350  
**Rol de este archivo:** memoria + historial + bitácora. Cualquier instancia Grok debe poder retomar SOLO con este doc + 29/30/31/32.

---

## 0 · Reglas operativas (inmutables)

1. 1 tarea = 1 salida · ≤300 LOC/archivo · commit real en GitHub (no sandbox).
2. Cada **4–5 salidas** → mostrar enlaces commit a Director + re-leer este PIPELINE.
3. Cada escritura en PIPELINE debe ser **detallada**: qué, path, deps, criterio done, qué NO hacer.
4. Si se pierde contexto → **PARAR** y pedir doc por trazabilidad; no inventar.
5. OpenClaw/Hermes **NO se cablean** hasta Wordflow cerrado + micro-kernel install + HF compute (PIPELINE/32).
6. Core Input/Lock/Ping/Classifier = **0% LLM**.

---

## 1 · HECHO WAVE-0 (T0a–T0k) — trazabilidad commit

| ID | Qué | Paths principales | Commit | Link |
|----|-----|-------------------|--------|------|
| T0a | InputContract schema + InputCompiler literal | `schemas/input_contract.schema.json` · `engine/input_compiler.py` · `tests/test_input_compiler.py` | 5a13b2c1 | https://github.com/maxbry123-commits/agentes/commit/5a13b2c187e8cc229cd1c1e98d4a4baa67e50676 |
| T0b | Structured Questions Q01–Q12 + resolve_gate | `schemas/structured_questions.schema.json` · `engine/structured_questions.py` · tests | dade3047 | https://github.com/maxbry123-commits/agentes/commit/dade3047248555dc7fb1eede9d412f3418f2d26e |
| T0c | ResourceTrace inventory pre-plan | `schemas/resource_trace.schema.json` · `engine/resource_trace.py` · tests | 6a6fb0d2 | https://github.com/maxbry123-commits/agentes/commit/6a6fb0d22070ae3ac282b7ce62857de8d8f747d2 |
| T0d | GoalsCompiler from resolved form only | `schemas/goals_compiled.schema.json` · `engine/goals_compiler.py` · tests | b34adafe | https://github.com/maxbry123-commits/agentes/commit/b34adafea5f0ce2d7ce363c315e70fe64844cb0b |
| T0e | GoalLock immutable + validate/discard | `schemas/goal_lock.schema.json` · `engine/goal_lock.py` · tests | e385de63 | https://github.com/maxbry123-commits/agentes/commit/e385de632e3ee0061a3088dab6f9215f1df63ba7 |
| T0f | Push/Ping 15s + post_tool | `schemas/push_ping.schema.json` · `engine/push_ping.py` · tests | bb4f3208 | https://github.com/maxbry123-commits/agentes/commit/bb4f320886fda6252e1cd22b4099d83c6a2b9b71 |
| T0g | FocusMonitor + focus_gate | `schemas/focus_monitor.schema.json` · `engine/focus_monitor.py` · tests | 00dbea21 | https://github.com/maxbry123-commits/agentes/commit/00dbea212595a0695b12cbb93ada59702ad2de0f |
| T0h | Bitácora EventStore append-only chain | `schemas/bitacora_event.schema.json` · `engine/bitacora.py` · tests | dc60f978 | https://github.com/maxbry123-commits/agentes/commit/dc60f97848ce46f208f45bd8496d015527b3259f |
| T0i | ObjectiveEcho pre-engine inject | `schemas/objective_echo.schema.json` · `engine/objective_echo.py` · tests | 558ecdec | https://github.com/maxbry123-commits/agentes/commit/558ecdec0202136f043da44bdc4725016a442697 |
| T0j | Cognitive Registers R0–R15 | `schemas/cognitive_registers.schema.json` · `engine/cognitive_registers.py` · tests | 4e74099d | https://github.com/maxbry123-commits/agentes/commit/4e74099db3338ed203b59d63b5b7fb4188f46dc7 |
| T0k | TaskClassifier + DecisionGate | `schemas/task_class.schema.json` · `engine/task_classifier.py` · tests | 29dc6c95 | https://github.com/maxbry123-commits/agentes/commit/29dc6c95bc8da9db4e97e17b1afc11cfe3917350 |

**Base path código:** `extensions/wordflow/`  
**Tree engine:** https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/engine

### Cadena determinista ya materializada

```
raw → InputCompiler → Questions → (ResourceTrace) → GoalsCompiler
    → GoalLock → [Echo + Registers] → Classifier/Gate
    → Push/Ping + Focus → Bitácora
```

Engines OC/Hermes: **solo hints** en Classifier; **no adapters reales**.

---

## 2 · PENDIENTE WAVE-0 (detalle recuperación)

### T0l — Reasoning Ledger / Decision Memory frames
- **Objetivo:** Frame append-only: goal, evidence, decision, alternatives, refutations, tools, artifacts, confidence, checkpoint_id.
- **Paths:** `schemas/reasoning_ledger.schema.json` · `engine/reasoning_ledger.py` · `tests/test_reasoning_ledger.py`
- **Deps:** T0e GoalLock, T0h Bitácora (opcional log GATE/NOTE).
- **Done cuando:** append frame + verify no rewrite + link lock_id; 0% LLM.
- **NO:** llamar LLM; no sustituir Bitácora.

### T0m — Tests anclas cognitivas integrados
- **Objetivo:** Suite que encadena T0a→T0k (contract→questions→goals→lock→ping→focus→echo→registers→classify) + casos violación GoalLock.
- **Path:** `tests/test_wave0_anchors_integration.py`
- **Deps:** T0a–T0l preferible; mínimo T0a–T0k.
- **Done cuando:** tests pasan en cadena; documentar comando `python -m unittest extensions.wordflow.tests...`
- **NO:** CI Actions obligatorio en esta tarea (puede ser T40).

### T0n — PlanningProposal schema + merge-to-Q (no auto-resolve)
- **Objetivo:** Schema proposal desde engines; merge solo como Q* PROPOSED; resolve_gate sigue exigiendo ANSWERED.
- **Paths:** `schemas/planning_proposal.schema.json` · `engine/planning_proposal.py`
- **Deps:** T0b, T0k.
- **Done cuando:** proposal no marca resolved=true; policy auto_accept default false.
- **NO:** adapters reales OC/Hermes (PIPELINE/32).

### T0o — PlanningPort interface + FakeOpenClaw/FakeHermes
- **Objetivo:** Interface Port + fakes que devuelven PlanningProposal.
- **Paths:** `engine/ports/planning_port.py` · `engine/ports/fake_engines.py`
- **Deps:** T0n.
- **Done cuando:** Fake retorna proposal válido; sin red calls.
- **NO:** clonar repos agentes; no T3.

### T0p — MemoryPack schema + Hermes MemoryPort Fake
- **Objetivo:** MemoryPack + Fake MemoryPort; merge vía `cognitive_registers.merge_memory_pack`.
- **Paths:** `schemas/memory_pack.schema.json` · `engine/ports/memory_port.py`
- **Deps:** T0j, T0f.
- **Done cuando:** Fake pack → registers R5/R7/R8/R9; R0 intacto.
- **NO:** Hermes real.

### T0q — Ping hook memory_refresh policy
- **Objetivo:** Policy en PushPingSupervisor: on_focus_degraded / every N intervals → llamar MemoryPort **si inyectado**; default off sin port.
- **Paths:** patch `engine/push_ping.py` o `engine/push_ping_hooks.py` · `policies/engine_attach.yaml` seed
- **Deps:** T0f, T0p.
- **Done cuando:** sin port → no crash; con Fake → merge registers.
- **NO:** openclaw_on_ping.

---

## 3 · PENDIENTE post WAVE-0 (resumen detallado por wave)

### WAVE-1 · Runtime Bus + Manifest + Handoff (T1–T7)
| ID | Qué hacer | Done | NO |
|----|-----------|------|----|
| T1 | Engine ABI (protocolo job in/out) | schema + Protocol Python | acoplar OC código |
| T2 | RuntimeBus no-bypass (todo job pasa bus) | dispatch + deny sin manifest | god controller |
| T3 | **DIFERIDO** OpenClaw+Hermes adapters reales | solo tras PIPELINE/32 pasos 2–3 | ahora |
| T4 | Stubs engines genéricos | FakeEngine | — |
| T5 | Execution Manifest sign + pre-dispatch gate | sign hash + DENY sin sign | LLM sign |
| T6 | Handoff Package compile/validate | schema goals/artifacts/evidence/checkpoint | prosa libre |
| T7 | Tests FakeEngine + Manifest DENY | unittest | — |

### WAVE-2 · Resource + Passport + Broker (T8–T13)
ArtifactPin / HF index / ResourceGate / Capability Passport / broker prepare-load — **detalle fino en PIPELINE/29**. HF wire real post-Wordflow.

### WAVE-3 · Parallel FULL N07 (T14–T24)
Scheduler, queue, workers 10–50, sandbox, SSH orchestrator, lease, checkpoint, circuit breaker — **no MVP**. Ver plan 29 + docs parallel.

### WAVE-4 · Sheriff + Mission + Evidence (T25–T28)
Sheriff 5 estados + Mission=GoalLock enforce + Evidence graph mínimo.

### WAVE-5 · Expert Panel (T29–T32)
Panel multi-model + Decision Gate — **después** WAVE-0/1 estables.

### WAVE-6–8 (T33–T48)
Registry publish, KER/DNA proto, CI, Tool Contract, deliberation_level, Episode structure, Hallucination detector stub, Confidence gate, Literal mode, templates, claim DSL.

### POST Wordflow (bloque crítico Director)
1. Micro-kernel instalación/descarga determinista → GitHub  
2. HF como compute/storage  
3. Cablear T3 OC/Hermes + download agents  
Sin 1–2, descarga se corta (PIPELINE/32).

---

## 4 · Docs PIPELINE vigentes (orden lectura recuperación)

1. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/33_WAVE0_PROGRESS_PENDING_BITACORA.md **(este — empezar aquí)**
2. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/32_ENGINE_DEFER_AND_HF_COMPUTE.md
3. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/31_ENGINE_ATTACH_INPUT_AND_PING.md
4. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/30_KIMI_COGNITIVE_RUNTIME_INTEGRATION.md
5. https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/29_YAIWES_RUNTIME_GAPS_Y_PLAN.md
6. https://github.com/maxbry123-commits/agentes/blob/main/docs/PRUNE_OPENCLAW_HERMES.md

Si falta contexto de **código Wordflow previo (main_loop, council, sentinel):** pedir al Director re-pasar docs SALIDA wordflow / ficha v2 / DESPLIEGUE.

---

## 5 · Auditoría chat → gaps en PIPELINE (cerrados o abiertos)

| Tema chat | ¿En PIPELINE? | Estado |
|-----------|---------------|--------|
| Input Gateway T0a–T0d | 30 + 33 | HECHO código |
| GoalLock / Ping / Focus / Bitácora / Echo / Registers / Classifier | 30 + 33 | HECHO código |
| OC/Hermes solo 10% LLM + adapters | 31 + 32 + 33 | Diseño; cableado diferido |
| HF 1TB skills/datasets | 32 + 29 | Post-Wordflow |
| Micro-kernel install determinista | 32 | Post-Wordflow |
| Parallel N07 full SSH/10-50 | 29 + 33 wave3 | Pendiente |
| Fakes Planning/Memory T0n–T0q | 31 + 33 | Pendiente WAVE-0 cola |
| main_12 loop existente wordflow | código previo repo | No reimplementar; integrar anchors |
| CI workflow tests | T40 | Pendiente |
| Actualizar línea “SIGUIENTE T0e” en 32 | 32 obsoleto parcial | **Superseded por 33** |

---

## 6 · Próxima acción código

**T0l** Reasoning Ledger (detalle §2).  
Luego T0m → T0n…T0q según Director.  
No T3 real.

---

## 7 · Contadores

| Métrica | Valor |
|---------|-------|
| WAVE-0 hechos | T0a–T0k (11) |
| WAVE-0 pendientes | T0l–T0q (6) |
| Plan total aprox | ~65 salidas (T0* + T1–T48 + post) |
| HEAD | 29dc6c95… |

**SIGUIENTE CÓDIGO:** T0l  
**SIGUIENTE DOC tras T0l–T0m:** refrescar §1 de este archivo con commits nuevos.
