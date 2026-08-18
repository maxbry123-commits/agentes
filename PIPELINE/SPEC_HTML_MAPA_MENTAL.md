# Spec HTML mapa mental cascada — S05 / T05
**Fecha:** 2026-08-17
**Estilo:** NCT/APEX cascada

## Requisitos del HTML final (T41)
1. Cascada vertical: Visión → Kernel → Instance → Extensions → Path → Recursos → UI
2. Cada bloque lleva ID canónico (ROOT_MAP_IDS)
3. Cada bloque muestra: `→ Para qué` / `→ Sin esto`
4. Estados de color: IMPLEMENTED (verde) | PARTIAL (ámbar) | MISSING (rojo) | PENDING (gris)
5. Enlaces directos a path GitHub cuando exista archivo
6. Sin dependencias externas pesadas (HTML + CSS mínimo inline o un solo archivo)
7. Responsive básico

## Estructura de secciones
```
1. Visión (OBJETIVO V1)
2. Kernel (WF.00)
3. WordflowInstance (INST.*)
4. Extensions wordflow (WF.01)
5. Extensions wordflow_kernel (WF.02)
6. Control-layer (WF.03)
7. Code path / loops
8. Recursos HF / cuentas
9. UI / Gateway
10. PIPELINE docs
```

## Entrega T41
Un solo archivo `docs/mapa_mental_v1.html` (o PIPELINE/) que cumpla esta spec.
