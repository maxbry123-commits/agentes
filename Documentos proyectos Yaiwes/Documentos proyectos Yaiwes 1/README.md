# Desplegar — raíz inbox

**Raíz autorizada:** `Desplegar/`  
https://github.com/maxbry123-commits/agentes/tree/main/Desplegar

## Qué es

Única raíz donde el Director **sube** documentos y code para un plan.  
No es `despliegue/` (mecanismo viejo de contratos/CI). Ese path es candidato S2.

## Patrón (N variable — no hardcodear Desplegar 1)

```text
Desplegar/
├── README.md          ← este archivo; no reescribir
├── Desplegar 1/       ← ejemplo: lote del plan 1
├── Desplegar 2/       ← ejemplo: lote del plan 2
└── Desplegar N/       ← lote del Plan X-N
```

`Desplegar 1` solo existe cuando el Director sube el lote 1. S1 no crea `Desplegar 1/` vacío.

## Cableado

```text
Plan X-N  →  Desplegar/Desplegar N/  →  Refactoria/refactoria-plan-x-N/
```

- Docs/code NUEVOS del lote → `Desplegar/Desplegar N/`
- Archivo VIEJO que se va a modificar → `Refactoria/refactoria-plan-x-N/` (copia, no editar origen)

## Prohibido

- Usar `Desplegar 1` como nombre fijo en plantillas.
- Mezclar lotes de planes distintos en la misma carpeta N.
- Reescribir este README (parche = `Desplegar/Readme1.md`).
