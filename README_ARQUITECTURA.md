# README Arquitectura — Kernel multi-instancia + Extensions

**Tarea:** S02 / T02  
**Fecha:** 2026-08-17

## Diagrama texto

```
KERNEL (estable, pequeño)
  │
  ├── WordflowInstance A  (goals, state, loops, evidence)
  ├── WordflowInstance B
  └── WordflowInstance N

EXTENSIONS / CAPABILITIES (ficha.v2)
  ├── engines / adapters / connectors
  ├── skills / datasets (HF bajo demanda)
  └── plugins (UI, router slot, memory slot)
```

- Crear otra instancia **no** exige reescribir el kernel.
- Extensión = paquete cargable. Instancia = ejecución/proyecto aislado.
- COPY-FIRST: nunca regenerar código que ya existe y es compatible.

## Enlaces
- Método: PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md
- Plan 49: PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md
- Lista completa 1:1: PIPELINE/55_LISTA_COMPLETA_V1.md
