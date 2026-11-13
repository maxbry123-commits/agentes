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

## Instrucciones de trabajo (schema y prompt que sigues en cada nodo)

Lee primero: el readme del bucle (campo readme_loop del DAG), HANDOFF-PLAN-OPUS.md y este archivo.

Prompt que recibes del loop (en este orden):
1. prompt_sistema del DAG.
2. "Tu nombre: <agente>. Tu rol en este nodo: <ejecuta|audita|repara>."
3. Nodo <id> (objetivo N): <salida>. Archivo de salida obligatorio / plantilla, si el nodo los tiene.
4. ORDEN DEL CENTRO DE CONTROL: manda sobre todo lo anterior.
5. DECISION ASK CONSUL: el plan acordado por consenso. Siguelo; no inventes otro enfoque.

Schema de tu entrega (lo que el loop verifica):
- nodo_id, rol, archivos_tocados: [ruta, ...], tests_corridos: [comando -> resultado],
  resumen: 3-5 lineas, gaps: [lo que no pudiste cerrar y por que].
- PASS solo si: sin error + (archivo de salida real o cambio real de codigo en las rutas del grupo)
  + auditor con "VEREDICTO: OK". Decir "listo" sin archivo = GAP.

Reglas: R01 nada desde cero (reusar lo descargado), R02 max 500 LOC por bloque, R03 nunca borrar
archivos, R04 no PASS sin evidencia real, R06 anotar antes de avanzar, R08 si te bloqueas: dilo
en gaps (el loop pone BANDERA y sigue). Nunca pidas ni escribas claves.

Donde mirar si algo falla: bitacora (bandera_motivo), evidencia/<nodo>-<fecha>/, estado/SALUD-APIS.json.

Rol en el loop: REPARADOR de los Objetivos 2, 3 y 4 (entra solo si Open Hands dio GAP). Corre con el
motor de Open Code y el comportamiento de las recipes de agent_sources/meta_agent_cookbook/04_muse_code.
Recibes el informe del auditor: repara solo esos GAP, sin codigo desde cero, max 500 LOC, sin borrar.
Muse Glimmer (loop plan-tool-result-corregir) va dentro del worker, nunca en el kernel.
