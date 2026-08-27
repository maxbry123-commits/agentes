# MASTER DOCUMENTO 08: LOOP v6.0
## MAXBRY SUPER TEAM · 15 Capas + 3 Ciclos Paralelos

**Versión:** 1.0
**Fecha:** 2026-06-28
**Tipo:** Master Document
**Max chars:** 60,000
**Estado:** ✅ COMPLETO

---

## 1. INTRODUCCIÓN

El **Loop v6.0** es el sistema de iteración del orquestador. Tiene **15 capas** distribuidas en **3 ciclos paralelos** (A, B, C).

---

## 2. LAS 15 CAPAS

### CAPA 1 — Input Loop
Itera sobre el input hasta tener Definition Score ≥ 95%.

### CAPA 2 — Plan Loop
Itera sobre el plan hasta consenso del consejo.

### CAPA 3 — Execute Loop
Itera sobre la ejecución hasta completion.

### CAPA 4 — Validate Loop
Itera sobre validación hasta score ≥ 95%.

### CAPA 5 — Repair Loop
Pipeline de 5 pasos para reparar fallos.

### CAPA 6 — Learn Loop
Extrae lecciones y actualiza memoria.

### CAPA 7 — Adapt Loop
Adapta parámetros basado en resultados.

### CAPA 8 — Checkpoint Loop
Snapshots firmados cada N iteraciones.

### CAPA 9 — Consensus Loop
Ronda de votaciones del consejo.

### CAPA 10 — Monitor Loop
3 monitores activos: PAD, Anxiety, Drift.

### CAPA 11 — Cost Loop
Monitorea costo y ajusta perfil API.

### CAPA 12 — Escalate Loop
Escala a MAX cuando es necesario.

### CAPA 13 — Rollback Loop
Rollback automático si degradación.

### CAPA 14 — Deliver Loop
Itera sobre entrega hasta confirmación.

### CAPA 15 — Feedback Loop
Recolecta feedback post-entrega.

---

## 3. LOS 3 CICLOS PARALELOS

### LOOP A — EJECUCIÓN (Principal)
- Input → Plan → Execute → Validate → Deliver
- Es el ciclo de producción
- Prioridad alta
- Bloqueante para otros

### LOOP B — SUPERVISIÓN (Watchdog)
- Monitor → Detect → Alert → Decide → Act
- Vigila LOOP A
- Prioridad media
- No bloqueante

### LOOP C — APRENDIZAJE (Background)
- Observe → Analyze → Extract → Store → Update
- Aprende de LOOP A y B
- Prioridad baja
- Completamente async

---

## 4. DIAGRAMA

```
            ┌─────────────────────────────┐
            │     LOOP A — EJECUCIÓN      │
            │                             │
            │  Input → Plan → Exec → Val  │
            └─────────────┬───────────────┘
                          │
            ┌─────────────▼───────────────┐
            │     LOOP B — SUPERVISIÓN    │
            │                             │
            │  Monitor → Detect → Alert   │
            └─────────────┬───────────────┘
                          │
            ┌─────────────▼───────────────┐
            │     LOOP C — APRENDIZAJE    │
            │                             │
            │  Observe → Analyze → Store  │
            └─────────────────────────────┘
```

---

## 5. COORDINACIÓN ENTRE CICLOS

### A → B (cada 5 segundos)
LOOP A reporta estado a LOOP B.

### B → A (cuando alerta)
LOOP B puede pausar LOOP A si detecta problema.

### A → C (al completar)
LOOP A entrega datos a LOOP C al terminar.

### C → A (al aprender)
LOOP C actualiza skills/reglas que LOOP A usa.

---

## 6. PATRONES DE ITERACIÓN

### 6.1 Patrón Secuencial
```
A1 → B1 → C1 → A2 → B2 → C2
```

### 6.2 Patrón DAG Paralelo
```
     ┌─ A1 ─┐
S ──►├─ A2 ─┤──► E
     └─ A3 ─┘
```

### 6.3 Patrón Fractal
```
A1 = {
  A1.1, A1.2, A1.3 (donde cada uno es A en miniatura)
}
```

---

## 7. CHECKPOINTS Y REBUILD

### 7.1 Checkpoint
Cada N iteraciones (configurable, default 10):
- Snapshot del state completo
- Firmado con hash
- Almacenado en `/checkpoints/`

### 7.2 Rebuild
Permite volver a cualquier checkpoint:
```python
state.restore(checkpoint_id="cp-2026-06-28-001")
```

### 7.3 Rollback automático
Si loop detecta degradación:
- Encuentra último checkpoint "bueno"
- Restaura
- Reporta incidente

---

## 8. PIPELINE DE REPARACIÓN (5 PASOS)

### Paso 1 — Detect
Identifica tipo de fallo.

### Paso 2 — Diagnose
Diagnostica causa raíz.

### Paso 3 — Patch
Aplica parche correctivo.

### Paso 4 — Verify
Verifica que el parche funciona.

### Paso 5 — Document
Documenta el incidente y la solución.

---

## 9. PROPUESTAS M3 APLICADAS (INPUT/LOOP)

### 9.1 Definition Score Gate
Bloquea si Definition Score < 95%.

### 9.2 Auto-Repair Pipeline
Pipeline automático de 5 pasos.

### 9.3 3-Cycle Parallel
LOOP A + B + C en paralelo.

### 9.4 Checkpoint/Restore
Sistema de checkpoints firmados.

### 9.5 Max Mode Sampling
K samples + voto en decisiones críticas.

### 9.6 Goal-Stop
Criterio explícito de parada antes de deliver.

### 9.7 Dynamic Workflow
Workflow que se adapta mid-execution.

### 9.8 Multi-Source Research
Investigación con 5 fuentes.

### 9.9 Deterministic 90/10
90% código / 10% LLM.

### 9.10 Pre-Analysis Seed
Pipeline de 5 pasos antes de empezar.

---

## 10. MÉTRICAS DEL LOOP

- Latencia media por iteración
- Iteraciones promedio por tarea
- Tasa de éxito por capa
- Fallos por capa
- Tiempo total de loop
- Checkpoints generados
- Rollbacks ejecutados
</content>