SCHEMA FRONTEND BROWSER-VERIFIED v2 corregido 2026-09-17
Correccion: version anterior parafraseaba el texto del Director en vez de
copiarlo verbatim. Corregido aqui, cita exacta primero, luego el microflujo.

TEXTO VERBATIM DEL DIRECTOR (input block, sin reinterpretar):

BROWSER-VERIFIED WEB DESIGN - DISEÑADOR FRONTEND

Capacidad
Es el patron directamente orientado a construir una web y verificar el
trabajo utilizando un navegador real.

Aporta
Une dos mundos:
PROGRAMACION + PERCEPCION VISUAL

Regla
SOURCE CODE PASS no significa UI PASS.
Debe existir: CODE PASS + BROWSER PASS + VISUAL PASS.

FIN DEL TEXTO VERBATIM.

MICROFLUJO (anadido por Claude, aplicando el texto de arriba a Wordflow):
DETECTA_TAREA_FRONTEND -> ACTIVA_MINI_WORKFLOW_FRONTEND (separado dentro
de Wordflow, mismo Crazy Wall, distinto DAG interno) -> EDITA_COMPONENTE
-> BUILD -> CODE_PASS -> START_APP -> OPEN_REAL_BROWSER -> BROWSER_PASS
-> SCREENSHOT + INTERACT -> VISUAL_PASS -> si alguno falla, GAP
especifico (CODE/BROWSER/VISUAL), nunca un PASS generico.

REGLAS DE REUSO (para no improvisar, anadidas por el Director):
- Antes de escribir componente nuevo: usar motores de descarga y
  extraccion para traer componentes/ventanas/botones/pestanas de repos
  open source reales.
- REUSE_EXISTING > PATCH > ADAPT > GENERATE, igual que en backend.
- Bloques de codigo de frontend segmentados por ventana/componente, cada
  uno en su propio archivo.
