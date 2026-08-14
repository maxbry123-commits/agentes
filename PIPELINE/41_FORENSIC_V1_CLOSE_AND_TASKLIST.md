# PIPELINE/41 — Auditoría forense 2ª parte + lista V1 100%

**Fecha:** 2026-08-14  
**Scope:** T25–T48 + D0–D8 + tree `extensions/wordflow`  
**Objetivo:** cerrar Wordflow **versión 1** (código integrable, sin infra real OC/HF/SSH)

---

## PASADA 1 — Existencia material

| Hecho | Evidencia |
|-------|-----------|
| ~80+ módulos engine | tree engine/ en GH |
| ~70+ test_*.py | tree tests/ |
| T25–T48 commits | PIPELINE/36 |
| D0–D8 commits | PIPELINE/39 |
| CI workflow | `.github/workflows/test-wordflow.yml` |

**Veredicto P1:** material SÍ existe. No es stub vacío.

---

## PASADA 2 — Integración (el gap real)

Módulos **existen** pero **Orchestrator/main_loop NO los usan todos**:

| Módulo | ¿En Orchestrator.run_turn? |
|--------|----------------------------|
| Mission + Sheriff adapter | SÍ |
| CapabilityBrain + ExpertPanel | SÍ |
| StateAuthority | SÍ |
| gate_c00 / control_sheriff_bridge | **NO** |
| ContractRouter 13 tipos | **NO** |
| WorkflowDNA + dna_handoff | **NO** |
| ExecutionFacade / ParallelFacade | **NO** |
| Recovery | **NO** |
| Publish path | **NO** |
| Kimi policy may_invoke_llm | **NO** |
| EngineAttach + ports | **NO** |
| Bitácora / EvidenceGraph append | **NO** en orch |
| Push/Ping supervisor | **NO** en orch |

**Veredicto P2:** piezas sueltas. V1 ≠ “todo el código en un solo camino ejecutable”.

---

## PASADA 3 — Diferidos / faltantes

### Diferidos infra (NO codeables ahora sin Director)
- OC/Hermes binarios reales  
- HF download execute=true  
- SSH/Docker daemon  
- Token publish prod  
- Actions run_id (evidencia humana)

### Gaps codeables (SÍ para V1)
1. **Wire único V1:** OrchestratorV1 = mission→C00→contracts→panel→facade→dna→evidence→bitácora  
2. **main_loop ↔ Orchestrator** un solo entrypoint  
3. **Test e2e V1** un solo archivo que recorra el camino  
4. **Enchufe ficha.v2** wordflow montable (manifest mínimo)  
5. **Recovery en path** post DENY/FAIL  
6. **ContractRouter** en gate pre-ejecución  
7. **Export package** `__init__.py` API pública estable  
8. **CLAIM DSL** status V1 para CHAT_B  

---

## PASADA 4 — Mejoras (sin sobreingeniería)

| Mejora | Por qué |
|--------|--------|
| Un solo `run_v1()` | Evita 3 paths (main_loop / wave4 / wave5 / orch) |
| C00 obligatorio en orch | D6 existe y no se usa |
| DNA en cada turn ALLOW | Trazabilidad remoto |
| Fail-closed si panel DENY + recovery plan | Cierra N07 mínimo |
| No Fase4 minimax en V1 | Scope creep |

---

## 3 SIMULACIONES · cerrar 100% V1

### Sim A — Camino feliz
Input literal → GoalLock → Mission ALLOW → C00+contracts → Panel APPROVE → Facade noop → DNA → evidence → state ESPERAR_APROBACION → ok=true

### Sim B — Sheriff DENY
risk_score alto → DETENIDO → recovery.plan ESCALATE → ok=false stage=sheriff · sin publish

### Sim C — Panel REJECT + repair
Mission ALLOW · panel DENY → state REPAIR → recovery RETRY · sin facade

Si A/B/C pasan en test e2e → **V1 código 100%** (infra sigue fuera).

---

## LISTA NUEVA DE TAREAS — V1 CLOSE (solo codeable)

| ID | Tarea | LOC max | Salida |
|----|-------|---------|--------|
| V1-01 | `orchestrator_v1.py` wire: mission→gate_c00→contract_router→panel→optional facade→dna→evidence | ≤300 | 1 |
| V1-02 | Integrar recovery en DENY/FAIL paths | ≤150 | 1 |
| V1-03 | Integrar bitácora append en V1 turn | ≤150 | 1 |
| V1-04 | `entrypoint_v1.py` único: raw→OrchestratorV1 | ≤100 | 1 |
| V1-05 | `ficha.v2.json` + manifest wordflow extension | ≤120 | 1 |
| V1-06 | Export API pública `engine/__init__.py` estable | ≤120 | 1 |
| V1-07 | `tests/test_v1_e2e.py` Sim A/B/C | ≤250 | 1 |
| V1-08 | PIPELINE claim V1 + actualizar 40/41 status | ≤150 | 1 |

**Total salidas V1: 8**  
**Fuera V1 (lista futura):** Fase4 loops, OC/Hermes real, HF execute, SSH real, Acquire-OS full

### Microdiagrama V1

```
raw → mission → C00+contracts → panel/YAIWES → [facade?] → DNA → evidence → bitácora → state
         \→ DENY → recovery.plan → stop
```

**SIGUIENTE al Ok:** V1-01
