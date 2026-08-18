# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

**Fecha:** 2026-08-17 (actualizado estándares avanzados)  
**Estado:** LEY DE TRABAJO  
**Plan activo:** PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md  
**Estándar code:** PIPELINE/ADVANCED_ENGINEERING_STANDARD_V2.md + extensions/wordflow/standards/

## Reglas de archivo y calidad (LEY)

| Regla | Valor |
|-------|-------|
| LOC por **archivo** | preferido 300–800; >800 revisión; >1000 refactor |
| LOC del **proyecto** | **sin límite** — escala por módulos |
| Calidad del code | **nivel profesional avanzado — NUNCA MVP** |
| Gaps de auditoría | **100% resueltos antes de avanzar** |
| Almacenamiento | GitHub = única verdad; prohibido sandbox storage |

≤300–800 LOC limita el **archivo**, no el alcance ni la profundidad del sistema.

## Formato de salida OBLIGATORIO

```
# CONTROL DE TRABAJO
1. **TOTAL TAREAS V1:** 49
2. **TERMINADAS:** N
3. **PENDIENTES:** M
4. **SIGUIENTE:** **Sy / Ty**
5. **PLAN:** .../52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md
6. **MÉTODO:** .../00_METODO_TRABAJO_Y_ARQUITECTURA.md
7. **CONFIRMACIÓN:** NO sandbox storage · GitHub = verdad
```

## LEY AUDIT-5
Cada 5 tareas (o antes si grande): forense 100% → gaps → corregir 100% → mejorar 10x → actualizar arch/PIPELINE → **no avanzar hasta gaps 100% resueltos**.

## Estándares de code avanzado (resumen)
Ver: `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V2.md`  
Ejecutable: `extensions/wordflow/standards/` (schema + sheriff + quality DAG)

Principios Cursor-native:
- Context engineering (repo map, rules, contracts)
- Generate → Inspect → Plan → Edit → Test → Verify → Evidence → Merge
- AI output nunca es prueba de corrección
- Deterministic-first; LLM solo vía gateway
- Architecture fitness tests machine-enforced
