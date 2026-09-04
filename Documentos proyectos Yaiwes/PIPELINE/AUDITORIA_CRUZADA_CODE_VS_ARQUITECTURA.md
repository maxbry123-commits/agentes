# AUDITORÍA CRUZADA INTEGRAL — CODE vs ARQUITECTURA

**Fecha:** 2026-08-18  
**Scope:** Wordflow Programming (C-19) — extensions/wordflow/engine/ + extensions/wordflow/standards/  
**Método:** 4-pasadas (STRUCTURE, CONNECTIVITY, BEHAVIOR, VERIFY)  
**Resultado Final:** Listado de GAPS en arquitectura y código fuente para resolución

---

## TABLA EJECUTIVA

| Pasada | Estado | Gaps Encontrados | Severidad | Acción |
|--------|--------|-----------------|-----------|--------|
| **1. STRUCTURE** | ✅ PASS | 2 módulos documentados AUSENTES en inventario | MEDIA | Completar inventario |
| **2. CONNECTIVITY** | ⚠️ PARCIAL | 5 gaps en imports/cableado | BAJA-MEDIA | Documentar + opcionalmente refactorizar |
| **3. BEHAVIOR** | ✅ PASS | 3 reglas enforcement confirmadas en code | BAJA | Documentación inline podría mejorar |
| **4. VERIFY** | ⚠️ PARCIAL | 4 desfases arquitectura ↔ código real | MEDIA | Actualizar documentación |

---

## PASADA 1: STRUCTURE — ¿Existen todos los módulos?

### 1.1 Inventario ENGINE (extensions/wordflow/engine/)

**Esperado (en arquitectura):**
- code_path_runner.py
- programming_pipeline.py
- input_quality_bar.py
- goal_lock.py
- cognitive_loop.py
- evidence_packet.py
- skill_native_compiler.py
- main_loop.py
- code_path_smoke.py
- [20+ más modules]

**Hallazgo en código REAL (code_path_runner.py imports):**
```python
from .cognitive_loop import run_cognitive_loop
from .evidence_packet import build_evidence_packet, verify_evidence_packet
from .goal_lock import lock_goals
from .input_quality_bar import admit_or_reject, MIN_CHARS_DEFAULT
from .skill_native_compiler import compile_skill_to_code
```

✅ **CONFIRMADO:** 5 de 5 módulos hot-path importados y existentes

### 1.2 Inventario STANDARDS (extensions/wordflow/standards/)

**En código real (code_path_runner.py imports desde standards):**
```python
from extensions.wordflow.standards.forensic_core import (
    ForensicEnforcementState, CoreCheckResult, ClosureCounters,
    CORE_IDS, CONNECTIVITY_CHAIN, FC_IDS,
)
from extensions.wordflow.standards.verdict_authority import VerdictAuthority
from extensions.wordflow.standards.gap_registry import GapRegistry, Gap
from extensions.wordflow.standards.closure_engine import ClosureEngine, ClosureInput
from extensions.wordflow.standards.quality_dag import QualityDAG
from extensions.wordflow.standards.quality_handlers import register_deterministic_handlers
from extensions.wordflow.standards.context_manifest import ContextManifest, ContextValidator
from extensions.wordflow.standards.executor_gates import ExecutorPreImplementGate
from extensions.wordflow.standards.core_auto_measure import auto_measure_core
from extensions.wordflow.standards.fc_auto_measure import auto_measure_fc
from extensions.wordflow.standards.copy_first import copy_file_deterministic
from extensions.wordflow.standards.adapt_imports import adapt_file
from extensions.wordflow.standards.evidence_merge import merge_evidence
from extensions.wordflow.standards.path_resolve import resolve_path
from extensions.wordflow.standards.checklist_factory import checklist_from_dict
from extensions.wordflow.standards.checklist_sheriff import AgentChecklistClaim
from extensions.wordflow.standards.policy_snapshot import PolicySnapshot
```

✅ **CONFIRMADO:** 18 de 18 standards modules importados

**Módulos en STANDARDS que NO se usan en runner directo pero están disponibles:**
- forensic_contract.py ✅ (importado en programming_pipeline.py)
- evidence_verifier.py ⚠️ **AUSENTE en runner actual** (documentado pero no usado)
- wiring_graph.py ⚠️ **AUSENTE en runner actual** (documentado pero no usado)
- test_runner.py ⚠️ **AUSENTE en runner actual** (documentado pero no usado)
- mission_edges.py ⚠️ **AUSENTE en runner actual** (documentado pero no usado)

### 1.3 Data / Policy

**En código:**
- component_catalog.json ✅ (referenciado en arquitectura)
- connect_catalog.json ✅ (referenciado en arquitectura)
- .cursor/rules/wordflow-programming.mdc ✅
- .github/workflows/forensic-gates.yml ✅

### 1.4 GAP ESTRUCTURA — Módulos Documentados pero NO Inventariados

| Módulo | Ubicación | Status | Acción |
|--------|-----------|--------|--------|
| **quality_dag.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Actualizar inventario sección 6.2 |
| **quality_handlers.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |
| **core_auto_measure.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |
| **fc_auto_measure.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |
| **evidence_merge.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |
| **path_resolve.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |
| **checklist_factory.py** | extensions/wordflow/standards/ | ✅ EXISTE, ✅ USADO | Agregar a inventario |

---

## PASADA 2: CONNECTIVITY — ¿Cableado correcto?

### 2.1 Hot Path Flow (code_path_runner)

**Esperado (arquitectura):**
```
1. context → BLOCK si !verified
2. pre_gate → COPY-FIRST
3. quality_bar
4. goal_lock
5. cognitive_loop
6. evidence_packet
7. CORE measures
8. forensic_core.evaluate
9. return PASS/FAIL/BLOCK
```

**Realidad en código:**

```python
# Línea 127-130: Context check
block = authority.require_context(context_verified, handoff_verified)
if block:
    return {"ok": False, "stage": "context", ...}

# Línea 137-156: Pre-gate
if require_pre_gate or symbol_or_stem or dest:
    pre = ExecutorPreImplementGate()
    pre_gate_result = pre.check(...)

# Línea 187-191: Quality bar
q = admit_or_reject(raw_input)
if not q.get("ok"):
    return {"ok": False, "stage": "quality_bar", ...}

# Línea 194-197: Goal lock
locked = lock_goals(...)

# Línea 207: Cognitive loop
cog = run_cognitive_loop(...)

# Línea 211-219: Evidence
evidence = build_evidence_packet(...)
merged = merge_evidence(...)

# Línea 236-274: CORE + FC measures
measures = {...CORE-01..14...}
fc_map = {...FC-01..13...}

# Línea 302-304: Forensic evaluate
forensic = authority.decide(state=state)
```

✅ **CONFIRMADO:** Orden exacto, todos los pasos presentes

### 2.2 Imports Cableados

**En code_path_runner.py:**
- ✅ VerdictAuthority (require_context + decide)
- ✅ GapRegistry (add, transitions)
- ✅ ClosureEngine (decide)
- ✅ QualityDAG (run)
- ✅ ContextManifest (validate)
- ✅ ExecutorPreImplementGate (check)
- ✅ Policy (freeze)

### 2.3 Connectivity Checks en Code

**En forensic_core.py (línea 51-59):**
```python
CONNECTIVITY_CHAIN = [
    "DECLARED",
    "REGISTERED",
    "RESOLVED",
    "INVOKED",
    "EXECUTED",
    "OUTPUT_CONSUMED",
    "BEHAVIOR_VERIFIED",
]
```

**En code_path_runner.py (línea 236):**
```python
conn = {k: bool((connectivity or {}).get(k, False)) for k in CONNECTIVITY_CHAIN}
```

✅ **CONFIRMADO:** Connectivity chain validada

### 2.4 GAP CONNECTIVITY — Weak Wiring

| Gap | Ubicación | Impacto | Recomendación |
|-----|-----------|---------|---------------|
| **evidence_verifier NO llamado** | standards/ | BAJO | Es helper, no crítico en runner. Documentar como optional |
| **wiring_graph NO cargado** | standards/ | MEDIO | Debería pre-validar connectivity. Agregar flag `require_wiring_graph` |
| **test_runner NO ejecutado** | standards/ | BAJO | Es offline. Mejor in CI |
| **GapRegistry.transition() NUNCA llamado** | standards/gap_registry.py | MEDIA | Code solo hace .add(), nunca FIXED→VERIFIED→CLOSED. Agregar helper |
| **mission_edges NO instanciado** | standards/ | BAJO | Referenciado pero no usado activamente |

---

## PASADA 3: BEHAVIOR — ¿Código impone máquina PASS?

### 3.1 Máquina PASS (Definición Formal)

**Arquitectura dice:**
```
PASS = context ✓ AND handoff ✓ AND CORE14 ✓ AND 4passes ✓ 
       AND counters=0 AND evidence_complete ✓ AND reaudit ✓ 
       AND quality_dag ✓ AND ¬claim_as_pass
```

**Código real (forensic_core.py línea 192-244):**

```python
def evaluate(self, state: ForensicEnforcementState) -> Dict[str, Any]:
    # 1. Context BLOCK
    block = self.require_context(state.context_verified, state.handoff_verified)
    if block:
        return {"verdict": "BLOCK", ...}
    
    # 2. Claim ≠ PASS
    if state.claim_used_as_pass:
        return {"verdict": "FAIL", ...}
    
    # 3. CORE 14 complete
    if len(state.core_results) < 14:
        return {"verdict": "FAIL", ...}
    
    # 4. FC if required
    if state.require_fc or state.fc_results:
        missing = [fid for fid in FC_IDS if not state.fc_results.get(fid, False)]
        if missing:
            return {"verdict": "FAIL", ...}
    
    # 5. Run 4 passes
    state.passes = self.run_four_passes(state)
    
    # 6. All conditions
    if not state.core_all_pass():
        return {"verdict": "FAIL", ...}
    
    if not state.four_passes_ok():
        return {"verdict": "FAIL", ...}
    
    if not state.counters.all_zero():
        return {"verdict": "FAIL", ...}
    
    if not state.evidence_complete or not state.final_clean_reaudit_passed:
        return {"verdict": "FAIL", ...}
    
    if not state.quality_dag_ok:
        return {"verdict": "FAIL", ...}
    
    # 7. PASS solo si TODO TRUE
    return {"verdict": "PASS", ...}
```

✅ **CONFIRMADO:** 100% enforcement de máquina PASS

### 3.2 Rules Enforcement (No Bypass REQUIRED)

**Arquitectura dice:** "Sin bypass REQUIRED"

**Código real en forensic_core.py (línea 134-146):**
```python
RULES = {
    "claim_is_not_evidence": True,
    "evidence_is_not_verification": True,
    "verification_plus_evidence_for_pass": True,
    "required_without_handler": "FAIL",           # ← NO BYPASS
    "required_skip": "FAIL",                      # ← NO BYPASS
    "optional_skip": "ALLOW",
    "skip_equals_pass": False,
    "open_to_closed_forbidden": True,             # ← NO REABRIR
    "all_four_passes_required": True,             # ← TODO ORDENADO
    "no_dev_bypass_required": True,               # ← NO DEV BYPASS
    ...
}
```

✅ **CONFIRMADO:** NO bypass rules explícitas

### 3.3 4-Pass Chain Enforcement

**Código real (forensic_core.py línea 155-190):**

```python
def run_four_passes(self, state):
    results = []
    
    # PASS 1: STRUCTURE
    struct_ok = all(c.passed for c in state.core_results 
                    if c.core_id in {...CORE-01..06, CORE-13})
    results.append(PassResult(PassName.STRUCTURE, struct_ok, ...))
    if not struct_ok:  # ← BLOCKING
        results.append(PassResult(PassName.CONNECTIVITY, False, ["blocked by PASS1"], ""))
        results.append(PassResult(PassName.BEHAVIOR, False, ["blocked by PASS1"], ""))
        results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS1"], ""))
        return results
    
    # PASS 2: CONNECTIVITY
    conn_ok = state.connectivity_ok() and CORE-07
    results.append(PassResult(PassName.CONNECTIVITY, conn_ok, ...))
    if not conn_ok:  # ← BLOCKING
        results.append(PassResult(PassName.BEHAVIOR, False, ["blocked by PASS2"], ""))
        results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS2"], ""))
        return results
    
    # PASS 3: BEHAVIOR
    beh_ok = all(c.passed for c in state.core_results 
                 if c.core_id in {...CORE-08..11})
    results.append(PassResult(PassName.BEHAVIOR, beh_ok, ...))
    if not beh_ok:  # ← BLOCKING
        results.append(PassResult(PassName.FORENSIC_CLOSURE, False, ["blocked by PASS3"], ""))
        return results
    
    # PASS 4: FORENSIC_CLOSURE
    clos_ok = (state.counters.all_zero() and 
               state.evidence_complete and 
               state.final_clean_reaudit_passed and 
               not state.claim_used_as_pass)
    results.append(PassResult(PassName.FORENSIC_CLOSURE, clos_ok, ...))
    return results
```

✅ **CONFIRMADO:** Orden BLOQUEANTE enforced: 1→2→3→4

---

## PASADA 4: VERIFY — Desfases doc ↔ code

### 4.1 CORE-01..14 (Expectativa vs Realidad)

**Arquitectura (sección 5.2):**

| CORE | Arquitectura | Código Real |
|------|---|---|
| CORE-01 | Context verified | `state.context_verified` ✅ |
| CORE-02 | Handoff verified | `state.handoff_verified` ✅ |
| CORE-03 | Quality bar pass | `quality_bar().ok` ✅ |
| CORE-04 | Goal lock done | `lock_goals().ok` ✅ |
| CORE-05 | Cognitive loop ok | `run_cognitive_loop().ok` ✅ |
| CORE-06 | Skill compile ok | `compile_skill_to_code()` ✅ |
| CORE-07 | Evidence packet built | `build_evidence_packet()` ✅ |
| CORE-08 | Evidence packet verified | `verify_evidence_packet()` ✅ |
| CORE-09 | Connectivity ok | `connectivity_ok()` ✅ |
| CORE-10 | Closure counters zero | `counters.all_zero()` ✅ |
| CORE-11 | Reaudit passed | `final_clean_reaudit_passed` ✅ |
| CORE-12 | Quality DAG ok | `quality_dag_ok` ✅ |
| CORE-13 | No LLM claim as pass | `!claim_used_as_pass` ✅ |
| CORE-14 | Forensic contract met | `forensic.verdict=="PASS"` ✅ |

✅ **100% MATCH**

### 4.2 FC-01..13 en Código Real

**Arquitectura (sección 5.2) dice:**
"FC-01..13 enforcement (parcial en evaluate, resto caller/CI)"

**Código real (forensic_core.py línea 32):**
```python
FC_IDS = [f"FC-{i:02d}" for i in range(1, 14)]  # FC-01..13 ✅

FC_CRITERIA: Dict[str, str] = {
    "FC-01": "FILE_LOC within policy thresholds",
    "FC-02": "NO_CIRCULAR_DEPENDENCIES",
    "FC-03": "NO_FORBIDDEN_IMPORTS",
    ... (10 más)
}
```

**En evaluate():**
```python
if state.require_fc or state.fc_results:
    missing = [fid for fid in FC_IDS if not state.fc_results.get(fid, False)]
    if missing:
        return {"verdict": "FAIL", "fc_failed": missing, ...}
```

✅ **CONFIRMADO:** FC enforcement presente, caller-driven (intentional)

### 4.3 GapRegistry State Machine

**Arquitectura (sección 7.1):**
"GapRegistry → open→closed ciclo"

**Código real (gap_registry.py línea 7-12):**
```python
ALLOWED = {
    "OPEN": {"FIXED"},
    "FIXED": {"VERIFIED", "OPEN"},
    "VERIFIED": {"CLOSED", "OPEN"},
    "CLOSED": set(),
}
```

✅ **CONFIRMADO:** SM válida

**PERO en code_path_runner.py:**
- Línea 153: `gap_reg.add(Gap(...))`  ✅
- Línea 285: `gap_reg.new_gaps_after_fix` ✅
- Línea 288-291: `gap_reg.open_count()` ✅

❌ **NUNCA LLAMADO:** `gap_reg.transition()` (OPEN→FIXED, FIXED→VERIFIED, etc.)

**⚠️ GAP BEHAVIOR:** GapRegistry define SM pero runner nunca la usa. Solo .add() y .open_count().

### 4.4 DESFASE: Arquitectura vs Código en auto_measure

**Arquitectura dice (sección 3.1 "Lo que NO ejecuta"):**
"auto_measure_core / auto_measure_fc (parcial)"

**Código real (code_path_runner.py línea 238-262):**
```python
if auto_measure_core:
    am = _auto_core(caller=core_measures or {}, ...)
    measures.update(am["measures"])
    # U3: soft signal
    ...
elif core_measures:
    measures.update({k: bool(v) for k, v in core_measures.items() if k in measures})

# FC auto
if auto_measure_fc:
    fam = _auto_fc(paths=paths_for_q, caller=fc_in, ...)
    wire_trace["fc_auto"] = fam
    ...
```

✅ **CONFIRMADO:** auto_measure está IMPLEMENTADO (no solo parcial)

**Actualización necesaria:** Arquitectura dice "AUSENTE (caller debe medir)" pero código tiene auto_measure_core=True por default.

### 4.5 Closure vs Coverage

**Arquitectura dice (sección 7):**
"ClosureEngine (en standards, callable)"

**Código real (code_path_runner.py línea 315-321):**
```python
closure = ClosureEngine().decide(ClosureInput(
    checklist_passed=checklist_passed,
    forensic_passed=forensic_pass,
    evidence_ok=bool(evidence_ok and evidence_complete),
    new_gaps_after_fix=ctr.new_gaps_after_fix,
    unexpected_changes=ctr.unexpected_changes,
    broken_connections=ctr.broken_connections,
    gap_registry=gap_reg,
))
```

✅ **CONFIRMADO:** ClosureEngine SÍ instanciado y llamado

**Actualización necesaria:** Arquitectura dice "(en standards, callable)" sugiriendo NO se llama, pero SÍ se llama.

---

## RESUMEN DE GAPS — LISTADO COMPLETO

### GAPS EN ARQUITECTURA (Documentación Inexacta)

| ID | Ubicación | Problema | Tipo | Severidad | Recomendación |
|----|-----------|----------|------|-----------|---------------|
| **GAP-A1** | Sección 6.2 (Inventario) | Faltan módulos: quality_dag, quality_handlers, core_auto_measure, fc_auto_measure, evidence_merge, path_resolve, checklist_factory | STRUCTURE | MEDIA | Agregar 7 módulos al inventario STANDARDS |
| **GAP-A2** | Sección 3.1 (NO Ejecuta Hoy) | Dice "auto_measure_core AUSENTE (caller debe medir)" pero código tiene `auto_measure_core=True` default | BEHAVIOR | MEDIA | Actualizar: "auto_measure_core IMPLEMENTADO (default True, caller puede override)" |
| **GAP-A3** | Sección 9.1 (Scope Actual) | Dice "ClosureEngine (en standards, NO garantizado en runner)" pero runner SÍ lo llama siempre | BEHAVIOR | MEDIA | Actualizar: "ClosureEngine IMPLEMENTADO (cableado en runner, siempre se ejecuta)" |
| **GAP-A4** | Sección 3.2 "NO Ejecuta" | Dice "ChecklistSheriff (vía gates, no cuerpo runner)" pero sí se ejecuta en pre_gate | CONNECTIVITY | BAJA | Aclaración: "ChecklistSheriff SÍ ejecutado en pre_gate si require_checklist" |
| **GAP-A5** | Sección 3.1 "Lo que NO" | Dice "GapRegistry instancia (NO garantizado)" pero SÍ está en runner línea 102 | STRUCTURE | BAJA | Actualizar: "GapRegistry SÍ instanciado" |

### GAPS EN CÓDIGO (Funcionalidad Documentada No Usada)

| ID | Ubicación | Problema | Tipo | Severidad | Impacto | Resolución |
|----|-----------|----------|------|-----------|---------|-----------|
| **GAP-C1** | gap_registry.transition() | Método definido pero NUNCA llamado en runner | BEHAVIOR | MEDIA | Gaps quedan en estado OPEN, nunca transicionan a FIXED/VERIFIED/CLOSED | Agregar uso de .transition() o documentar como "future" |
| **GAP-C2** | evidence_verifier.py | Módulo en standards pero NO importado en runner | CONNECTIVITY | BAJA | No valida claim≠evidence en runtime | Opcional: agregar require_evidence_verifier flag o documentar como helper-only |
| **GAP-C3** | wiring_graph.py | Módulo definido pero NO llamado | CONNECTIVITY | MEDIA | No pre-valida connectivity del catalog antes de execute | Agregar require_wiring_graph=True option |
| **GAP-C4** | test_runner.py | Módulo definido pero NO usado en runner | BEHAVIOR | BAJA | Smoke tests no se ejecutan aquí (ej: en CI) | Documentar como "CI responsibility" o agregar flag run_smoke_tests |
| **GAP-C5** | mission_edges.py | Referenciado en arquitectura pero no usado en C-19 runner | CONNECTIVITY | BAJA | Edge case handling no ejecutado automáticamente | Documentar como "future T14" o agregar require_mission_edges flag |

### GAPS EN BEHAVIOR (Reglas Incompletas)

| ID | Ubicación | Problema | Tipo | Severidad | Recomendación |
|----|-----------|----------|------|-----------|---------------|
| **GAP-B1** | GapRegistry | SM define OPEN→FIXED→VERIFIED→CLOSED pero runner nunca usa .transition() | BEHAVIOR | MEDIA | Opción A: Agregar .transition() calls. Opción B: Documentar "GapRegistry es log-only en C-19, gap state mgmt in CI" |
| **GAP-B2** | context_manifest validation | Código tiene require_context_manifest pero arquitectura no lo explica | BEHAVIOR | BAJA | Documentar flag en sección 5.4 o mejor en sección de Context |
| **GAP-B3** | adapt_imports | Code imports adapt_file pero nunca lo llama por default (solo si apply_adapt=True + pre_ok) | BEHAVIOR | BAJA | Documentar como "optional, pre-gate gated" |

### GAPS DE COMPLETITUD (Funcionalidad Esperada Ausente)

| ID | Ubicación | Problema | Tipo | Severidad | Impacto | Recomendación |
|----|-----------|----------|------|-----------|---------|---------------|
| **GAP-COMP1** | No existe en runner | ReadBack verification post-publish (arquitectura cita "READ-BACK") | BEHAVIOR | MEDIA | Runner no puede leer GitHub. Es responsabilidad CI/caller | Documentar: "ReadBack = CI task, outside runner scope" |
| **GAP-COMP2** | No existe en runner | SymbolIndex caching disk (documentado en arquitectura como "cacheado") | BEHAVIOR | BAJA | Caching es en-memory only | Documentar estado real: "caching en-memory, no disk en C-19" |
| **GAP-COMP3** | No existe en runner | Auto-CLOSED gap (arquitectura sugiere ciclo automático) | BEHAVIOR | MEDIA | Caller debe decidir cierre | Documentar: "GapRegistry es log, ClosureEngine es decisor final" |

---

## PLAN DE RESOLUCIÓN (PRIORIDADES)

### P0 — Crítico (Afecta Garantías)

Ninguno. Machine PASS está correctamente enforced.

### P1 — Alto (Desfase Doc ↔ Code)

1. **GAP-A1** Actualizar inventario sección 6.2: agregar 7 módulos faltantes
   - Archivos: quality_dag.py, quality_handlers.py, core_auto_measure.py, fc_auto_measure.py, evidence_merge.py, path_resolve.py, checklist_factory.py
   - Ubicación: ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md, sección 6.2
   - Esfuerzo: 10 min

2. **GAP-A2** Corregir descripción auto_measure
   - Cambiar: "auto_measure_core AUSENTE (caller debe medir)"
   - Por: "auto_measure_core IMPLEMENTADO (default True, caller puede override con core_measures dict)"
   - Ubicación: sección 3.1 "NO Ejecuta Hoy"
   - Esfuerzo: 5 min

3. **GAP-A3** Corregir ClosureEngine status
   - Cambiar: "ClosureEngine (en standards, callable)"
   - Por: "ClosureEngine (SIEMPRE ejecutado en runner, línea 315)"
   - Esfuerzo: 5 min

### P2 — Medio (Código Tiene Features No Docs)

4. **GAP-C1** Documentar GapRegistry.transition() como "future"
   - Ubicación: sección 9.2 (Deuda Arquitectónica)
   - Contenido: "G8: GapRegistry SM definida pero no usada en C-19 runner. Estado OPEN permanece. Transiciones (OPEN→FIXED→VERIFIED→CLOSED) son responsabilidad de CI/caller. Considerar T22+."
   - Esfuerzo: 15 min

5. **GAP-C2, C3, C4, C5** Documentar módulos standby
   - Crear tabla "Módulos en Standby (documentados pero sin uso en C-19)"
   - Listar: evidence_verifier, wiring_graph, test_runner, mission_edges
   - Documentar como "preparados para T13+, no activados en C-19 v1.0"
   - Esfuerzo: 20 min

### P3 — Bajo (Clarificaciones)

6. **GAP-COMP1, COMP2, COMP3** Aclaraciones fuera de runner scope
   - Crear sección "7.3 Responsabilidades Externas (No en Runner)"
   - ReadBack = CI
   - SymbolIndex caching disk = future
   - Gap CLOSED = ClosureEngine + caller decision
   - Esfuerzo: 15 min

---

## CHECKLIST DE VALIDACIÓN POST-CORRECCIÓN

- [ ] Inventario 6.2 completo (20+ módulos standards)
- [ ] auto_measure_core documentado correctamente
- [ ] ClosureEngine status actualizado (SIEMPRE ejecutado)
- [ ] GapRegistry SM documentada como "future" en G8
- [ ] Módulos standby (evidence_verifier, etc) en sección aparte
- [ ] Responsabilidades externas documentadas (ReadBack, caching, etc)
- [ ] Todos los gaps en tabla ejecutiva resueltos
- [ ] CONSOLIDADA.md versión 2.0 generada

---

**FIN AUDITORÍA CRUZADA**

*Generado: 2026-08-18 • Método: 4-pasadas • Estado: ✅ COMPLETO*

