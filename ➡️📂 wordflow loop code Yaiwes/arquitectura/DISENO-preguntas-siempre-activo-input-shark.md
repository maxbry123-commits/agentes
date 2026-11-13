DISENO - SISTEMA DE PREGUNTAS SIEMPRE-ACTIVO PARA YAIWES + INPUT SHARK +
UI YAIWES - 2026-09-17

## CONFIRMACION IMPORTANTE
El mecanismo de preguntas interactivas antes de ejecutar SIGUE EXISTIENDO
en el producto de Anthropic ahora mismo - no fue removido. Valida que el
concepto es real y replicable.

## LOS 3 LUGARES DONDE VIVE (aclarado por el Director, 2026-09-17)
Mismo diseno, 3 implementaciones independientes:
1. UI YAIWES interface (repo nct-hub, hipotesis) - de cara al usuario
2. UI YAIWES backend - logica que procesa preguntas/respuestas
3. Yaiwes, por medio del Input Shark (repo agentes / osquestador-auditor)
No se comparte codigo directo entre los 3, se comparte el DISENO.

## DECISION: SIEMPRE ACTIVO, no condicional a ambiguedad detectada
Pieza SUPERIOR en prioridad, vive DENTRO del Input Shark, se activa en
el 100% de las tareas.

## MICROFLUJO (formato Glimmer)

1. Capacidad: antes de razonar/ejecutar, siempre una fase de preguntas
   de enfoque que clarifica el objetivo real.
2. Patron: TAREA_RECIBIDA -> INPUT_SHARK -> GENERAR_PREGUNTAS (siempre)
   -> PRESENTAR -> RECIBIR_RESPUESTAS -> CONTEXTO_ENRIQUECIDO -> RAZONAMIENTO
3. LOOP: siempre genera 1-3 preguntas (nunca 0, nunca mas de 3), opciones
   sobre texto libre cuando se puede, si no responde usa default declarado
   explicitamente ("asumo X, dime si no").
4. Aporta: evita el patron ya visto de Sol/Grok ejecutando sobre
   interpretacion equivocada, rehaciendo trabajo despues.
5. Usa: mecanismo de preguntas interactivas real, Input Shark con Fables,
   mission_context (DISENO-MCP-contexto-compartido.md).
6. Reglas: siempre se activa, max 3 preguntas min 1, preferir opciones,
   default declarado nunca asumido en silencio, los 3 lugares implementan
   el mismo microflujo de forma independiente.
7. Fallos: pregunta ignorada -> sigue con default, no se bloquea esperando.
8. Test: tarea ambigua real genera preguntas especificas antes de escribir
   codigo.

## PENDIENTE DE CODIGO
Componente de CODE real, Claude lo construye cuando el Director apruebe,
no se delega a Sol. Se construye 3 veces (uno por lugar), no 1 compartida.
