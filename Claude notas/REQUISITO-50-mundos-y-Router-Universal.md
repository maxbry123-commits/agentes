REQUISITO ARQUITECTONICO CRITICO - 2026-09-18 (para el cierre final, Salida 8+)

## CADA WORDFLOW = UN MUNDO INDEPENDIENTE (mas de 50 workers)
Confirmado por el Director: habra mas de 50 wordflows/agentes corriendo.
CADA UNO debe tener su propio conjunto minimo, sin compartir archivos
entre si (mismo codigo base, pero cada instancia con su propio set):
- Readme memoria.md (memoria propia del worker)
- Handoff (propio)
- Crazy Wall bitacora stated JSON (propio, o su seccion propia en el
  Crazy Wall central - a definir en Salida 8)
- System prompt (propio, generado desde el mismo template)
- Cualquier otra cosa que ese worker necesite

Cada uno debe funcionar como un "sistema operativo independiente" -
mismo patron ya establecido en documentos VERBATIM (worker_template,
mismo code_sha256, distinto worker_id/task/workspace).

## FUENTE DE API KEYS - CORRECCION IMPORTANTE
Cerebras (las 6 keys que ya estan cableadas en consultor_experto.py y
router_modelos.py) es SOLO PARA HACER PRUEBAS, no la fuente de produccion.
En produccion, TODOS los wordflows (los 50+) se conectan al Router
Inteligente Universal como proveedor de API keys - el Router decide que
modelo/proveedor usar, no cada worker con su propia key hardcodeada.

IMPLICACION PARA EL CODIGO YA ESCRITO: router_modelos.py y
consultor_experto.py deben quedar con un adapter que en el futuro apunte
al Router Universal en vez de directo a Cerebras - marcado como TAREA
PENDIENTE para cuando el Router Universal este activo (Prioridad 2 de la
lista actual, despues de cerrar Wordflow Loop + Comand Center).

## NO SE DECLARA NADA CERRADO SIN QUE ESTO ESTE RESUELTO
Este requisito se verifica en Salida 8 (cierre formal) antes de declarar
VERIFIED_CLOSED - no basta con que Seals Team funcione solo, tiene que
quedar listo para operar como 1 de 50+ mundos independientes conectados
al Router Universal.
