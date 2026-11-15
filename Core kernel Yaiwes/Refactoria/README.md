# Refactoria

**Raíz autorizada:** `Refactoria/`  
https://github.com/maxbry123-commits/agentes/tree/main/Refactoria

## Qué es

Sitio de la **versión vieja** (o del archivo que se quiere modificar).  
No se edita el original in-place. Se copia aquí, se escribe el nuevo aparte, verificación cruzada ×3, luego se integra al path canónico.

## Patrón por plan (N variable)

```text
Refactoria/refactoria-plan-x-N/
├── source/     copia exacta del original
└── new/        versión nueva
```

Ejemplo: Plan X-2 → `Refactoria/refactoria-plan-x-2/` + `Desplegar/Desplegar 2/`.

Hoy existen `Refactoria/G1`…`G7` de la misión YAIWES (gaps). No se borran en S1.

## Regla

- source/ no se edita.
- Integrar `new/` solo con 3 verificaciones PASS + evidencia.
- Borrar viejo solo con autorización Director.
- Este README no se reescribe; parche = `Refactoria/Readme1.md`.
