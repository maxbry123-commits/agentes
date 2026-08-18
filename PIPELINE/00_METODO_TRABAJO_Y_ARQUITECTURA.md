# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA DE RESPONSABILIDADES

**Fecha:** 2026-08-17 (Paso 2)  
**Estado:** LEY DE TRABAJO  
**Plan activo:** PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md

## Formato de salida OBLIGATORIO (cada tarea)

```
# CONTROL DE TRABAJO

1. **TOTAL TAREAS V1:** 49
2. **TERMINADAS:** N (Tx/Sx)
3. **PENDIENTES:** M
4. **SIGUIENTE:** **Sy / Ty**
5. **PLAN:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md
6. **MÉTODO:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md
7. **CONFIRMACIÓN:** NO sandbox storage · GitHub = verdad
```

## Lista de tareas — requisitos
- Debe incluir **trazabilidad de documentos** (doc origen, ancla, path) por cada tarea.
- El formato de *salida* (CONTROL DE TRABAJO) **no es** la lista completa.
- La lista completa se presenta con columnas: Salida | ID | Tarea | Trazabilidad docs | Objetivo | Estado
- Agrupada por BLOQUE A–F.

## LEY AUDIT-5
Cada 5 tareas terminadas (o antes si grande/multipart):
1. Auditar método + PIPELINE
2. Forense 100% de las 5
3. Gaps → corregir → 10x
4. Actualizar arquitectura + bitácora
5. NO avanzar hasta 100% gaps resueltos
6. Insertar la auditoría como tarea adicional

## Reglas base
- Una tarea = una salida = commit GitHub
- ≤300 LOC por archivo
- COPY-FIRST → WIRE → test Fake → PATCH mínimo
- GitHub = única verdad (prohibido sandbox storage)
