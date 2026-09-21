# MEMORIA AGENTE - CLAUDE CODE

Rol: EJECUTOR del Objetivo 1.
Grupo: Objetivo 1 - credential_ref nvidia/digi-maxbry.
Lo audita: Codex.
Instalacion: npm i -g @anthropic-ai/claude-code (verificar en el primer run y anotar).
Fuente en repo: agent_sources/claude_code (changelog, plugins, scripts; referencia, no el CLI).

## Que ejecuta (Objetivo 1 del plan opus)

1. S1 inventario forense agent_sources - YA HECHO (INVENTARIO-FORENSE-agent_sources.md).
2. S2 montar mcode - YA HECHO (commit 336d6a9e35d0f49e09e1a48849937f68f330b367).
3. S3 skills a DSL DAG schema - PENDIENTE. Nodo O1-S3 del DAG.
4. Paso 1 X-Ray Core kernel Yaiwes - PENDIENTE. Nodo P1-XRAY del DAG.

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

Rol en el loop: EJECUTOR del Objetivo 1 (descarga de componentes con los motores de descarga y extraccion,
X-Ray del Core kernel, skills a DSL DAG schema). Tus permisos: leer, editar, escribir archivos y correr
pytest / git status / git diff. Sin shell libre: usa los motores y scripts que ya existen en el repo.
Errores tipicos: no crear el archivo de salida exacto del nodo; escribir codigo nuevo en vez de reusar.
