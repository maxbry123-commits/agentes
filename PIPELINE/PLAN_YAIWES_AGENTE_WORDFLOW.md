# PLAN AGENTE YAIWES v1 — ALINEADO A ESTRUCTURA README + PLAN_100

**Fuente de verdad de estructura:**  
`agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`  
`agente-yaiwes/README.md` (estructura canónica)

**Nombre:** Agente Yaiwes v1  
**Repo:** maxbry123-commits/agentes · main  
**Regla:** NO reescribir extensions/wordflow operativo. Solo COPY / REF / PLACEHOLDER.  
**GitHub = truth.** 1 tarea = 1 salida. Binary PASS only with evidence. Fail-closed.

---

## 0. BLOQUE DE PROTECCIÓN — NO TOCAR ESTE PLAN NI EL PLAN_100

```text
PROHIBIDO:
- Cambiar el número de salidas (9).
- Reescribir extensions/wordflow materializado.
- Inventar código en nodos ESQ (solo PLACEHOLDER + descripción).
- Declarar PASS sin archivo de checkpoint nuevo + evidencia.

PERMITIDO:
- Crear checkpoint nuevo por salida.
- Actualizar status PENDING → PASS/FAIL con evidencia.
- Registrar GAP real sin borrar nodo.
```

---

## NÚMERO ÚNICO DE SALIDAS

# **TOTAL DE SALIDAS = 9**

| Orden | ID | Nombre | Prioridad |
|-------|-----|--------|-----------|
| 1º | **SALIDA 1** | Archivos de la nueva raíz (árbol completo) | P0 |
| 2º | **SALIDA 5** | **DESPLIEGUE 1** (documentos Opción A) | P0 |
| 3º | **SALIDA 2** | Espejo motor → code-programming-engine/ | P1 |
| 4º | SALIDA 0 | Contrato (puede ir junto a 1) | P1 |
| 5º | SALIDA 3 | REFs a piezas REALES | P1 |
| 6º | SALIDA 4 | Docs mapa (ORIGIN_MAP, COPY_MANIFEST) | P2 |
| 7º | SALIDA 6 | Modular / binding | P2 |
| 8º | SALIDA 7 | Enganche LEGACY | P2 |
| 9º | SALIDA 8 | Cierre 100% | P0 |

**Orden de ejecución obligatorio (Director):**  
**1 → 5 → 2 → resto (0/3/4/6/7) → 8**

---

## REGLA DE CHECKPOINT — ARCHIVO NUEVO OBLIGATORIO

Cada salida **DEBE CREAR** un archivo nuevo:

```text
PIPELINE/checkpoints/SALIDA_N_YYYY-MM-DD.md
```

- Nunca sobrescribir.
- Un archivo = una sola salida.
- Sin este archivo → no puede ser PASS.
- Al final: exactamente **9 archivos** de checkpoint.

---

## DSL DAG SCHEMA (obligatorio en las 9)

Cada salida instancia:

```yaml
id: SALIDA_N
nombre: "..."
tipo: CREATE | COPY | REF | PLACEHOLDER | ENGANCHE | VALIDATE

input_schema: { ... }
output_schema:
  required: [status, evidence, checkpoint_sha, cross_check]

sheriff:
  laws: [NO_SKIP, NO_ASSUME, NO_HALLUCINATION, NO_FAKE_PASS, NO_REWRITE_LEGACY, NO_TOUCH_PLAN]
  fail_closed: true

validador:
  schema_check: true
  evidence_required: true
  binary_pass: true

verificación:
  - type: tree | test | catalog | xray

verificación_cruzada:
  - against: PLAN_100 | component_catalog | connect_catalog | tree

guardián:
  on_fail: DENY
  on_pass: ALLOW_NEXT

checkpoint_file: PIPELINE/checkpoints/SALIDA_N_YYYY-MM-DD.md   # CREATE nuevo
```

---

## DETALLE DE LAS 9 SALIDAS (basado en PLAN_100 + README)

### SALIDA 1 — Nueva raíz completa (1º)
- **Objetivo:** Materializar todas las carpetas del árbol definitivo de `PLAN_100_ESTRUCTURA_DEFINITIVA.md`.
- **Acción:** CREATE carpetas + PLACEHOLDER.md (descripción + PENDIENTE_CODE) en hojas ESQ/MIX sin body. REF con SOURCE.md hacia paths canónicos.
- **Prohibido:** Inventar implementación.
- **Checkpoint:** CREATE `PIPELINE/checkpoints/SALIDA_1_YYYY-MM-DD.md`
- **Evidencia:** tree de `agente-yaiwes/` completo vs árbol del PLAN_100.

### SALIDA 5 — DESPLIEGUE 1 (2º, justo después de Salida 1)
- **Fuente:** `despliegue/` + `INSTRUCCIONES_GROK_OPCION_A.md` (u equivalente).
- **Entregas:**
  - capability registration (catalogs idempotente)
  - pool / instance / metering (copy, no inventar)
  - classifier_hook según doc
  - `despliegue/manifests/deployment_01.yaml`
  - `despliegue/auditoria/verification.yaml`
- **Checkpoint:** CREATE nuevo archivo.
- **Evidencia:** verification.yaml + status catalogs.

### SALIDA 2 — Espejo motor → code-programming-engine/ (3º)
- **Método:** COPY (mismos blob SHA o cp + commit). Origen no se borra.
- **Origen → Destino:**
  - `extensions/wordflow/engine/**` → `code-programming-engine/engine-modules/`
  - `extensions/wordflow/standards/**` → `code-programming-engine/standards-forensic/`
  - `extensions/wordflow/schemas/**` → `code-programming-engine/schema-contracts-io/`
  - tests relevantes → `module-tests/`
- **Checkpoint:** CREATE nuevo archivo.
- **Evidencia:** SHA origen = destino.

### SALIDA 0 — Contrato
- Lista nodos REAL / MIX / ESQ / REF.
- `despliegue/auditoria/migration_plan.yaml` estado.
- Checkpoint: CREATE nuevo.

### SALIDA 3 — REFs a piezas REALES
- SOURCE.md hacia: control-layer, reception, schemas, catalogs, gateway, openclaw/hermes stubs, maxbry_loop, github_deploy, etc.
- No copiar body innecesario. Solo REF.
- Checkpoint: CREATE nuevo.

### SALIDA 4 — Docs mapa
- ORIGIN_MAP.md, COPY_MANIFEST.json, READMEs por bloque principal.
- Checkpoint: CREATE nuevo.

### SALIDA 6 — Modular / binding
- code-path-execution, programming-engine-binding, refs p01–p12 si existen.
- Sin reimplementar monolito.
- Checkpoint: CREATE nuevo.

### SALIDA 7 — Enganche LEGACY
- Pocos archivos: catálogos/connect; marker LEGACY en wordflow viejo.
- **No apagar hot path** (`extensions/wordflow`).
- Checkpoint: CREATE nuevo.

### SALIDA 8 — Cierre 100%
- Checklist §4.1–4.3 de PLAN_100.
- `despliegue/auditoria/cierre_estructura_100.yaml`.
- Verificar: cero nodos faltantes del árbol, Despliegue 1 auditado, wordflow LEGACY intacto.
- Checkpoint: CREATE nuevo.
- **PASS solo con evidencia total de las 9.**

---

## QUÉ NO SE TOCA (auditoría forense)

| Ámbito | Estado | Acción |
|--------|--------|--------|
| extensions/wordflow (materialized) | Ya existe y opera | **REF / no tocar** |
| extensions/wordflow_kernel (materialized) | Ya existe | **REF / no tocar** |
| Stubs (intelligence_gateway, openclaw, hermes) | Documentados en catalogs | Dejar o PLACEHOLDER documentado |
| Partials (github_deploy, acquire) | Catalog status partial | Solo si Despliegue 1 lo exige |
| 400+ archivos wordflow | No requieren rewrite | **NO cambiar** |

---

## CRITERIO DE CIERRE

- [ ] Las 9 salidas con checkpoint nuevo cada una
- [ ] Árbol agente-yaiwes completo según PLAN_100
- [ ] Despliegue 1 hecho y verification.yaml
- [ ] Espejo motor o GAP explícito
- [ ] extensions/wordflow LEGACY intacto
- [ ] ESQ = solo PLACEHOLDER + descripción (sin código inventado)

---

## ESTADO ACTUAL

| Ítem | Estado |
|------|--------|
| PLAN_100 en main | HECHO |
| Este plan alineado | HECHO |
| Salida 1 (raíz completa) | PENDIENTE |
| Salida 5 (Despliegue 1) | PENDIENTE — siguiente tras Salida 1 |
| Salida 2 (espejo) | PENDIENTE |

**Siguiente orden del Director:** ejecutar **SALIDA 1**, luego **SALIDA 5**.

**TOTAL DE SALIDAS = 9**  
**TOTAL DE ARCHIVOS DE CHECKPOINT A CREAR = 9**
