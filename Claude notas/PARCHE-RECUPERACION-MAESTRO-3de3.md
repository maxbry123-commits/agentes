PARCHE DE RECUPERACION MAESTRO - SALIDA 3 DE 3 - 2026-09-17
Continua de PARCHE-RECUPERACION-MAESTRO-2de3.md

## REGLAS DE TRABAJO CONSOLIDADAS (para quien retome esta sesion)

1. Un paso/tarea por salida. No avanzar sin cerrar o dejar GAP documentado.
2. Claude analiza y decide arquitectura. Sol SOLO ejecuta ordenes
   imperativas literales con URL exacta de origen/destino - Sol NUNCA
   compara, analiza, ni decide (alucina si se le pide eso).
3. Prompts a Sol: formato INPUT_BLOCK VERBATIM + maximo 3 pasos +
   evidencia obligatoria (path+sha256) + URL exacta de donde reportar.
4. Antes de escribir CUALQUIER schema o bloque de codigo: consultar
   biblioteca/GitHub primero (REUSE>PATCH>ADAPT>GENERATE), nunca escribir
   de memoria del LLM directo.
5. Nunca declarar PASS sin evidencia real (test + hash + resultado
   observable) - un oraculo externo decide, no el propio agente.
6. Nunca borrar archivos - editar quirurgicamente o crear version nueva
   y comparar antes de eliminar la vieja.
7. Cada componente/agente se presenta con el formato Glimmer: Capacidad,
   Patron microflujo horizontal en texto (sin imagenes salvo pedido
   explicito), LOOP, Aporta, Usa, Reglas, Fallos, Test.
8. Verificar 4 veces (no 1) que una regla nueva quede realmente cableada
   en todos los lugares donde aplica, no solo documentada una vez.
9. Ante ambiguedad real: preguntar con opciones concretas, nunca asumir
   en silencio y nunca frenar el avance esperando respuesta indefinida.
10. Toda esta memoria vive en Claude notas/ (unica raiz), nunca se resume,
    solo se anade.

## ESCALERA DE ESCALAMIENTO
Sol GPT -> Claude Haiku -> Claude Sonnet -> Claude Opus -> GPT/Astra
(historicamente sin resultados) -> Fables 5.1

## PROXIMO PASO EXACTO (donde quedamos)
Con las 3 salidas del parche de recuperacion completas, y los 20 archivos
de arquitectura + gaps documentados, el siguiente paso pendiente es:
TAREA 2 - Ask Council (12 puntos) + propuesta de mejoras para cerrar
Wordflow Loop y Seals Team, usando GOALS (12 entrada/salida) + 3
refutaciones + 4 simulaciones, tal como se definio antes de esta ronda
de correcciones y auditoria extendida.

## LO QUE EL DIRECTOR DEBE DECIDIR/APROBAR ANTES DE TAREA 2 (si aun no lo hizo)
- Aprobar ejecutar el prompt de comparacion de los 2 Crazy Wall (ya escrito)
- Aprobar ejecutar el prompt de descarga de 5 componentes (Omniroute,
  Orca, Omarchy, Anydoc, Skill Design Anthropic - ya escrito)
- Poner las 4 variables de entorno en GitHub Secrets para la primera
  prueba real de Seals Team
- Confirmar si el servidor MCP se codea ya o se espera a Tarea 2

FIN DEL PARCHE DE RECUPERACION MAESTRO (3 de 3). Con estas 3 salidas mas
Claude notas/memoria.md, cualquier sesion nueva puede retomar el 100% del
contexto sin depender de esta conversacion.
