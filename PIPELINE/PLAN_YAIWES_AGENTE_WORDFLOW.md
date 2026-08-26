# README PLAN YAIWES v1

**Nombre oficial:** README PLAN YAIWES v1  
**Fuente de estructura:** README canónico + `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`  
**Repo:** maxbry123-commits/agentes · main  
**Agente:** Yaiwes v1  
**Regla:** NO reescribir `extensions/wordflow` (LEGACY). Solo COPY / REF / PLACEHOLDER.  
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
| 3º | **SALIDA 2** | Espejo motor → code-programming-engine/ |
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

El cierre debe coincidir con el árbol completo de `PLAN_100_ESTRUCTURA_DEFINITIVA.md`:

- `code-programming-engine/` (subestructura engine-modules, standards-forensic, schemas, tests…)
- `kernel-principal/` completo (control-layer, extension-kernel, reasoning-kernel, resource-governance, internal-bus, execution-manifest…)
- `input-layer/` (cli-entry, route-entry, cross-tool-session-import, reception)
- `definition-registry/` completo
- `control-governance/` completo
- `multi-workflow-engine/` (shared-services + instances/workflow-N)
- `execution-orchestration/` completo
- `execution-engine-pool/` completo
- `deploy-publish/` completo
- Nodos adicionales del plan: agent-fleet-parallelism, mesh-routing, pipeline-runtime, human-in-the-loop, observability, etc.
- `extensions/` como REFs
- `ORIGIN_MAP.md`, `COPY_MANIFEST.json`

### C. Gaps forenses (lo que falta para igualar el README)

| Gap | Severidad | Salida que lo cierra |
|-----|-----------|----------------------|
| Subárboles internos de kernel-principal, definition-registry, control-governance, multi-workflow-engine, execution-* | ALTO | **SALIDA 1** |
| Nodos §4.1 obligatorios (capability-passport, goal-dual-driver, dead-letter, mcp-transport, etc.) | ALTO | **SALIDA 1** |
| ORIGIN_MAP.md + COPY_MANIFEST.json | MEDIO | **SALIDA 4** |
| Despliegue 1 verification completo | ALTO | **SALIDA 5** |
| Espejo body motor (code-programming-engine) | MEDIO | **SALIDA 2** |
| REFs detallados + enganche LEGACY | BAJO | **SALIDA 3 / 7** |
| Checklist cierre 100% | ALTO | **SALIDA 8** |

### D. Lo que NO se toca

| Ámbito | Estado | Acción |
|--------|--------|--------|
| `extensions/wordflow` + kernel | materialized / LEGACY operativo | **REF — no reescribir** |
| `despliegue/` base | ya tiene manifests, schemas, auditoria, Opción A | Usar en Salida 5 |
| `code-programming-engine/` raíz | estructura iniciada | Completar espejo en Salida 2 |
| Stubs catalogs (gateway, openclaw, hermes) | documentados | No inventar vendor path |

### E. Veredicto auditoría

| Criterio | Resultado |
|----------|-----------|
| ¿El plan sigue la estructura del README/PLAN_100? | **SÍ** (9 salidas, orden 1→5→2→…→8) |
| ¿El árbol actual de agente-yaiwes = árbol final README? | **NO** — solo scaffold |
| ¿Hay que tocar 400+ archivos wordflow? | **NO** |
| ¿Al final debe quedar como el árbol del README/PLAN_100? | **SÍ** — eso es el criterio de cierre de Salida 8 |

**Resultado:** plan alineado. Ejecución pendiente desde **SALIDA 1**.

---

## DSL DAG (las 9 salidas)

Cada salida lleva: sheriff + validador + verificación + verificación cruzada + guardián + **checkpoint file nuevo**.

### SALIDA 1 — Nueva raíz completa
Materializar **todas** las carpetas del árbol PLAN_100. PLACEHOLDER.md en ESQ/MIX sin body. SOURCE.md en REF. Sin inventar código.

### SALIDA 5 — DESPLIEGUE 1
Según `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`: catalogs, pool, classifier_hook, deployment_01.yaml, verification.yaml.

### SALIDA 2 — Espejo motor
COPY (mismos SHA) engine/standards/schemas/tests → code-programming-engine/. Origen no se borra.

### SALIDA 0 — Contrato
Lista REAL/MIX/ESQ/REF + migration_plan.yaml.

### SALIDA 3 — REFs
SOURCE hacia piezas REALES existentes (control-layer, reception, catalogs, stubs, etc.).

### SALIDA 4 — Docs mapa
ORIGIN_MAP.md, COPY_MANIFEST.json, READMEs de bloque.

### SALIDA 6 — Modular / binding
programming-engine-binding, code-path-execution refs.

### SALIDA 7 — Enganche LEGACY
Marker LEGACY; no apagar hot path wordflow.

### SALIDA 8 — Cierre 100%
Checklist §4.1–4.3. Árbol final = árbol README/PLAN_100. verification + cierre_estructura_100.yaml.

---

## CRITERIO DE CIERRE (igual al README)

- [ ] Cero nodos del árbol definitivo faltantes
- [ ] Cero ítems §4.1 faltantes
- [ ] Salida 1 hecha
- [ ] Despliegue 1 auditado
- [ ] Espejo motor o GAP explícito
- [ ] extensions/wordflow LEGACY intacto
- [ ] ESQ = solo PLACEHOLDER + descripción
- [ ] 9 checkpoints creados

---

## ESTADO

| Ítem | Estado |
|------|--------|
| README PLAN YAIWES v1 | **HECHO** (este archivo) |
| PLAN_100 | HECHO |
| Salida 1 | PENDIENTE |
| Salida 5 | PENDIENTE (tras 1) |
| Salida 2 | PENDIENTE |

**Siguiente:** ejecutar **SALIDA 1**, luego **SALIDA 5**.

**TOTAL DE SALIDAS = 9**  
**TOTAL DE CHECKPOINTS A CREAR = 9**
