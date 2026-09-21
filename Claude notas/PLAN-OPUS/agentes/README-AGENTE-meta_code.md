# MEMORIA AGENTE - META CODE (Muse Code + Muse Glimmer)

Rol: en los Objetivos 2, 3 y 4, despues de Open Hands: revisa de nuevo, refactoriza y repara.
Grupos: usa la clave del objetivo en curso (2 movistar-briseida, 3 wow-maxbry, 4 wow-brisa).

## Son dos piezas

1. Muse Code - programa: lee repo, mantiene sesion, modifica codigo.
   Fuente: agent_sources/meta_muse_code_sdk (SDK) + agent_sources/meta_agent_cookbook/04_muse_code (10 recipes).
2. Muse Glimmer - decide: plan, tool, result, self-correct, next.
   Fuente: agent_sources/muse_glimmer/code/agentic-fundamentals (agent_loop.py, response_parser.py, run_agent.py).
   Primer paso: leer esos 3 archivos y anotar que hace cada uno (aun no leidos).
   Su loop va DENTRO del worker, nunca en el kernel (prohibido dos cerebros).

## Acceptance

1. Cada refactor sale de codigo ya existente, citando la ruta de origen.
2. Cada reparacion trae test que falla antes y pasa despues.
3. Max 500 LOC por bloque. Nada se borra.

## Antes de cada salida

Ask Consul: goal de entrada + goal de salida, consenso, entrada PLANEADO en la bitacora.

## Donde reporta

Claude notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json (solo anadir).

## Memoria (anadir abajo, nunca borrar)

- 2026-09-21: memoria creada. Sin ejecuciones todavia.
