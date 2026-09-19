${OLD}

## 16. CORRECCION IMPORTANTE - Run 3 limpieza historial (2026-09-19) - mi conclusion anterior era ERRONEA

Run 35431119175 (workflow con clon COMPLETO, fix del blob-not-found):
TODOS los pasos del job terminaron con conclusion:"success" real (no
solo continue-on-error), confirmado ademas leyendo el log real
completo en Claude notas/evidencia_runs/limpieza_historial_35431119175.txt:

1. CLON COMPLETO: CLONE_EXIT=0. PERO du -sh repo-mirror = 16G real, y
   git count-objects -vH: in-pack 1,127,762 objetos, size-pack 15.70
   GiB. ESTO CONTRADICE lo que anote en la seccion 13: el clon blobless
   anterior media 47MB porque un clon blobless deliberadamente NO trae
   el contenido de los blobs (solo arboles/commits) - no porque el
   resto fuera basura no alcanzable. Con el clon completo se confirma
   que el repo agentes SI tiene ~15-16GB de contenido real y alcanzable
   en su historia. RETRACTO la conclusion anterior de "es basura
   dangling" - fue una inferencia incorrecta a partir de un clon
   parcial. Pido disculpas por la confusion que esto pudo causar.
2. FILTRO: git filter-repo --force --path ... corrio de verdad sobre
   ~4365 commits (FILTER_EXIT=0, 45.72s parseo + 156.57s repack). PERO
   el tamano final quedo en 15.09 GiB - una reduccion minima (de 15.70
   a 15.09 GiB). Esto significa que la mayoria del peso NO esta en las
   carpetas que se estan quitando del historial, sino DENTRO de las
   carpetas que SI se conservan (Motores, Core kernel Yaiwes, Wordflow,
   etc.) - probablemente versiones historicas de archivos grandes
   (modelos, binarios, zips) commiteados y luego borrados/reemplazados
   muchas veces en esas mismas carpetas protegidas. GAP NUEVO: hay que
   identificar QUE archivos grandes especificos inflan esas carpetas
   protegidas antes de poder reducir el tamano real de verdad.
3. PUSH: git push limpio --mirror FALLO con un error DISTINTO al de
   antes: "remote: Invalid username or token. Password authentication
   is not supported for Git operations. fatal: Authentication failed".
   Causa: el secret MAXBRY_123_TOKENS no es un token valido para
   autenticacion git (formato incorrecto, expirado, o no es un PAT
   real de GitHub). ACCION PENDIENTE DEL DIRECTOR: regenerar/revisar
   MAXBRY_123_TOKENS en GitHub (Settings -> Developer settings ->
   Personal access tokens), con permiso repo completo sobre
   yaiwes-nucleo-limpio, y decirme cuando este listo para reintentar
   el push (Run 4).

ESTADO REAL FINAL: filter-repo SI funciona ahora, pero (a) la
reduccion de tamano es minima porque el peso esta en las carpetas que
se conservan, no en las que se descartan, y (b) el push sigue sin
completarse por credenciales invalidas. yaiwes-nucleo-limpio sigue en
size:0. NO declarar cerrado. Esto reabre la pregunta de fondo: aun
con la limpieza de carpetas funcionando, puede que "yaiwes-nucleo-
limpio" siga pesando varios GB si las carpetas protegidas mismas
tienen historia pesada - haria falta ademas limitar el tamano de blob
(--strip-blobs-bigger-than) dentro de esas carpetas protegidas para
bajar el peso real, algo que no se ha discutido aun con el Director.

SIGUIENTE: (a) pedir al Director un MAXBRY_123_TOKENS valido, (b)
investigar que archivos grandes especificos hay dentro de las 8
carpetas protegidas (usar git rev-list/verify-pack o similar en el
propio filter-repo run) antes de asumir que basta con push, y (c)
proponerle al Director si tambien quiere podar blobs grandes dentro
de esas carpetas o si el tamano actual es aceptable para el repo
limpio.
