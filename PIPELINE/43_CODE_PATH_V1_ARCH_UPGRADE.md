# PIPELINE 29 — CODE PATH V1 · ARCH UPGRADE · KNOWLEDGE RUNTIME · EXPERT ROLES

**Versión:** 1.1  
**Fecha:** 2026-08-15  
**Repo objetivo:** `maxbry123-commits/agentes`  
**Ancla:** PIPELINE 28 (SUPERSEDE parcial)  
**Modo:** 1 tarea = 1 salida = 1 commit · ≤220 LOC/archivo · YAML=contrato · .py=runtime · `llm_control: DENY` núcleo  
**Estado:** FUENTE DE VERDAD actualizada tras auditoría arquitectura + Knowledge Runtime + roles expertos

---

## 0. TRAZABILIDAD NUEVA (batch 2026-08-15)

| ID | Fuente | Aporta |
|----|--------|-------|
| F40 | Auditoría arquitectura (P0–P4) | Mission Planner · DAG · Blackboard · Event Bus · Scheduler · Policy · Context Builder · 5 planos |
| F41 | Knowledge Runtime redesign | Skill/Dataset/Method/Adapter/Capability Runtime · Unified Registry · Knowledge Package · Resource Runtime |
| F42 | Roles expertos + multi-motor | Wordflow analiza agentes/modelos disponibles → Router → especialistas API → Ask Council → motores Wordflow |
| F01–F34 | PIPELINE 28 | Base previa (no se pierde) |

**Regla:** sin ancla Fxx → no se programa.

---

## 1. VEREDICTO FORENSE (post-integración)

```
VEREDICTO: PARCIAL_FUERTE → listo para materializar V1.1
COBERTURA DOCS→PLAN: ~94%
PLAN→CÓDIGO: ~40% (sin cambio de código en esta salida)
SOBREINGENIERÍA: CONTROLADA (P0–P2 V1; P3–P4 post-V1)
5 PLANOS: DEFINIDOS · kernel permanece pequeño
KNOWLEDGE RUNTIME: OBLIGATORIO (no opcional HF)
EXPERT ROLES: INTEGRADO en C-12 reforzado
```

### Decisiones de alcance V1 vs post-V1

| Componente | V1 | Post-V1 / V1.1 |
|------------|----|----------------|
| Mission Planner (split Council) | **SÍ** (C-21) | — |
| Mission Graph (DAG mínimo) | **SÍ** ligero (C-22) | Scheduler full |
| Blackboard operativo | **SÍ** (C-23) | — |
| Event Bus mínimo | **SÍ** stub (C-24) | full pub/sub |
| Scheduler independiente | stub + prioridades | full afinidad/cancel |
| Context Builder | **SÍ** (C-25) | — |
| Policy Engine | **SÍ** seed (C-26) | — |
| Knowledge Runtime (Skill/Dataset/Method/Adapter) | **SÍ** contratos + Unified Registry (C-27) | proveedores concretos |
| Capability Marketplace métricas | NO | post-V1 |
| Semantic Diff + Runtime/Cognitive Budget | NO | post-V1 |
| Artifact Registry + Workflow Genome | seed hash | full post-V1 |
| 5 planos físicos | documentados | materializar progresivo |

---

## 2. LISTA 1 — GAPS ACTUALIZADOS

### Gaps previos (PIPELINE 28) — siguen vivos

| ID | Gap | Estado |
|----|-----|--------|
| G-CODE-01..24 | SE · C09 · RB · C10 · Credential · Capability 3-modos · 9docs · Handoff · etc. | SIN CAMBIO |
| G-CODE-25 | Engine adapters Hermes/OpenClaw | post-cierre Wordflow |

### Gaps nuevos (F40 + F41 + F42)

| ID | Gap | Qué falta exactamente | Ancla | Prioridad |
|----|-----|----------------------|-------|-----------|
| G-CODE-26 | **Mission Planner** | Componente que recibe CouncilContract y produce TaskGraph (nodos + deps). Council decide; Planner divide. | F40 P0 | P0 |
| G-CODE-27 | **Mission Graph / DAG ligero** | Nodos desbloqueados + edges + checkpoint por nodo. No pipeline lineal. | F40 P0 | P0 |
| G-CODE-28 | **Blackboard operativo** | Estado vivo: objetivos activos, tareas, evidencias, recursos, bloqueos. Ledger = histórico. | F40 P0 | P0 |
| G-CODE-29 | **Event Bus mínimo** | Eventos: MissionCreated → GoalLocked → ResourcesReady → CompileFinished → AuditPassed → Deploy* | F40 P0 | P1 |
| G-CODE-30 | **Context Builder** | Antes de WF.MAIN_12: empaqueta MissionContract + GoalLock + Evidence + Policies + Blackboard + Recursos (mínimo payload). | F40 P1 | P0 |
| G-CODE-31 | **Policy Engine seed** | Seguridad · licencias · deploy · credenciales · permisos · límites. Todos los nodos consultan. | F40 P1 | P1 |
| G-CODE-32 | **Knowledge Runtime** | Skill/Dataset/Method/Adapter/Capability Runtime + Unified Registry + Knowledge Package. No opcional. | F41 | P0 |
| G-CODE-33 | **Resource Runtime** (evoluciona Resource Brain) | Discovery → Resolver → Registry → Loader → VersionPin → DepGraph → Cache → Session → Snapshot → Evidence | F41 | P0 |
| G-CODE-34 | **Adapter contract único** | connect / discover / execute / verify / disconnect para GitHub·HF·SSH·FS·MCP·Docker… | F41 | P1 |
| G-CODE-35 | **Expert Role Analyzer** | Wordflow inspecciona agentes/modelos disponibles → produce AvailableMotors map → Router elige especialistas | F42 | P0 |
| G-CODE-36 | **Multi-motor Ask Council** | Roles de especialista (API distintas) + motores Wordflow (OpenClaw/Hermes/… como engines) en el mismo Council | F42 | P0 |
| G-CODE-37 | Dependency Graph fino | repo→file→class→function→artefacto (recompile solo afectado) | F40 P1 | post-V1 |
| G-CODE-38 | Capability Marketplace métricas | calidad/latencia/coste/disponibilidad | F40 P2 | post-V1 |
| G-CODE-39 | Semantic Diff + Budgets | goal change → impact → recompile parcial · Runtime/Cognitive Budget | F40 P2 | post-V1 |
| G-CODE-40 | Artifact Registry + Workflow Genome | hash/versión/productor/consumidor + manifiesto declarativo | F40 P2 | post-V1 |

---

## 3. LISTA 2 — TAREAS Y SALIDAS (V1.1)

### Bloque residual PIPELINE 28 (sin reordenar IDs)

| ID | Tarea | Path | Gaps | LOC |
|----|-------|------|------|-----|
| C-01 | InputBlock + GoalLock e2e | wordflow/ | 11 | ≤100 |
| C-02 | Enchufe gate + fichas | ficha.v2 × | 13 | ≤80 |
| C-03 | architecture_output + code_output + Validator | schemas/ | 10,18 | ≤120 |
| C-04 | SE acquire_12 | source_evolution/ | 01 | ≤180 |
| C-05 | SE analyze_12 + reuse_decision | source_evolution/ | 02 | ≤150 |
| C-06 | C09 dual + MethodPackage seed | skill_compiler/ | 05,21 | ≤200 |
| C-07 | promote_12 → request_deploy | source_evolution/ | 03,04 | ≤140 |
| C-08 | Resource Brain → **Resource Runtime** base | resource_brain/ | 06,33 | ≤180 |
| C-09 | Audit 4-pasadas + EvidencePacket | audit_forensic/ | 08 | ≤120 |
| C-10 | Doc→Arch→Code microflow | wordflow/microflows/ | 18 | ≤150 |
| C-11 | 9 docs nativos runtime (lazy 4 core) | project_bootstrap/ | 19 | ≤150 |
| C-12 | ExpertPanel + Ask Council 12 + **Expert Role Analyzer** | wordflow/council/ | 20,35,36 | ≤180 |
| C-13 | HF index skills/datasets (bajo demanda) | providers/hf/ | 21 | ≤160 |
| C-14 | Credential Manager | extensions/credentials/ | 22 | ≤200 |
| C-15 | Capability Router Live/MCP/Snapshot | capabilities/ | 24 | ≤160 |
| C-16 | C10 Deploy multi-repo + AuthBridge | extensions/github/ | 09,23 | ≤220 |
| C-17 | SSH adapter (contract Adapter) | extensions/ssh/ | 23,34 | ≤100 |
| C-18 | main_12 wiring code path | wordflow/ | 12 | ≤150 |
| C-19 | License + Repair e2e + tests + CI + claim | tests/ | 15 | ≤120 |

### Bloque nuevo arquitectura (V1.1) — orden de arranque

| ID | Tarea | Path | Gaps | LOC | Nota |
|----|-------|------|------|-----|------|
| C-21 | **Mission Planner** | wordflow/planner/ | 26 | ≤160 | Council → TaskGraph |
| C-22 | **Mission Graph (DAG ligero)** | wordflow/graph/ | 27 | ≤180 | nodes/edges/checkpoint |
| C-23 | **Blackboard operativo** | wordflow/state/ | 28 | ≤140 | vs Ledger histórico |
| C-24 | **Event Bus mínimo** | wordflow/events/ | 29 | ≤120 | stub pub/sub |
| C-25 | **Context Builder** | wordflow/context/ | 30 | ≤120 | payload mínimo pre-MAIN_12 |
| C-26 | **Policy Engine seed** | control/policies/ | 31 | ≤140 | seguridad/licencia/deploy/cred |
| C-27 | **Knowledge Runtime + Unified Registry** | knowledge/ | 32,33,34 | ≤220 | Skill/Dataset/Method/Adapter contracts |
| C-28 | Adapter contract + GitHub/HF/FS seeds | adapters/ | 34 | ≤160 | connect/discover/execute/verify/disconnect |
| C-29 | Knowledge Package producer | knowledge/package/ | 32 | ≤140 | Method+Skill+Dataset+Evidence+Tests |
| C-30 | Wiring Planner→Graph→Blackboard→Events → main_12 | wordflow/ | 26–29 | ≤150 | integración |
| C-31 | Tests + CI + claim bloque arquitectura | tests/ + PIPELINE | — | ≤100 | |

**TOTAL SALIDAS V1.1 = 19 (C-01…C-19) + 11 (C-21…C-31) = 30**  
Post-V1: G-CODE-37…40 (Dependency Graph fino, Marketplace, Semantic Diff, Budgets, Genome full).

**Orden de arranque recomendado (anti-sobreingeniería):**
```
C-01 → C-02 → C-21 (Planner) → C-23 (Blackboard) → C-25 (Context)
→ C-12 (Council + Expert Analyzer) → C-26 (Policy)
→ C-08/C-27 (Resource/Knowledge Runtime) → C-28 (Adapters)
→ C-04…C-07 (SE) → C-22 (DAG) → C-24 (Events)
→ C-14/C-15/C-16 (Credential + Capability + C10)
→ C-11 (9 docs después de artefactos reales)
→ C-18 wiring → C-19/C-31 claims
```

---

## 4. DIAGRAMA DE FLUJO FINAL (programación de code · V1.1)

```text
═══════════════════════════════════════════════════════════════
 CONTROL PLANE
═══════════════════════════════════════════════════════════════
 [chat | documento | repo URL | patch]
            │
            ▼
 C-01  InputBlock + Sentinel + GoalLock
        · hash chain · G_IN 01-12 · quality_bar · never MVP
        · Classifier: NEW | CORRECTION | UPDATE
            │
            ▼
 C-12  Expert Role Analyzer + Ask Council 12
        · escanea motores disponibles (modelos + agentes)
        · Router elige especialistas (API distintas)
        · motores Wordflow (OpenClaw/Hermes/…) como engines
        · output: CouncilContract (plan + roles + riesgos)
            │
            ▼
 C-21  Mission Planner
        · CouncilContract → TaskGraph (nodos + deps + policies)
        · NO es el Council
            │
            ▼
 C-22  Mission Graph (DAG)
        · solo nodos desbloqueados · checkpoints por nodo
            │
            ▼
 C-26  Policy Engine (consulta en cada nodo)
        · seguridad · licencia · deploy · cred · límites
            │
═══════════════════════════════════════════════════════════════
 STATE PLANE
═══════════════════════════════════════════════════════════════
 C-23  Blackboard (operativo)     C-18 Ledger (histórico append-only)
        · objetivos activos            · MissionCreated…
        · tareas / evidencias          · GoalLocked…
        · recursos / bloqueos          · DeployFinished…
        · métricas                     · hash chain
            │
 C-24  Event Bus (mínimo)
        MissionCreated → GoalLocked → ResourcesReady
        → CompileFinished → AuditPassed → Deploy*
            │
═══════════════════════════════════════════════════════════════
 KNOWLEDGE PLANE  (obligatorio · no opcional)
═══════════════════════════════════════════════════════════════
 C-27  Knowledge Runtime + Unified Registry
        ├── Skill Runtime      (id/ver/inputs/outputs/deps/tests/license)
        ├── Dataset Runtime    (Loader→Validator→Pin→Normalizer→Cache→KP)
        ├── Method Runtime     (Compile→Verify→Optimize→Promote)
        ├── Adapter Runtime    (contract único)
        ├── Capability Runtime (Resolver→Compat→Cost→Execute→Evidence)
        └── Prompt Runtime     (versionado · guardrails · nunca embebido)
            │
 C-08  Resource Runtime (evoluciona Resource Brain)
        Discovery → Resolver → Registry → Loader → VersionPin
        → DepGraph → Cache → Session → Snapshot → Evidence
            │
 C-28  Adapters (mismo contrato)
        GitHub · HF · FS · SSH · MCP · Docker · …
        connect / discover / execute / verify / disconnect
            │
 C-29  Knowledge Package
        Method + Skill + Dataset + Evidence + Tests + Meta + License
            │
═══════════════════════════════════════════════════════════════
 EXECUTION PLANE
═══════════════════════════════════════════════════════════════
 C-25  Context Builder (payload mínimo)
        MissionContract + GoalLock + Evidence + Policies
        + Blackboard slice + Recursos seleccionados
            │
            ▼
 C-04  SE acquire_12 (parcial|completo · VersionPin · license_gate)
            │
 C-05  SE analyze_12 (IR · reuse_decision REUSE_FIRST|ADAPT|GENERATE_LAST)
            │
 C-06  C09 dual compiler (knowledge | procedure | executable)
            │
 C-07  promote_12 → request_deploy (solo PASS)
            │
 C-03  Validator fail_closed + CodeOutput
            │
 C-09  AUD.FORENSIC 4 pasadas + EvidencePacket
            │
 C-09b WF.MAIN_12 Cognitive Loop
        Pre-flight → Think → Micro-checkpoint → Post-3Q
        → Self-audit 5 → Repair (max 2) + circuit breaker
        · LLM solo aquí (10%) · JUEZ ≠ ESCRITOR
            │
═══════════════════════════════════════════════════════════════
 DEPLOY + OBSERVATION
═══════════════════════════════════════════════════════════════
 C-14  Credential Manager (token_ref · nunca literal)
            │
 C-15  Capability.execute (Live | MCP | Snapshot)
            │
 C-16  C10 github_deploy
        dry-run → Git Data API (blob→tree→commit→ref)
        → expected_head → no force_push → evidence.json
            │
 C-17  SSH / otros adapters (si hace falta)
            │
 C-11  9 docs nativos (después de artefactos reales)
        PROFILE · ARCHITECTURE · CAPABILITIES · TRACEABILITY
        (+ resto lazy)
            │
 C-19/31  Tests + CI + claim YAML (path + blob_sha + doc_anchor)
═══════════════════════════════════════════════════════════════
```

**Reglas duras del diagrama**
1. Council decide · Planner divide · Scheduler (futuro) ejecuta nodos desbloqueados.
2. Knowledge Runtime es plano obligatorio; proveedores son adapters.
3. LLM solo dentro de Cognitive Loop / Expert roles (10%).
4. 9 docs se generan desde artefactos reales (no antes).
5. can_write_kernel / can_write_github = false hasta C10 autorizado.
6. 1 nodo = 1 package ≤220 LOC · ficha.v2 en cada módulo.

---

## 5. CINCO PLANOS (arquitectura estable)

```
CONTROL PLANE     Mission Manager · Planner · (Scheduler) · Event Bus · Policy
EXECUTION PLANE   Resource Runtime · SE · Compiler · Validator · Deploy · Cognitive Loop
KNOWLEDGE PLANE   Skill · Dataset · Method · Adapter · Capability · Prompt · Unified Registry · Knowledge Package
STATE PLANE       Blackboard · Mission Ledger · Checkpoints · Artifact Registry (seed)
OBSERVATION PLANE Audit · EvidencePacket · métricas · trazabilidad · claims
```

Kernel permanece pequeño e inmutable. Todo lo demás = extensiones cargables por contratos.

---

## 6. EXPERT ROLES + MULTI-MOTOR (detalle F42)

```
Wordflow
  │
  ├─ Expert Role Analyzer
  │     escanea: modelos disponibles + agentes registrados + APIs Router
  │     produce: AvailableMotors {role → engine|api|cost|latency}
  │
  ├─ Router Inteligente (futuro micro-kernel)
  │     selecciona especialistas según tarea
  │
  └─ Ask Council 12
        · roles de especialista (API distintas)
        · motores Wordflow (OpenClaw / Hermes / …) solo como engines de razonamiento
        · output estructurado → Mission Planner
```

No se embebe ningún agente. Solo se invocan por contrato de motor. Mañana se puede sustituir el motor sin tocar el Wordflow.

---

## 7. BITÁCORA

| Fecha | Acción |
|-------|--------|
| 2026-08-14 | PIPELINE 28 creado (code path V1 base) |
| 2026-08-15 | PIPELINE 29/43: integración F40 arquitectura + F41 Knowledge Runtime + F42 Expert Roles |
| 2026-08-15 | Gaps G-CODE-26…40 · Tareas C-21…C-31 · Diagrama 5 planos · orden anti-sobreingeniería |
| 2026-08-15 | **C-01 COMPLETED** — GoalLock e2e · `extensions/wordflow/engine/goal_lock.py` · 6/6 tests OK · sha256 `94a10e4c…` |

---

## 8. ENLACE PARA INGENIEROS (fuente de verdad)

**GitHub (repo privado agentes):**  
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/43_CODE_PATH_V1_ARCH_UPGRADE.md

**C-01 artifacts:**  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/goal_lock.py  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/tests/test_goal_lock.py

---

**FIN PIPELINE 43**  
Estado: C-01 cerrado · siguiente C-02 (Enchufe gate + fichas).
