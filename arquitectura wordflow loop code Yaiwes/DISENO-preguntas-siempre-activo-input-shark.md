DISENO - SISTEMA DE PREGUNTAS SIEMPRE-ACTIVO PARA YAIWES + INPUT SHARK +
UI YAIWES - 2026-09-17

## CONFIRMACION IMPORTANTE
El Director recordaba un mecanismo de preguntas antes de ejecutar (una
ventana con preguntas en el chat). CONFIRMADO: este mecanismo SIGUE
EXISTIENDO en el producto de Anthropic ahora mismo (presentacion de
preguntas interactivas con opciones tocables antes de continuar) - no
fue removido. Esto valida que el concepto es real y replicable.

## DECISION DE DISENO: SIEMPRE ACTIVO, no condicional a ambiguedad detectada

Para Yaiwes y UI Yaiwes: esta pieza es SUPERIOR en prioridad, vive DENTRO
del Input Shark (disenado con Fables), y se activa en el 100% de las
tareas, no solo cuando el sistema detecta ambiguedad.

## MICROFLUJO (formato Glimmer)

### 1. Capacidad
Antes de que cualquier tarea llegue al razonamiento o ejecucion, se
presenta siempre una fase de preguntas/enfoque que clarifica el objetivo
real, evitando que el sistema ejecute sobre una suposicion equivocada.

### 2. Patron - microflujo transversal horizontal
TAREA_RECIBIDA -> INPUT_SHARK -> GENERAR_PREGUNTAS_DE_ENFOQUE (siempre,
no condicional) -> PRESENTAR_AL_DIRECTOR -> RECIBIR_RESPUESTAS ->
CONSTRUIR_CONTEXTO_ENRIQUECIDO -> RECIEN_AHORA_PASA_AL_RAZONAMIENTO

### 3. LOOP
TAREA_NUEVA -> INPUT_SHARK.recibir()
-> SIEMPRE genera 1-3 preguntas de enfoque (nunca 0, nunca mas de 3)
-> presenta como opciones cuando es posible (no texto libre siempre)
-> espera respuesta del Director
-> si el Director no responde una pregunta especifica: usa el default
   mas razonable y lo declara explicitamente ("asumo X, dime si no")
-> arma el contexto final -> pasa a decision_on_demand / Reasoning Kernel

### 4. Aporta
Evita el patron que ya vimos fallar varias veces en esta conversacion
(Sol/Grok ejecutando sobre una interpretacion equivocada, generando
trabajo que hay que rehacer) - la pregunta previa es mas barata que el
trabajo mal hecho.

### 5. Usa
El mecanismo de preguntas interactivas ya real y disponible (confirmado
arriba), el Input Shark disenado con Fables, y el contexto de la mision
actual (mission_context, ver DISENO-MCP-contexto-compartido.md).

### 6. Reglas
- SIEMPRE se activa, nunca se salta por "la tarea parece clara".
- Maximo 3 preguntas, minimo 1 - nunca cero.
- Preferir opciones sobre texto libre cuando la pregunta lo permite.
- Si el Director no responde: usar default razonable, declararlo
  explicitamente, nunca asumir en silencio.

### 7. Fallos
PREGUNTA_IGNORADA -> el sistema sigue con el default declarado, no se
bloquea esperando indefinidamente (evita el "no avanza" que ya vimos con
Sol quedandose pensando).

### 8. Test
Una tarea ambigua real (ej. "mejora el frontend") debe generar preguntas
especificas (que pantalla, que criterio de mejora, que prioridad) antes
de que cualquier codigo se escriba - nunca ejecutar directo sobre una
instruccion de una sola linea sin enfocar primero.

## PENDIENTE DE CODIGO
Este es un componente de CODE real (parte del Input Shark), no mecanico -
Claude lo construye cuando el Director apruebe el diseno de arriba, no se
delega a Sol.
