# NOTAS-11 — SALIDA 2 / PASO 2
# Copia PLAN YAIWES en notas Grok. Original no se reescribe.

Fuente: PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
SHA: 91f6aac5 (igual en main y b7c9b89)
https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md

---

# README PLAN YAIWES v1 — PLAN EJECUTABLE COMPLETO

**Repo:** `maxbry123-commits/agentes` · **rama:** `main`  
**Agente:** Yaiwes v1  
**GitHub = única verdad.** 1 tarea = 1 salida. PASS solo con evidencia. FAIL-CLOSED.

**Documento de producción:** `PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md`

## ESTADO AUDITADO 2026-08-26

| Salida | Estado | Nota |
|---|---|---|
| S1 | PASS | checkpoint real |
| S2 | PASS | materialización; remote apply NO afirmado |
| S3 | PASS | ORIGIN_MAP + COPY_MANIFEST |
| S4–S9 | PASS | organización según PASO3 |
| S10 | PASS documental | 7 gaps técnicos OPEN |
| S11 | PASS | LEGACY/hot path preservado |
| S12 | PASS de proceso | gaps registrados |

**Regla:** gap técnico OPEN→CLOSED solo con evidencia real en `main`.

---

## SISTEMA REFACTORIA (anti-pérdida de código) — OBLIGATORIO

Técnica canónica para todo cambio de código productivo a partir de S10+ / fase 2.

### Paso 1 — Aislar (copiar, no editar in-place)
```text
despliegue/refactoria/<GAP_o_TASK_ID>/source/   ← copia exacta del original
Refactoria/<GAP_o_TASK_ID>/source/              ← misma copia en raíz Refactoria
```
Nunca modificar primero el original en `extensions/` o destinos canónicos.

### Paso 2 — Implementar en LOOP
```text
Refactoria/<GAP_o_TASK_ID>/new/                 ← versión nueva
```
- Usar `source/` como referencia permanente
- Bucle hasta cumplir acceptance (contratos, tests, sin pérdida de API pública)

### Paso 3 — Verificación cruzada ×3
1. Diff source/ vs new/ (APIs, imports críticos, comportamiento)
2. Tests contra new/
3. Checklist del gap/task + evidencia

**Solo si las 3 PASS:** integrar `new/` al path canónico PASO3.  
**Borrar original** solo con autorización Director + 3 verificaciones documentadas.  
**Nunca** borrar `Refactoria/*/source/` en el mismo task (queda evidencia).

### Prohibido
- Editar hot path sin paridad de tests
- PASS sin las 3 verificaciones
- Inventar body/adapters/schemas para cerrar gaps

---

## 1. FUENTES CANÓNICAS

1. `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`
2. `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
3. `agente-yaiwes/ORIGIN_MAP.md`
4. `agente-yaiwes/COPY_MANIFEST.json`
5. `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`
6. Este plan
7. `PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md`

## 2. REGLAS GLOBALES

```text
PROHIBIDO: inventar; reescribir code_path_runner sin paridad; duplicar lego;
PASS sin checkpoint; afirmar remote apply sin evidencia.
OBLIGATORIO: PASO3 + ORIGIN_MAP; checkpoint; COPY+LEGACY; Refactoria en cambios de code;
gaps solo con evidencia real.
```

### Regla LEGO
| Módulo | Autoridad única |
|---|---|
| goal_lock.py | execution-orchestration/goal-lock |
| cognitive_loop.py | execution-orchestration/mission-planning |
| evidence_packet.py | observability/evidence-packet |

## 3. TOTAL DE SALIDAS = 12 (estados arriba)

## 4. S10 — GAPS CANÓNICOS

| ID | Gap | Destino | Estado |
|---|---|---|---|
| G1 | SYMBOL_INDEX_PROGRAMMING.md | control-governance/symbol-index-wiring-graph/ | OPEN |
| G2 | Stage C-19 schemas | code-programming-engine/schema-contracts-io/ | OPEN |
| G3 | test→asserts index | code-programming-engine/module-tests/ | OPEN |
| G4 | Real CI log/trace | observability/trace-history/ | OPEN |
| G5 | p01→p12 E2E | code-programming-engine/code-path-execution/ | OPEN |
| G6 | Real adapters | execution-engine-pool/adapter-layer/ | OPEN |
| G7 | OpenClaw/Hermes bodies | execution-engine-pool/auxiliary-role-agents/ | OPEN |

## 5. DEPLOYMENT
remote_apply / readback: NOT_CLAIMED. deployment_01 validation_result: PENDING.

## 6. HOT PATH
extensions/wordflow/engine/code_path_runner.py — operativo e intacto.

## 7. CRECIMIENTO DE CAPACIDADES (fase 2)
OSS de otros agentes → ACQUIRE → ANALYZE gap → REUSE/PATCH/ADAPT → ficha v2 + enchufe → catalog → router.  
No clonar agentes enteros. No escribir de cero lo que se puede reciclar.
