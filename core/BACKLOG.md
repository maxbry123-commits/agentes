---
# BACKLOG — Propuestas registradas en RT-90 (sin ejecutar)

**Regla E08**: mejoras, refactorizaciones, nuevas librerías, herramientas o
arquitecturas se REGISTRAN acá al cierre del proyecto, NO se ejecutan.

---

## Estado: VACÍO (sin propuestas todavía)

Este archivo se llena en RT-90 con ideas detectadas durante la ejecución que
NO se ejecutaron (por anti-scope-creep E08 / E13).

## Formato de entrada

```yaml
- id: "BL-001"
  detectada_en: "<nodo_id o fase>"
  categoria: "refactor | nueva_libreria | nueva_herramienta | arquitectura | observabilidad"
  descripcion: "<1-3 frases>"
  beneficio_estimado: "<qué mejora>"
  costo_estimado: "<tiempo/tokens>"
  prioridad_sugerida: "baja | media | alta"
  riesgo: "bajo | medio | alto"
  fecha_deteccion: "<ISO8601>"
  estado: "registrada | aprobada | rechazada | ejecutada"
```

## Decisión del Director (Max)

Cuando el Director (Max) lo requiera, este archivo se revisa y cada entrada
pasa por el flujo E07 (aprobación explícita antes de ejecutar).

---

**Última actualización:** RT-90 (cierre de proyecto)
