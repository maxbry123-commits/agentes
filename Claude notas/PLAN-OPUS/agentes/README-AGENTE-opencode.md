# MEMORIA AGENTE - OPEN CODE

Rol: EJECUTOR de los Objetivos 2, 3 y 4.
Grupos: Objetivo 2 nvidia/movistar-briseida, Objetivo 3 nvidia/wow-maxbry, Objetivo 4 nvidia/wow-brisa (usa la clave del grupo del objetivo en curso).
Lo audita: Open Hands. Luego repara: Meta Code.
Instalacion: npm i -g opencode-ai (verificar en el primer run y anotar).
Fuente en repo: agent_sources/opencode.

## Que ejecuta

Objetivo 2 - cerrar Wordflow loop code Yaiwes: S4 doble raiz, S5 gaps del kernel (checkpoint durable primero), S6 frontend visualizable.
Objetivo 3 - terminar Seals Team YAIWES: S7 gaps restantes, S8 grupos 1 y 2 + cierre verificado.
Objetivo 4 - Orquestador Comand Center: S9 adapters, S10 motor durable + 50 mundos.
Detalle de cada salida: Claude notas/PLAN-MAESTRO-4-OBJETIVOS.md.
Si un objetivo esta bloqueado: BANDERA, anotar, seguir con el siguiente, volver en bucle al final.

## Antes de cada salida

Ask Consul: goal de entrada + goal de salida, consenso, entrada PLANEADO en la bitacora.

## Donde reporta

Claude notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json (solo anadir).

## Memoria (anadir abajo, nunca borrar)

- 2026-09-21: memoria creada. Sin ejecuciones todavia. El swap anterior a aider queda anulado por orden del Director.

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

Rol en el loop: EJECUTOR de los Objetivos 2, 3 y 4 (terminar Wordflow loop code Yaiwes, crear agente
Seals Team YAIWES en la misma raiz, crear Orquestador Comand Center). Permisos: editar archivos y correr
pytest / git status / git diff; sin red ni shell libre. Trabaja dentro de las rutas del grupo.
Error tipico: cambios fuera de las rutas del grupo (no cuentan) o sin test.
