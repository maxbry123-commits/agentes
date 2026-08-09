# PIPELINE 05 — Auditoría 5 Pasadas (Gaps + Fallos)

**Fecha:** 2026-08-09  
**Estado:** PERFIL INCORPORADO  
**Fuente:** Auditoría de documentos G1-G4 + SALIDA-01 + Guías de despliegue

---

## 1. Estado general

```yaml
estado_general: |
  Núcleo (G1), Research (G2) y DAG/Sheriff (G3) están especificados al 100% con código.
  Capa de Control (G4) solo tiene el 25% (doc1).
  SALIDA-01 consolida e integra Temporal, pero aún es diseño, no código ejecutable.
  Guías de despliegue están desactualizadas (mencionan Dagu en lugar de Temporal).
```

---

## 2. PASADA 1 — Cobertura de documentos

| Documento | Estado | Observación |
|-----------|--------|-------------|
| A01 / A02 / A03 | DUPLICADO | Contenido ≈ G1/G2/G3. G es la versión definitiva |
| G1-doc1..4 (Núcleo) | ✅ COMPLETO | Código Python completo (state, events, contracts, tests) |
| G2-doc1..4 (Research) | ✅ COMPLETO | Contratos + Protocols (stubs de Sandbox/Memory) |
| G3-doc1..4 (DAG/Sheriff) | ✅ COMPLETO | DAG validator, Sheriff, políticas, tests |
| G4-doc1 (Capa de Control) | ❌ INCOMPLETO | Solo manifest + state.json (25%) |
| SALIDA-01 | ⚠️ PARCIAL | Diseño de integración + Temporal (no código ejecutable) |
| GUIA-DESPLIEGUE-* | ⚠️ DESACTUALIZADO | Menciona Dagu; SALIDA-01 eligió Temporal |
| GUIA-MAESTRA-00 | ✅ COMPLETO | Plan de 6 salidas |

**Conclusión:** Faltan G4-doc2, G4-doc3, G4-doc4. Faltan G5-G19.

---

## 3. PASADA 2 — Consistencia

| Contradicción | Dónde | Resolución necesaria |
|---------------|-------|----------------------|
| Dagu vs Temporal | Guías vs SALIDA-01 | Decisión formal del Director |
| Nomenclatura A vs G | A01≈G1 | Eliminar A (redundante) |
| Ubicación de archivos | G1 genérico vs SALIDA-01 `agentes/control-layer/` | Seguir SALIDA-01 |
| Sandbox/Memoria | G2 = Protocol | Correcto (implementación llega después) |

**Única contradicción real:** Dagu vs Temporal.

---

## 4. PASADA 3 — Gaps bloqueantes

| ID | Gap | Impacto |
|----|-----|---------|
| GAP-31 | G4 incompleto (faltan doc2-4) | **BLOQUEANTE** |
| GAP-32 | SALIDA-01 es solo diseño | **BLOQUEANTE** |
| GAP-33 | Guías de despliegue desactualizadas | Confusión |
| GAP-34 | G2 solo Protocols (sin implementaciones) | No bloquea ahora |
| GAP-35 | G3 no integrado con G1 ni G4 | Sistema no arranca |
| GAP-36 | No hay main.py que una G1+G2+G3+G4 | No se puede ejecutar |
| GAP-37 | Backend de estado (SQLite vs Postgres) | Persistencia |

---

## 5. PASADA 4 — Decisiones pendientes del Director

| ID | Decisión | Opciones | Default actual |
|----|----------|----------|----------------|
| D-01 | Motor de workflow | Dagu vs Temporal | SALIDA-01 dice Temporal |
| D-02 | Backend de estado | SQLite vs Postgres | InMemory (solo tests) |
| D-03 | Ubicación final | `agentes/control-layer/` | Consistente |
| D-04 | Autonomía levels 0-3 | Propuesta C18 | Pendiente |
| D-05 | 85 contratos | ¿Se implementan aquí? | No aparece en estos docs |
| D-06 | Prioridad de fuentes | GitHub → HF → docs | Claro |

---

## 6. PASADA 5 — Qué se puede construir hoy

```yaml
se_puede_construir:
  - G1 (Núcleo): 100%
  - G2 (Research): 70% (contratos)
  - G3 (DAG/Sheriff): 90% (falta integración)
  - Despliegue G1-G3: 100% según guía hasta T-004

no_se_puede_construir:
  - G4 (Capa de Control)
  - Integración G1+G2+G3+G4
  - Sistema completo (faltan G5-G19)
  - Conexión OpenClaw/Hermes (no especificada aquí)

bloqueos_principales:
  - G4 incompleto
  - Falta de integración
  - Guías desactualizadas (Dagu vs Temporal)
```

---

## 7. Resumen ejecutivo

```yaml
porcentaje_especificado: "40% (G1-G3 completos, G4 al 25%)"
porcentaje_implementable_hoy: "20% (solo G1-G3)"
siguiente_paso: "Obtener G4-doc2..4 + decidir D-01/D-02"
```

**Conclusión:** Base sólida (G1-G3). Falta Capa de Control (G4) + integración para tener sistema ejecutable.

---

## 8. Trazabilidad

- Origen: input block Director (2026-08-09) — “SEGUNDA PARTE – AUDITORÍA 5 PASADAS”
- Incorporado al perfil del PIPELINE

**Estado:** listo para auditoría.
