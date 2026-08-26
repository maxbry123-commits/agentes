# README PLAN YAIWES v1

**Nombre oficial:** README PLAN YAIWES v1  
**Fuente de estructura:** README canónico + `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`  
**Repo:** maxbry123-commits/agentes · main  
**Agente:** Yaiwes v1  
**Regla:** NO reescribir `extensions/wordflow` (LEGACY). Solo **COPY** / REF / PLACEHOLDER.  
**GitHub = truth.** 1 tarea = 1 salida. Binary PASS only with evidence. Fail-closed.

---

## 0. BLOQUE DE PROTECCIÓN — NO TOCAR

```text
PROHIBIDO:
- Cambiar el total de salidas (9).
- Reescribir extensions/wordflow materializado.
- Inventar código en nodos ESQ (solo PLACEHOLDER + descripción + PENDIENTE_CODE).
- PASS sin archivo de checkpoint nuevo + evidencia.

PERMITIDO:
- Crear checkpoint nuevo por salida.
- Actualizar status PENDING → PASS/FAIL con evidencia.
- Registrar GAP real sin borrar nodo.
```

---

## NÚMERO ÚNICO DE SALIDAS

# **TOTAL DE SALIDAS = 9**

| Orden | ID | Nombre |
|-------|-----|--------|
| 1º | **SALIDA 1** | Nueva raíz completa (árbol README/PLAN_100) |
| 2º | **SALIDA 5** | **DESPLIEGUE 1** |
| 3º | **SALIDA 2** | **COPIAR** motor → code-programming-engine/ |
| 4º | SALIDA 0 | Contrato |
| 5º | SALIDA 3 | REFs a piezas REALES |
| 6º | SALIDA 4 | Docs mapa (ORIGIN_MAP, COPY_MANIFEST) |
| 7º | SALIDA 6 | Modular / binding |
| 8º | SALIDA 7 | Enganche LEGACY |
| 9º | SALIDA 8 | Cierre 100% |

**Orden obligatorio:** 1 → 5 → 2 → (0/3/4/6/7) → 8

Cada salida **DEBE CREAR** archivo nuevo:  
`PIPELINE/checkpoints/SALIDA_N_YYYY-MM-DD.md`  
(Total esperado: **9** archivos de checkpoint.)

---

## AUDITORÍA FORENSE — ARCHIVOS vs ESTRUCTURA README / PLAN_100

### A. Estado actual de `agente-yaiwes/` (tree real @ main)

```text
agente-yaiwes/
├── README.md                          [REAL]
├── STRUCTURE.md                       [REAL — scaffold corto]
├── PLAN_100_ESTRUCTURA_DEFINITIVA.md  [REAL — plan maestro]
├── code-programming-engine/SOURCE.md  [REF]
├── kernel-principal/PLACEHOLDER.md
├── input-layer/PLACEHOLDER.md
├── definition-registry/PLACEHOLDER.md
├── control-governance/PLACEHOLDER.md
├── multi-workflow-engine/PLACEHOLDER.md
├── execution-orchestration/PLACEHOLDER.md
├── execution-engine-pool/PLACEHOLDER.md
├── deploy-publish/PLACEHOLDER.md
└── extensions-refs/PLACEHOLDER.md
```

**Conteo actual:** ~24 paths (solo top-level + placeholders).  
**Estado:** scaffold parcial. **NO** es el árbol 100% del README/PLAN_100.

### B. Árbol objetivo (README / PLAN_100) — lo que debe quedar al final

El cierre debe coincidir con el árbol completo de `PLAN_100_ESTRUCTURA_DEFINITIVA.md`.

### C. Gaps forenses

| Gap | Severidad | Salida |
|-----|-----------|--------|
| Subárboles internos faltantes | ALTO | **SALIDA 1** |
| Nodos §4.1 obligatorios | ALTO | **SALIDA 1** |
| ORIGIN_MAP + COPY_MANIFEST | MEDIO | **SALIDA 4** |
| Despliegue 1 verification | ALTO | **SALIDA 5** |
| **COPIAR** body motor a code-programming-engine | MEDIO | **SALIDA 2** |
| REFs + enganche LEGACY | BAJO | **SALIDA 3 / 7** |
| Checklist cierre 100% | ALTO | **SALIDA 8** |

### D. Lo que NO se toca

| Ámbito | Acción |
|--------|--------|
| `extensions/wordflow` + kernel | **REF — no reescribir** |
| `despliegue/` base | Usar en Salida 5 |
| Stubs catalogs | No inventar vendor path |

### E. Veredicto

Plan alineado al README. Árbol actual = scaffold. Al final = árbol README/PLAN_100. Wordflow no se reescribe.

---

## DSL DAG (las 9 salidas)

Cada salida: sheriff + validador + verificación + verificación cruzada + guardián + **checkpoint nuevo**.

### SALIDA 1 — Nueva raíz completa
Materializar todas las carpetas del árbol PLAN_100. PLACEHOLDER.md en ESQ/MIX. SOURCE.md en REF. Sin inventar código.

### SALIDA 5 — DESPLIEGUE 1
Según `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`.

### SALIDA 2 — COPIAR motor → code-programming-engine/
**Acción: COPIAR** (mismos blob SHA o copy determinista). Origen **no se borra**.

| Origen | Destino |
|--------|--------|
| `extensions/wordflow/engine/**` | `code-programming-engine/engine-modules/` |
| `extensions/wordflow/standards/**` | `code-programming-engine/standards-forensic/` |
| `extensions/wordflow/schemas/**` | `code-programming-engine/schema-contracts-io/` |
| tests relevantes | `code-programming-engine/module-tests/` |

Evidencia: SHA origen = SHA destino.

### SALIDA 0 — Contrato
Lista REAL/MIX/ESQ/REF + migration_plan.yaml.

### SALIDA 3 — REFs
SOURCE hacia piezas REALES existentes.

### SALIDA 4 — Docs mapa
ORIGIN_MAP.md, COPY_MANIFEST.json.

### SALIDA 6 — Modular / binding
programming-engine-binding, code-path-execution refs.

### SALIDA 7 — Enganche LEGACY
Marker LEGACY; no apagar hot path wordflow.

### SALIDA 8 — Cierre 100%
Checklist §4.1–4.3. Árbol final = árbol README/PLAN_100.

---

## CRITERIO DE CIERRE

- [ ] Cero nodos del árbol definitivo faltantes
- [ ] Salida 1 hecha
- [ ] Despliegue 1 auditado
- [ ] **COPIA** del motor hecha o GAP explícito
- [ ] extensions/wordflow LEGACY intacto
- [ ] 9 checkpoints creados

---

## ESTADO

| Ítem | Estado |
|------|--------|
| README PLAN YAIWES v1 | **HECHO** |
| Salida 1 | PENDIENTE |
| Salida 5 | PENDIENTE (tras 1) |
| Salida 2 (COPIAR) | PENDIENTE |

**Siguiente:** **SALIDA 1**, luego **SALIDA 5**.

**TOTAL DE SALIDAS = 9**  
**TOTAL DE CHECKPOINTS A CREAR = 9**
