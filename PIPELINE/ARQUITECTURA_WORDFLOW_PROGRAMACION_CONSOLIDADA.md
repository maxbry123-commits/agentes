# ARQUITECTURA WORDFLOW PROGRAMACIÓN — DOCUMENTO CONSOLIDADO

**Versión:** 1.0  
**Fecha:** 2026-08-18  
**Repo:** maxbry123-commits/agentes  
**Autor:** Auditoría Forense Integral  
**Fuente:** Análisis cruzado ARQUITECTURA_WORDFLOW_PROGRAMMING.md + WORDFLOW_PROGRAMMING_FORENSIC_MAP.md + WORDFLOW_PROGRAMMING_MASTER.md + code_path_runner.py + programming_pipeline.py + standards/*

---

## 📋 ÍNDICE

1. [Visión General](#1-visión-general)
2. [Arquitectura en Capas](#2-arquitectura-en-capas)
3. [Componentes del Sistema](#3-componentes-del-sistema)
4. [Flujo de Ejecución (Hot Path)](#4-flujo-de-ejecución-hot-path)
5. [Control Plane Forense](#5-control-plane-forense)
6. [Inventario de Archivos](#6-inventario-de-archivos)
7. [Contratos y Enforcement](#7-contratos-y-enforcement)
8. [Máquina de Decisión (PASS/FAIL/BLOCK)](#8-máquina-de-decisión)
9. [Límites Explícitos](#9-límites-explícitos)
10. [Auditoría Cruzada 3-Pasadas](#10-auditoría-cruzada-3-pasadas)
11. [Guía de Uso y Checklist](#11-guía-de-uso-y-checklist)
12. [Referencias y Enlaces](#12-referencias-y-enlaces)

---

## 1. VISIÓN GENERAL

### Propósito
Sistema determinista fail-closed para programación de código dentro del Wordflow. No es IDE. No es escritor autónomo de Git. **LLM siempre DENY en paths críticos.**

### Principios
- ✅ **Determinismo:** Núcleo sin LLM directo, solo contratos
- ✅ **Fail-closed:** Sin context verificado = BLOCK inmediato
- ✅ **COPY-FIRST:** Reutilizar código antes de generar
- ✅ **Trazabilidad:** Cada decisión auditada con evidencia
- ✅ **Validación:** Pre/Post gates obligatorios
- ✅ **Forense:** 3 pasadas (estructura, conectividad, comportamiento)

### Dos Scopes (No Colapsar)
| Scope | Contenido | Responsable |
|-------|-----------|------------|
| **C-19 Programming Path** | code_path_runner + forensic_core + measures | Núcleo determinista |
| **Engine Wordflow Completo** | 80+ módulos engine/* | Orquestación amplia |

---

## 2. ARQUITECTURA EN CAPAS

```
┌─────────────────────────────────────────────────────────────┐
│ Callers: bootstrap / smoke / CI / agente / UNKNOWN          │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ ENGINE (80+ módulos) — execution + orquestación             │
│                                                              │
│  HOT PATH programming:                                       │
│  ├─ code_path_runner.run_code_path (único path verificado)   │
│  ├─ quality_bar (admit/reject input)                         │
│  ├─ goal_lock (lock de goals)                                │
│  ├─ cognitive_loop (interior LLM = UNKNOWN)                  │
│  ├─ evidence_packet (evidencia del engine)                   │
│  ├─ skill_native_compiler (compile skill opcional)           │
│  ├─ programming_pipeline (pipeline pre/post + run_unified)   │
│  └─ main_loop (main_12 + programming_path)                   │
│                                                              │
│  Resto: orchestrator*, policy, handoff, bridges, …           │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ STANDARDS (control plane) — fail-closed                      │
│                                                              │
│  ├─ forensic_core (PASS máquina C-19)                        │
│  ├─ forensic_contract + forensic_report                      │
│  ├─ verdict_authority (decisión final)                       │
│  ├─ gap_registry (ciclo de vida gaps)                        │
│  ├─ closure_engine (árbitro CLOSED)                          │
│  ├─ checklist_sheriff (checklist + applicability)            │
│  ├─ executor_gates (pre/post gates)                          │
│  ├─ copy_first + symbol_index (scanner COPY-FIRST)           │
│  ├─ context_manifest (context + validator)                   │
│  ├─ evidence_verifier (claim ≠ evidence)                     │
│  ├─ wiring_graph (catalog graph connectivity)                │
│  ├─ test_runner (smoke tests offline)                        │
│  ├─ quality_dag (DAG calidad)                                │
│  ├─ policy_snapshot (freeze de política)                     │
│  └─ [20+ más en standards/]                                  │
│                                                              │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ DATA / POLICY                                                │
│  ├─ component_catalog.json (componentes declarados)          │
│  ├─ connect_catalog.json (conexiones declaradas)             │
│  ├─ PIPELINE/*.md (política humana)                          │
│  ├─ .cursor/rules/wordflow-programming.mdc (rules agent)     │
│  ├─ AGENTS.md (autoridad docs)                               │
│  └─ .github/workflows/forensic-gates.yml (CI forense)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. COMPONENTES DEL SISTEMA

### 3.1 ENGINE — Execution Plane

#### Hot Path (Elementos Críticos)

| Componente | Path | Responsabilidad |
|------------|------|-----------------|
| **code_path_runner** | `extensions/wordflow/engine/code_path_runner.py` | Punto de entrada único, orquesta flujo completo |
| **programming_pipeline** | `extensions/wordflow/engine/programming_pipeline.py` | Pipeline pre/post + run_unified |
| **input_quality_bar** | `extensions/wordflow/engine/input_quality_bar.py` | Validar calidad input |
| **goal_lock** | `extensions/wordflow/engine/goal_lock.py` | Lock inmutable de goals |
| **cognitive_loop** | `extensions/wordflow/engine/cognitive_loop.py` | Loop cognitivo (LLM interior) |
| **evidence_packet** | `extensions/wordflow/engine/evidence_packet.py` | Empaque de evidencia |
| **skill_native_compiler** | `extensions/wordflow/engine/skill_native_compiler.py` | Compile skill a código |
| **main_loop** | `extensions/wordflow/engine/main_loop.py` | main_12 + programming_path bridge |

#### Lo que EJECUTA HOY `run_code_path`
```python
1. ForensicProgrammingEnforcer.require_context() 
   → BLOCK si falta context_verified/handoff_verified
   
2. admit_or_reject(quality_bar)
   → FAIL si input no cumple criterios
   
3. lock_goals()
   → Inmutabilizar goals para la sesión
   
4. run_cognitive_loop()
   → Procesar con LLM (interior = UNKNOWN)
   
5. compile_skill_to_code() [opcional]
   → Si input.skill presente
   
6. build_verify_evidence_packet()
   → Construir evidencia del engine
   
7. Mediciones CORE-01..14
   → Usar valores caller o auto_measure (default False)
   
8. Connectivity + ClosureCounters
   → Verificar cierre de gaps
   
9. ForensicProgrammingEnforcer.evaluate()
   → Aplicar máquina PASS
   
10. return {ok, verdict, forensic, llm_control="DENY"}
```

#### NO Ejecuta Hoy en Runner
- ChecklistSheriff (llamado vía gates, no cuerpo runner)
- ContextManifest object validator (optional, flag-based)
- COPY-FIRST ejecutor (PreGate lo llama, no inline)
- ClosureEngine instanciado (en standards, callable)
- QualityDAG.run() (flag-based, no exec en runner)
- FC-01..13 enforcement (parcial en evaluate, resto caller/CI)

### 3.2 STANDARDS — Control Plane

#### Núcleo Forense

| Componente | Path | Propósito |
|------------|------|----------|
| **forensic_core** | `extensions/wordflow/standards/forensic_core.py` | CORE14 + 4-pass + counters + máquina PASS |
| **forensic_contract** | `extensions/wordflow/standards/forensic_contract.py` | Dataclass contrato |
| **verdict_authority** | `extensions/wordflow/standards/verdict_authority.py` | Decide PASS/FAIL/BLOCK |
| **evidence_verifier** | `extensions/wordflow/standards/evidence_verifier.py` | Claim ≠ Evidence ≠ Verification |

#### Gestión de Gaps

| Componente | Path | Propósito |
|------------|------|----------|
| **gap_registry** | `extensions/wordflow/standards/gap_registry.py` | Ciclo de vida gaps (open→closed) |
| **closure_engine** | `extensions/wordflow/standards/closure_engine.py` | Árbitro de cierre |
| **checklist_sheriff** | `extensions/wordflow/standards/checklist_sheriff.py` | Sheriff checklist + applicability |

#### Reutilización (COPY-FIRST)

| Componente | Path | Propósito |
|------------|------|----------|
| **copy_first** | `extensions/wordflow/standards/copy_first.py` | Scanner AST + stem index |
| **symbol_index** | `extensions/wordflow/standards/symbol_index.py` | Índice AST cacheado |
| **adapt_imports** | `extensions/wordflow/standards/adapt_imports.py` | Adaptación automática imports |

#### Arquitectura y Política

| Componente | Path | Propósito |
|------------|------|----------|
| **context_manifest** | `extensions/wordflow/standards/context_manifest.py` | Manifest + validator |
| **executor_gates** | `extensions/wordflow/standards/executor_gates.py` | Pre/Post gates |
| **policy_snapshot** | `extensions/wordflow/standards/policy_snapshot.py` | Freeze de política |
| **applicability_engine** | `extensions/wordflow/standards/applicability_engine.py` | Tags → required |

#### Testing y Calidad

| Componente | Path | Propósito |
|------------|------|----------|
| **test_runner** | `extensions/wordflow/standards/test_runner.py` | Smoke tests offline |
| **quality_dag** | `extensions/wordflow/standards/quality_dag.py` | DAG de calidad |
| **quality_handlers** | `extensions/wordflow/standards/quality_handlers.py` | Handlers UNIT/ARCH |

#### Wiring y Scope

| Componente | Path | Propósito |
|------------|------|----------|
| **wiring_graph** | `extensions/wordflow/standards/wiring_graph.py` | Catalog graph |
| **scope_measure** | `extensions/wordflow/standards/scope_measure.py` | Scope + REQ tracking |
| **mission_edges** | `extensions/wordflow/standards/mission_edges.py` | Edge cases negocio |

---

## 4. FLUJO DE EJECUCIÓN (HOT PATH)

### 4.1 Diagrama de Secuencia

```
┌─ Input (raw_input + kwargs)
│
├─→ 1. PRE_GATE (ExecutorPreImplementGate)
│      ├─ require_context() → BLOCK si !context_verified
│      ├─ ExistingCodeScanner.scan()
│      ├─ ChecklistSheriff.verify() [si require_checklist]
│      └─ return {allow: bool, plan: Plan}
│
├─→ 2. QUALITY_BAR (admit_or_reject)
│      ├─ Validar input quality
│      └─ Reject si no cumple
│
├─→ 3. GOAL_LOCK (lock_goals)
│      ├─ Inmutabilizar goals
│      └─ Chain hash
│
├─→ 4. COGNITIVE_LOOP (run_cognitive_loop)
│      ├─ Procesar con LLM (interior UNKNOWN)
│      └─ Generar hipótesis
│
├─→ 5. [OPT] COMPILE_SKILL (skill_native_compiler)
│      └─ Si skill presente
│
├─→ 6. EVIDENCE ENGINE (build_verify_evidence_packet)
│      ├─ Construir EvidencePacket
│      └─ Verificar completitud
│
├─→ 7. MEASURES (CORE-01..14 + connectivity + counters)
│      ├─ core_auto_measure [default False]
│      ├─ connectivity checks
│      └─ closure counters
│
├─→ 8. POST_GATE (ExecutorPostVerifyGate)
│      ├─ VerdictAuthority.decide()
│      ├─ Aplicar máquina PASS
│      └─ Generar forensic report
│
└─→ 9. RETURN
       ├─ {ok, verdict, forensic, llm_control="DENY"}
       └─ Consumer responsable de acción

```

### 4.2 Estados de Output

```python
return {
    "ok": bool,                        # Ejecutó sin error
    "verdict": "PASS|FAIL|BLOCK",      # Decisión máquina
    "stage": "PRE|QUALITY|GOAL|...",   # Dónde falló si es negativa
    "forensic": {                      # Reporte forense
        "core_measures": [...],        # CORE-01..14
        "connectivity": {...},
        "counters": [0, 0, ...],
        "evidence_complete": bool,
        "reaudit_passed": bool,
        "quality_dag_ok": bool,
    },
    "llm_control": "DENY",             # Nunca permitir LLM aquí
    "path": "C-19_PROGRAMMING"         # Identificador path
}
```

---

## 5. CONTROL PLANE FORENSE

### 5.1 Máquina PASS (Definición Formal)

```python
PASS = (
    context_verified ✓
    AND handoff_verified ✓
    AND CORE_01 ✓ AND ... AND CORE_14 ✓
    AND pass_1 ✓ AND pass_2 ✓ AND pass_3 ✓ AND pass_4 ✓
    AND closure_counters == [0, 0, ..., 0]
    AND evidence_complete ✓
    AND final_clean_reaudit_passed ✓
    AND quality_dag_ok ✓
    AND NOT claim_used_as_pass
)
→ PASS

else → FAIL or BLOCK
```

### 5.2 CORE-01..14 (Medidas Críticas)

| ID | Medida | Default | Responsable |
|----|--------|---------|-------------|
| CORE-01 | Context verified | False | Entrada |
| CORE-02 | Handoff verified | False | Entrada |
| CORE-03 | Quality bar pass | False | quality_bar |
| CORE-04 | Goal lock done | False | goal_lock |
| CORE-05 | Cognitive loop ok | False | cognitive_loop |
| CORE-06 | Skill compile ok | False | compiler [opt] |
| CORE-07 | Evidence packet built | False | evidence engine |
| CORE-08 | Evidence packet verified | False | evidence engine |
| CORE-09 | Connectivity ok | False | graph check |
| CORE-10 | Closure counters zero | False | gap_registry |
| CORE-11 | Reaudit passed | False | auditor |
| CORE-12 | Quality DAG ok | False | quality_dag |
| CORE-13 | No LLM claim as pass | False | verdict_authority |
| CORE-14 | Forensic contract met | False | forensic_core |

### 5.3 4-Pass Auditoría

| Pasada | Enfoque | Checklist |
|--------|---------|-----------|
| **1. STRUCTURE** | Archivos y responsabilidades | ¿Existen todos los módulos? ¿Paths canónicos? |
| **2. CONNECTIVITY** | Importes y wiring | ¿Se llaman correctamente? ¿Faltan imports? |
| **3. BEHAVIOR** | Reglas y enforcement | ¿Código impone máquina PASS? ¿Bypass REQUIRED? |
| **4. VERIFY** | Cruzado vs código real | ¿Docs ↔ código match? ¿Deuda G1–G7? |

### 5.4 Context Manifest (Entrada Requerida)

```python
{
    "mission_id": "T13_BOOTSTRAP",
    "context_verified": True,           # ← REQUERIDO
    "handoff_verified": True,           # ← REQUERIDO
    "symbol_or_stem": "goal_lock",
    "dest": "extensions/wordflow/engine/goal_lock.py",
    "checklist": {...},                 # ← REQUERIDO si require_checklist
    "scan_roots": ["extensions/", "control-layer/"],
}
```

Sin `context_verified=True` → BLOCK inmediato.

---

## 6. INVENTARIO DE ARCHIVOS

### 6.1 Engine (extensions/wordflow/engine/)

```
code_path_runner.py                  (17 KB) — Hot path
programming_pipeline.py              (5.5 KB) — Pipeline
input_quality_bar.py                 (2.5 KB) — Quality
goal_lock.py                         (4 KB) — Goal lock
cognitive_loop.py                    (2.4 KB) — Cognitive
evidence_packet.py                   (3 KB) — Evidence
skill_native_compiler.py             (3.5 KB) — Skill compile
main_loop.py                         (9 KB) — Main loop
code_path_smoke.py                   (1.8 KB) — Smoke
[20+ más: policy, handoff, bridges, orchestrator*, …]
```

**Total:** ~80+ módulos en engine/

### 6.2 Standards (extensions/wordflow/standards/)

```
NÚCLEO FORENSE:
  forensic_core.py                   — PASS máquina
  forensic_contract.py               — Dataclass
  verdict_authority.py               — Decisión
  evidence_verifier.py               — Verify claims

GAPS:
  gap_registry.py                    — Lifecycle
  closure_engine.py                  — Árbitro
  checklist_sheriff.py               — Sheriff

REUTILIZACIÓN:
  copy_first.py                      — Scanner
  symbol_index.py                    — AST

ARQUITECTURA:
  context_manifest.py
  executor_gates.py
  policy_snapshot.py
  applicability_engine.py

TESTING:
  test_runner.py
  quality_dag.py
  quality_handlers.py

WIRING:
  wiring_graph.py
  scope_measure.py
  mission_edges.py

[15+ más: rule_engine, schema, adapt_imports, …]
```

**Total:** ~30+ módulos en standards/

### 6.3 Datos / Policy

```
extensions/wordflow/
  ├─ component_catalog.json          — Componentes declarados
  ├─ connect_catalog.json            — Conexiones declaradas
  ├─ ficha.v2.json                   — Ficha plugin universal

PIPELINE/
  ├─ 00_METODO_TRABAJO_Y_ARQUITECTURA.md
  ├─ ARQUITECTURA_WORDFLOW_PROGRAMMING.md
  ├─ WORDFLOW_PROGRAMMING_FORENSIC_MAP.md
  ├─ WORDFLOW_PROGRAMMING_MASTER.md
  ├─ ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md
  ├─ [50+ documentos arquitectura/auditoria]

.cursor/
  └─ rules/wordflow-programming.mdc

.github/workflows/
  └─ forensic-gates.yml              — CI forense

AGENTS.md                             — Autoridad docs
README.md                             — Descripción sistema
```

---

## 7. CONTRATOS Y ENFORCEMENT

### 7.1 Contratos de Arquitectura

| Contrato | Punto Enforcement | Validación |
|----------|-------------------|-----------|
| **ForensicCodeContract** | post_verify | VerdictAuthority.decide() |
| **EvidencePacket** | evidence_verifier | claim ≠ evidence ≠ verification |
| **ContextManifest** | require_context() | context_verified mandatory |
| **ChecklistClaim** | pre_gate | checklist_sheriff (si require_checklist) |
| **WiringGraph** | wiring_graph.load() | catalog connectivity |
| **PolicySnapshot** | freeze() | policy immutability |
| **GapRegistry** | closure_engine | open→closed ciclo |

### 7.2 Reglas Enforcement (No se bypasean)

```python
1. NO context_verified=True
   → BLOCK (no hay execución)

2. CORE-01..14 incompleto
   → FAIL (máquina requiere todos True)

3. 4 passes no lineales
   → FAIL (orden obligatorio: STRUCTURE → CONNECTIVITY → BEHAVIOR → VERIFY)

4. claim_used_as_pass=True
   → FAIL (LLM claim nunca cuenta como pass)

5. closure_counters != [0, 0, ..., 0]
   → FAIL (gaps deben cerrarse)

6. evidence_complete=False
   → FAIL (evidencia incompleta)

7. llm_control != "DENY" en hot path
   → BLOCK (LLM nunca permitido aquí)

8. runner escribe git directo
   → BLOCK (no permitido)

9. token en logs/chat
   → BLOCK (seguridad)

10. No verificación remota (READ-BACK)
    → FAIL (GitHub publish no verificado)
```

---

## 8. MÁQUINA DE DECISIÓN (PASS/FAIL/BLOCK)

### 8.1 Flujo de Veredicto

```
Input (context_verified, measures, evidence, …)
    │
    ├─ context_verified? NO
    │  └─→ BLOCK (no hay autoridad)
    │
    ├─ context_verified? SÍ
    │  ├─ Validar CORE-01..14
    │  │  └─ ¿Todos True? NO
    │  │     └─→ FAIL
    │  │  └─ ¿Todos True? SÍ
    │  │     ├─ Validar 4-pass orden
    │  │     │  └─ ¿Orden? NO
    │  │     │     └─→ FAIL
    │  │     │  └─ ¿Orden? SÍ
    │  │     │     ├─ Validar closure_counters
    │  │     │     │  └─ ¿Zeros? NO
    │  │     │     │     └─→ FAIL
    │  │     │     │  └─ ¿Zeros? SÍ
    │  │     │     │     ├─ Validar evidence_complete
    │  │     │     │     │  └─ ¿Complete? NO
    │  │     │     │     │     └─→ FAIL
    │  │     │     │     │  └─ ¿Complete? SÍ
    │  │     │     │     │     ├─ Validar reaudit_passed
    │  │     │     │     │     │  └─ ¿Passed? NO
    │  │     │     │     │     │     └─→ FAIL
    │  │     │     │     │     │  └─ ¿Passed? SÍ
    │  │     │     │     │     │     ├─ Validar quality_dag_ok
    │  │     │     │     │     │     │  └─ ¿OK? NO
    │  │     │     │     │     │     │     └─→ FAIL
    │  │     │     │     │     │     │  └─ ¿OK? SÍ
    │  │     │     │     │     │     │     ├─ Validar !claim_as_pass
    │  │     │     │     │     │     │     │  └─ ¿False? NO (LLM claim)
    │  │     │     │     │     │     │     │     └─→ FAIL
    │  │     │     │     │     │     │     │  └─ ¿False? SÍ
    │  │     │     │     │     │     │     │     └─→ ✅ PASS
    │  │     │     │     │     │     │     │
    │  │     │     │     │     │     │     └─ Generar forensic report
    │  │     │     │     │     │     │        return {ok=True, verdict="PASS"}
    │
```

### 8.2 Tabla de Decisión (Truth Table)

| context | CORE14 | 4-pass | counters | evidence | reaudit | dag | claim | **VEREDICTO** |
|---------|--------|--------|----------|----------|---------|-----|-------|--------------|
| NO      | —      | —      | —        | —        | —       | —   | —     | **BLOCK**    |
| SÍ      | NO     | —      | —        | —        | —       | —   | —     | **FAIL**     |
| SÍ      | SÍ     | NO     | —        | —        | —       | —   | —     | **FAIL**     |
| SÍ      | SÍ     | SÍ     | NO (≠0)  | —        | —       | —   | —     | **FAIL**     |
| SÍ      | SÍ     | SÍ     | SÍ (=0)  | NO       | —       | —   | —     | **FAIL**     |
| SÍ      | SÍ     | SÍ     | SÍ (=0)  | SÍ       | NO      | —   | —     | **FAIL**     |
| SÍ      | SÍ     | SÍ     | SÍ (=0)  | SÍ       | SÍ      | NO  | —     | **FAIL**     |
| SÍ      | SÍ     | SÍ     | SÍ (=0)  | SÍ       | SÍ      | SÍ  | SÍ    | **FAIL**     |
| SÍ      | SÍ     | SÍ     | SÍ (=0)  | SÍ       | SÍ      | SÍ  | NO    | **✅ PASS**  |

---

## 9. LÍMITES EXPLÍCITOS

### 9.1 Scope Actual de C-19

| Característica | ¿Implementado? | Impacto |
|---|---|---|
| **Pre-gate COPY-FIRST** | Parcial (scanner existe, no enforcement) | Riesgo: LLM puede generar en lugar de copiar |
| **Context BLOCK** | SÍ | PASS solo con context_verified=True |
| **Evidence verifier** | SÍ | claim ≠ evidence validado |
| **4-pass** | SÍ booleanos | Solo medidas binarias, no profundidad |
| **GapRegistry runtime** | SÍ en standards, NO garantizado en runner | Riesgo: gaps pueden quedar abiertos |
| **OPEN→CLOSED estado machine** | Documentado, NO verificado en runtime | Riesgo: gap puede reabrir |
| **cognitive_loop interior LLM** | SÍ presente, interior UNKNOWN | Riesgo: QA insuficiente |
| **Runner escribe git directo** | NO (explícito design) | Gen/adapt es externo al path |
| **LLM DENY enforcement** | SÍ return {llm_control="DENY"} | Responsable consumer respetar |
| **Skill compile opcional** | SÍ si skill presente | Bueno: no fuerza compilación |

### 9.2 Deuda Arquitectónica (G1–G7)

| ID | Issue | Estado | Severidad |
|----|-------|--------|-----------|
| **G1** | Índice engine incompleto | Mitigado doc REAL | Media |
| **G2** | Playbook > cableado | Cerrado (Sheriff/COPY-FIRST) | Baja |
| **G3** | FC no enforced | Parcialmente (evaluate + auto) | Media |
| **G4** | Standards secundarios | Doc-light mission_edges/scope_measure | Baja |
| **G5** | Bridges adyacentes | Siguen adyacentes, C-19 no solo bools | Baja |
| **G6** | Dual evidence | Cerrado evidence_merge | Cerrada |
| **G7** | CORE auto-measure | Parcial (core_auto_measure existe) | Media |

---

## 10. AUDITORÍA CRUZADA 3-PASADAS

### Pasada 1: STRUCTURE

**Pregunta:** ¿Existen todos los módulos?

```
✅ code_path_runner.py           SÍ (17 KB)
✅ forensic_core.py              SÍ
✅ gap_registry.py               SÍ
✅ programming_points_catalog.py SÍ
✅ applicability_engine.py       SÍ
✅ context_manifest.py           SÍ
✅ evidence_verifier.py          SÍ
✅ checklist_sheriff.py          SÍ
✅ copy_first.py + symbol_index  SÍ
✅ wiring_graph.py               SÍ
✅ component_catalog.json        SÍ
✅ .github/workflows/forensic-gates.yml SÍ
```

**Veredicto:** ✅ PASS — Inventario completo de archivos

### Pasada 2: CONNECTIVITY

**Pregunta:** ¿Están correctamente cableados?

```
✅ runner → forensic_core       SÍ (import/evaluate)
✅ runner → quality/goal/cog    SÍ
✅ measures default False       SÍ (fail-closed)
⚠️ Sheriff sempre llamado       PARCIAL (API measures + gates)
⚠️ Auto CORE medidores          AUSENTE (caller debe medir)
⚠️ DOC mismatch auto            PARCIAL (doc REAL corrige, no auto)
```

**Veredicto:** ⚠️ PARCIAL — Existen gaps en auto-wiring

### Pasada 3: BEHAVIOR

**Pregunta:** ¿Código impone máquina PASS?

```
✅ NO context → BLOCK           SÍ
✅ CORE incompleto → FAIL       SÍ
✅ 4 passes orden               SÍ
✅ counters ≠0 → FAIL           SÍ
✅ claim→PASS bloqueado         SÍ
❌ dev bypass REQUIRED          NO en runner
⚠️ OPEN→CLOSED enforcement      NO verificado en runtime
⚠️ Impact engine AST            NO (motor único)
```

**Veredicto:** ✅ PASS — Máquina respetada, algunos gaps residuales

---

## 11. GUÍA DE USO Y CHECKLIST

### 11.1 Cómo Llamar a run_code_path

```python
from extensions.wordflow.engine.code_path_runner import run_code_path
from extensions.wordflow.standards.context_manifest import ContextManifest

# 1. Preparar contexto
manifest = ContextManifest(
    mission_id="T13_BOOTSTRAP",
    context_verified=True,
    handoff_verified=True,
    symbol_or_stem="goal_lock",
    dest="extensions/wordflow/engine/goal_lock.py",
)

# 2. Llamar con kwargs completos
result = run_code_path(
    raw_input="Implementar goal_lock con 3-state machine",
    context_verified=True,
    handoff_verified=True,
    symbol_or_stem="goal_lock",
    dest="extensions/wordflow/engine/goal_lock.py",
    require_checklist=True,
    require_pre_gate=True,
    require_fc=False,
)

# 3. Analizar resultado
if result["verdict"] == "PASS":
    print("✅ PASS — Programación aprobada")
    forensic = result["forensic"]
    print(f"Evidence: {forensic['evidence_complete']}")
    print(f"Reaudit: {forensic['final_clean_reaudit_passed']}")
elif result["verdict"] == "FAIL":
    print(f"❌ FAIL en stage {result['stage']}")
    print(f"Detail: {result.get('detail', 'N/A')}")
elif result["verdict"] == "BLOCK":
    print(f"🚫 BLOCK — Entrada rechazada")
    print(f"Razón: {result.get('detail', 'No context')}")
```

### 11.2 Checklist Pre-Uso

**Antes de llamar a `run_code_path`:**

- [ ] ¿Tengo `context_verified=True`? (obligatorio)
- [ ] ¿Tengo `handoff_verified=True`? (obligatorio)
- [ ] ¿He preparado el ContextManifest?
- [ ] ¿Están las raíces de scan correctas?
- [ ] ¿He incluido COPY-FIRST en el plan?
- [ ] ¿Sé de qué código reutilizar?
- [ ] ¿He preparado el checklist si require_checklist=True?
- [ ] ¿He leído el output contract esperado?

### 11.3 Checklist Post-Veredicto

**Si PASS:**
- [ ] Revisar evidence en detail
- [ ] Verificar forensic report
- [ ] Confirmar CORE-01..14 todos True
- [ ] Confirmar closure_counters todos 0
- [ ] Publicar resultado en GitHub
- [ ] Ejecutar READ-BACK verificación

**Si FAIL:**
- [ ] Leer stage dónde falló
- [ ] Revisar detail del error
- [ ] Reparar según categoría (quality/goal/cog/evidence/measure)
- [ ] Re-llamar con kwargs corregidos

**Si BLOCK:**
- [ ] Verificar context_verified
- [ ] Verificar handoff_verified
- [ ] Revisar policy snapshot
- [ ] No reintentar sin contexto

---

## 12. REFERENCIAS Y ENLACES

### Documentos PIPELINE (En Repo)

- 📄 [PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md](../PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md)
- 📄 [PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md](../PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md)
- 📄 [PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md](../PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md)
- 📄 [PIPELINE/WORDFLOW_PROGRAMMING_MASTER.md](../PIPELINE/WORDFLOW_PROGRAMMING_MASTER.md)
- 📄 [PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md](../PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md)
- 📄 [PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md](../PIPELINE/WORDFLOW_PROGRAMMING_MASTER_UNICO.md)
- 📄 [PIPELINE/WORDFLOW_PROGRAMMING_ALL_IN_ONE.md](../PIPELINE/WORDFLOW_PROGRAMMING_ALL_IN_ONE.md)

### Código Fuente (En Repo)

- 🔗 [extensions/wordflow/engine/code_path_runner.py](../extensions/wordflow/engine/code_path_runner.py)
- 🔗 [extensions/wordflow/engine/programming_pipeline.py](../extensions/wordflow/engine/programming_pipeline.py)
- 🔗 [extensions/wordflow/standards/forensic_core.py](../extensions/wordflow/standards/forensic_core.py)
- 🔗 [extensions/wordflow/standards/verdict_authority.py](../extensions/wordflow/standards/verdict_authority.py)
- 🔗 [extensions/wordflow/standards/gap_registry.py](../extensions/wordflow/standards/gap_registry.py)
- 🔗 [extensions/wordflow/component_catalog.json](../extensions/wordflow/component_catalog.json)
- 🔗 [extensions/wordflow/connect_catalog.json](../extensions/wordflow/connect_catalog.json)

### Políticas y Rules

- 📋 [.cursor/rules/wordflow-programming.mdc](../.cursor/rules/wordflow-programming.mdc)
- 📋 [AGENTS.md](../AGENTS.md)
- 📋 [.github/workflows/forensic-gates.yml](../.github/workflows/forensic-gates.yml)

### Tabla Comparativa: Docs vs Código Real

| Documento | Scope | Estado | Dónde Leer |
|-----------|-------|--------|-----------|
| ARQUITECTURA_WORDFLOW_PROGRAMMING.md | Visión general + capas | ACTUAL ✓ | Inicio |
| WORDFLOW_PROGRAMMING_FORENSIC_MAP.md | Mapa detallado real | VERIFICADO ✓ | Profundidad |
| WORDFLOW_PROGRAMMING_MASTER.md | 3-pasadas auditoria | REFERENCIA ✓ | Validación |
| ARQUITECTURA_WORDFLOW_PROGRAMMING_REAL.md | Inventario code actual | CRUZADO ✓ | Veracidad |
| Este archivo (CONSOLIDADA) | TODO EN UNO | INTEGRAL ✓ | Guía rápida |

---

## 📊 RESUMEN EJECUTIVO

### Identidad del Sistema
- **Nombre:** Wordflow Programming Control Plane (C-19)
- **Tipo:** Sistema determinista fail-closed
- **Propósito:** Orquestar programación de código con auditoría forense
- **Garantía:** Si `context_verified=True` + máquina PASS = salida verificada

### Arquitectura Core
```
Entrada (context_verified ✓ + kwargs)
  ↓
PRE-GATE (COPY-FIRST scan)
  ↓
COGNITIVE PATH (quality → goal → loop → evidence)
  ↓
POST-GATE (forensic_core.evaluate)
  ↓
Salida (PASS/FAIL/BLOCK + llm_control="DENY")
```

### Garantías de Seguridad
✅ No LLM en hot path (siempre DENY)  
✅ Sin context = BLOCK inmediato  
✅ Sin evidence = FAIL  
✅ Claim LLM como pass = FAIL  
✅ Runner no escribe git directo  
✅ No secrets en logs  

### Mecanismos de Control
- **Pre-gate:** COPY-FIRST + context validation
- **Ejecutor:** 10-stage pipeline determinista
- **Post-gate:** Máquina PASS (14 condiciones binarias)
- **Auditoria:** 3-pasadas (structure, connectivity, behavior)

### Puntos de Riesgo Residuales
⚠️ GapRegistry puede no cerrarse automáticamente (caller responsable)  
⚠️ Cognitive_loop interior UNKNOWN (no audit)  
⚠️ Auto CORE measures parcial (default False)  
⚠️ OPEN→CLOSED SM no verificado en runtime  

### Próximos Pasos (Roadmap)
1. **T13:** Verificar bootstrap end-to-end
2. **T14:** Integrar maxbry_loop bridge
3. **T22:** Enforcement FC-02..13 en CI
4. **T48:** Re-auditoría 4-pasadas completa

---

**FIN DEL DOCUMENTO CONSOLIDADO**

*Versión 1.0 • 2026-08-18 • Auditoría Integral • No modificar sin trazabilidad*
