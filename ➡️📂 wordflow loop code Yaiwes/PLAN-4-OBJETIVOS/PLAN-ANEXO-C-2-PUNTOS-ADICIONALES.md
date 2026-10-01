# PLAN ANEXO C - 2 puntos adicionales del Director (2026-09-20)

Este anexo SE ANADE al PLAN-MAESTRO-4-OBJETIVOS.md. No modifica nada del plan:
el plan queda igual, estos 2 puntos se ejecutan ademas, dentro de cada salida.

Instruccion textual del Director (1 a 1, sin reinterpretar):

PUNTO 1: "anade a la tarea del plan una aditoria forense x Ray de toda la raiz de
core kernel Yaiwes de cada componente y crea un archivo con la informacion"

PUNTO 2: "anade revisar el wordflow al final del cierre del objetivo y hacer la
auditoria basada a la plantilla de el metodo de meta que describio sol gpt y crear
la raiz todo en un archivo lo mismo al terminar con el agente seals team YAIWES y
con el osquestador comandante"

## PUNTO 1 - Auditoria forense X-Ray de la raiz de Core kernel Yaiwes

Que: recorrer la raiz "Core kernel Yaiwes" COMPONENTE POR COMPONENTE y dejar una
radiografia real de cada uno.

Plantilla: la que ya existe, no se inventa otra.
1. En este repo: Claude notas/VERBATIM-01-node-executor-xray-v2.md
2. En el repo router: Claude notas/DSL-FABLES-yaiwes-node-executor-xray-v2.md

Archivo de salida: Claude notas/XRAY-CORE-KERNEL-YAIWES.md

Una entrada por componente, y cada entrada lleva:
1. nombre del componente
2. ruta real dentro de la raiz
3. sha del arbol o del blob (evidencia, no memoria)
4. que hace de verdad (leido, no supuesto)
5. de que depende y quien lo usa
6. veredicto: REAL o PARCIAL o VACIO o DUPLICADO
7. GAP si lo hay

Acceptance: ninguna entrada puede decir "supuesto" ni "deberia". Si no se pudo
verificar, va como GAP explicito con bandera, y se sigue con el siguiente
componente (nunca se para el ciclo).

Cuando: se ejecuta como tarea dentro del Objetivo 1, y se vuelve a pasar al cerrar
cada objetivo para detectar drift.

## PUNTO 2 - Auditoria del Wordflow al cierre de cada objetivo

Que: al terminar CADA objetivo, antes de declararlo cerrado, revisar el Wordflow y
hacer la auditoria con la plantilla del metodo de Meta (la que describio Sol GPT).

Archivos de salida, uno por cierre, nunca se sobreescriben entre si:
1. Claude notas/AUDITORIA-WORDFLOW-OBJETIVO-1.md
2. Claude notas/AUDITORIA-WORDFLOW-OBJETIVO-2.md
3. Claude notas/AUDITORIA-WORDFLOW-OBJETIVO-3.md
4. Claude notas/AUDITORIA-WORDFLOW-OBJETIVO-4.md

La misma auditoria, con la misma plantilla, se repite en:
1. Claude notas/AUDITORIA-CIERRE-SEALS-TEAM-YAIWES.md, al terminar Seals Team
2. Claude notas/AUDITORIA-CIERRE-ORQUESTADOR-COMANDANTE.md, al terminar el orquestador

Cada auditoria lleva:
1. objetivo auditado y que se prometio
2. que quedo realmente en el codigo (ruta + sha)
3. test que corrio y su resultado real
4. evidencia (sha256, commit, run id)
5. GAPs abiertos, con bandera
6. veredicto final: CERRADO o GAP. Nunca cierre fingido.

Acceptance: sin evidencia real no hay PASS. Un modelo diciendo "CORRECTO" no es
evidencia (regla R04 del contrato).

Resumen: este anexo agrega 2 tareas fijas y repetibles (X-Ray por componente, y
auditoria de cierre por objetivo + Seals + orquestador), cada una con su archivo de
salida ya nombrado, usando plantillas que ya existen en el repo.
