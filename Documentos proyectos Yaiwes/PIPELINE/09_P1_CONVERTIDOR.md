# PIPELINE 09 — P1-CONVERTIDOR v5.0
## Convertidor de Documentos → Fichas Ejecutables

**Fecha:** 2026-08-09  
**Estado:** BASE CRÍTICA  
**Stop rule:** Sin APROBADO Director = STOP  
**Siguiente pipeline:** P2-CONSTRUCTOR

---

## 1. Propósito

Convertir documentos / texto / diagramas / código en **fichas** con contrato mínimo:

```
id · contenido · fuentes · confianza · dependencias · trace
```

Cobertura exigida: 1.0 (sin faltantes).

---

## 2. Fases del runtime

```
INDEXING (una sola vez)
  → EXTRACTION (100% del índice)
  → CLASSIFICATION
  → FUSION
  → AUDIT_1 (consistencia)
  → AUDIT_2 (integridad + cobertura)
  → FACTS (genera fichas → PENDING_APPROVAL)
  → WAIT_APPROVAL (Director)
  → DONE | RE_INDEXING
```

---

## 3. Reglas de fusión

- DUPLICADO → merge (nunca borrar)
- CONTRADICCIÓN → CONFLICTIVO + bloqueo + escalación Director
- VARIANTE → coexistencia

Resolución: MERGE | REPLACE | SPLIT.

---

## 4. Políticas críticas

- Sin evidencia textual = no EXPLICITO
- confianza < 0.6 → PENDING automático
- dependencia hard no APPROVED → item bloqueado
- ejecución idempotente (mismo input = mismo output)
- Sin APROBADO Director = STOP

---

## 5. Outputs

- RAW_MAP
- CLASSIFICATION_LAYER
- ONTOLOGY_LAYER
- AUDIT_REPORT
- EXECUTION_READY

---

## 6. Trazabilidad

- Origen: input block Director — P1-CONVERTIDOR v5.0 (JSON + texto estructurado)
- Base crítica del PIPELINE.

**Estado:** listo para auditoría.
