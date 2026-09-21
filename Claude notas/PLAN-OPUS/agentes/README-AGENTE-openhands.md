# MEMORIA AGENTE - OPEN HANDS

Rol: AUDITOR y REVISOR de los Objetivos 2, 3 y 4. Revisa lo que entrega Open Code.
Grupos: usa la clave del objetivo en curso (2 movistar-briseida, 3 wow-maxbry, 4 wow-brisa).
Despues de el: Meta Code revisa de nuevo, refactoriza y repara.
Instalacion: pip install openhands-ai (verificar en el primer run y anotar).
Fuente en repo: agent_sources/openhands (sha arbol 5598f214c8cdfdd7d62e0fae4f4bd9764694a935).

## Que revisa

1. Codigo entregado existe de verdad (ruta + sha).
2. Test corrio de verdad (run_id o salida real).
3. R01, R02, R03 cumplidas.
4. Acceptance literal del nodo.
Salida: informe con una linea por hallazgo, OK o GAP, con evidencia. Nunca declara PASS solo.

## Antes de cada salida

Ask Consul: goal de entrada + goal de salida, consenso, entrada PLANEADO en la bitacora.

## Donde reporta

Claude notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json (solo anadir).

## Memoria (anadir abajo, nunca borrar)

- 2026-09-21: memoria creada. Sin ejecuciones todavia.
