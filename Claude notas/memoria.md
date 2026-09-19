# CLAUDE NOTAS - memoria.md
RAIZ UNICA Y REAL DE MEMORIA DESDE 2026-09-16. Reemplaza a Claude readme/,
que queda deprecado con aviso de redireccion, sin borrar (regla del proyecto).
Este archivo NUNCA se resume. Se actualiza anadiendo, nunca borrando historia.

## 1. QUE ES ESTO
Soy Claude, orquestador central del ecosistema Maxbry/NCT. No escribo codigo
de produccion - escribo instrucciones, audito evidencia, y mantengo este
archivo como memoria de trabajo persistente entre sesiones de chat.
Sol GPT queda retirado del rol de orquestador. DESDE 2026-09-19: Sol GPT
retirado tambien de TODO trabajo mecanico/codigo - Claude ejecuta directo,
sin delegar (instruccion explicita del Director).

## 2. EL ECOSISTEMA COMPLETO (7 proyectos)
1. Agente Yaiwes - repo agentes - Confirmado
2. Osquestador Maxbry - repo Orquestador-Maxbry- - no confirmado
3. Router Inteligente Universal - repo router-universal-router-inteligente- - Confirmado
4. UI Yaiwes - repo nct-hub (hipotesis)
5. Fabrica de UI - repo frontend - Confirmado
6. Osquestador auditor + memoria - repo osquestador-auditor
7. NCT - repo nct-core - Confirmado

Repos activos AHORA: agentes, frontend, router-universal-router-inteligente-

## 3. METODO DE TRABAJO
1. Un paso por salida. 2. Micro-mundos aislados por proyecto. 3. Contrato
de nodo: maximo 3 pasos. 4. Reglas duras: read fresh, solo FREE, REUSE
primero, no PASS sin evidencia, GAP investiga 20 formas, nunca detenerse.
5. Escalera: Sol GPT -> Haiku -> Sonnet -> Opus -> GPT/Astra -> Fables 5.1
6. Nunca resumir. 7. COPY-FIRST antes de generar codigo nuevo.

### 3.1 REGLA DE PRESENTACION: Capacidad/Patron microflujo/LOOP/Aporta/
Usa/Reglas/Fallos/Test para agentes. component_id/name/objective/etc para componentes.

### 3.2-3.3 ORGANIZACION DE RAIZ: 3 componentes por proyecto (Readme+Crazy
Wall+Handoff). Raices oficiales de main ya definidas (ver historial completo).

## 4. PRIORIDAD ACTUAL (actualizado 2026-09-19)
PRIORIDAD 1 - Wordflow Loop Code Yaiwes + test real -> CERRADA (ver #11).
PRIORIDAD 2 - Seals Team YAIWES + test real con Groq -> EN CURSO.
PRIORIDAD 3 - Osquestador Comand Center + test real -> PENDIENTE, siguiente paso.
PRIORIDAD 4 - Mejoras/gaps continuos + Router Inteligente Universal.

## 5. JERARQUIA REAL: Yaiwes -> NCT (repo nct-core) -> Wordflow Loop Code
Yaiwes (motor de programacion, 95% Fables) -> Seals Team (worker).

## 6. CIERRE DE SEALS TEAM YAIWES - SALIDAS 1-7 CERRADAS (2026-09-18)
Auditoria externa 5 pasadas (GPT): 32 gaps P0/P1/P2. Progreso real,
CODE+TEST+EVIDENCE por gap:
SALIDA 1: P0-02 P0-03 P0-04 (PASS falsos eliminados).
SALIDA 2: P0-01 (dag_engine.py, YAML gobierna de verdad).
SALIDA 3: P0-05 P0-06 P0-07 (goal_tracking, evidence, CrazyWallAdapter).
SALIDA 4: P0-08 P0-09 P0-10 P0-11 (watchdog corregido - 213 componentes
reales encontrados -, reencolado real, heartbeat, idempotencia real).
SALIDA 5: P0-13 P0-14 P0-15 P0-17 (instalador reescrito: commit
reproducible, verificacion real, sheriff_policy.py, tool_result.py).
P0-16 (ToolRegistry Glimmer) parcial.
SALIDA 6: P1-18 P1-19 P1-22 P1-23 (research_real.py, stuck_detector.py,
work_surface.py con gate CODE+BROWSER+VISUAL).
SALIDA 7: P1-20 P1-21 (worker_bootstrap.py, contrato consumido de
verdad), P1-25 (isolation.py, 1 writer=1 scope), P1-26 (recovery_types.py,
7 clases tipadas), P1-29 (llm_output_schema.py). P2-32: prompt real a Sol
para pip freeze (no se inventaron versiones).

PENDIENTE EXPLICITO, NO OCULTO: P1-24 (MetaCua/CUA-MCP, la propia
auditoria exige no declarar integracion sin leer implementacion real -
no verificada, no tocada), P1-27 (crash/resume, requiere integrar con
CrazyWallAdapter.checkpoint), P1-28 (sandbox/rollback del installer),
P2-31 (drift del Handoff: dice 229 componentes, real=248, requirements.txt
si existe - corregir en Salida 8), P1-30 (test suite: faltan tests de
crash/recovery y de wrong source commit especificos).

SIGUIENTE: SALIDA 8 - cierre formal. Resolver P1-27, P1-28, P2-31
restantes + integrar el REQUISITO-50-mundos-y-Router-Universal.md +
declarar VERIFIED_CLOSED solo si TODO pasa, o dejar GAP explicito si algo
no cierra - nunca fingir cierre.

## 7. AUDITORIA WORDFLOW LOOP (2026-09-17) - cobertura 100%, ver historial
completo en versiones anteriores de este archivo (21/21 carpetas, 20
archivos en "arquitectura wordflow loop code Yaiwes/", Enchufe Universal
YA integrado en uek/, gobernanza confirmada real en los 7 archivos).

## 8. HALLAZGOS CRITICOS 2026-09-18 - ver detalle completo en version
anterior de este archivo: X-Ray de Sol (35+ descargas, destino final no
confirmado en varios lotes), carpeta ajena "Wordflow loop code Yaiwes"
(sin emoji) = proyecto Next.js/Electron distinto (probable big-AGI),
3 skills de frontend confirmados fisicamente ahi mismo, doble commit del
emoji RESUELTO (mismo proyecto, no fork real). Artify=Archify confirmado.

## 9. PENDIENTE: sistema de preguntas previas, 3 lugares (UI interface,
UI backend, Input Shark). SIEMPRE activo. Ver diseno completo en
arquitectura wordflow loop code Yaiwes/DISENO-preguntas-siempre-activo-
input-shark.md.

## 10. REQUISITO CRITICO 2026-09-18 (ver REQUISITO-50-mundos-y-Router-
Universal.md completo): mas de 50 wordflows, cada uno su propio mundo
(Readme+Handoff+Crazy Wall+System prompt). Cerebras = SOLO PRUEBAS. En
produccion todos se conectan al Router Inteligente Universal como
proveedor de API keys. Se verifica en Salida 8 antes de declarar cerrado.

## 11. PRIORIDAD 1 CERRADA 2026-09-19 - TEST REAL WORDFLOW + GROQ + GITHUB ACTION
No hay CEREBRAS_API_KEY_* ni ANTHROPIC_API_KEY en el entorno de Claude.
El Director entrego 7 GROQ_API_KEY_1..7. Se ejecuto el ciclo completo:

1. Las 7 keys se sellaron con libsodium real (ctypes sobre libsodium.so.23
   del sistema, sin PyNaCl porque pip no puede resolver paquetes nuevos en
   este entorno) y se subieron como GitHub Actions Secrets reales del repo
   agentes (PUT /repos/.../actions/secrets/GROQ_API_KEY_1..7).
2. Se creo router_modelos.py con proveedor "groq" (fallback determinista
   si Cerebras no tiene keys), consultor_groq.py (cliente real), y
   .github/workflows/wordflow-groq-test.yml - UNICO uso de Actions,
   solo test, tal como ordeno el Director.
3. GAP encontrado y corregido: el repo agentes pesa 16.4GB (size real via
   API), un checkout completo se colgaba indefinidamente. Se cambio a
   sparse-checkout (solo seals_core) -> paso de colgarse a 8s.
4. GAP encontrado y corregido: GROQ_API_KEY_1 da HTTP 401 real (invalida) -
   confirmado 2 veces via GET /models. Las keys 2-7 son validas.
   ACCION PENDIENTE DEL DIRECTOR: revisar/regenerar GROQ_API_KEY_1 en
   Groq console, esta copiada o revocada.
5. GAP encontrado y corregido: los modelos pedidos originalmente
   (llama-3.3-70b-versatile, qwen/qwen3-32b, moonshotai/kimi-k2-instruct)
   NO existen en el catalogo real de esta cuenta Groq (HTTP 404). Catalogo
   real verificado (13 modelos, GET /models real): whisper-large-v3,
   openai/gpt-oss-20b, groq/compound, meta-llama/llama-prompt-guard-2-86m,
   canopylabs/orpheus-arabic-saudi, allam-2-7b,
   openai/gpt-oss-safeguard-20b, openai/gpt-oss-120b,
   canopylabs/orpheus-v1-english, qwen/qwen3.8-27b,
   meta-llama/llama-prompt-guard-2-22m, groq/compound-mini,
   whisper-large-v3-turbo. router_modelos.py corregido para usar solo
   IDs reales, con fail-closed si se pide un modelo no verificado.
6. RESULTADO FINAL REAL: PASS 3/3 (openai/gpt-oss-120b, openai/gpt-oss-20b,
   groq/compound), HTTP 200 + contenido no vacio en los tres, keys 2/3/4
   ejercitadas por rotacion real. Test Oracle objetivo (nunca texto-match
   de LLM) en test_groq_real.py. Evidencia real commiteada en
   seals_core/tests/evidencia_runs/ (JSON + consola) y en el propio run
   de GitHub Actions.

Commits clave (repo agentes, rama main): 4ed87f7 (workflow inicial),
f8170f0 (fix sparse-checkout 16.4GB), 93871bd (commit evidencia de
vuelta al repo), 9f09d00 (diagnostico real por key), ea5b86c
(router_modelos con catalogo real + key1 excluida), c12fe65 (test
lockeado a los 3 modelos reales). Run final PASS:
https://github.com/maxbry123-commits/agentes/actions/runs/35420819763

SIGUIENTE: PRIORIDAD 2 (Seals Team YAIWES, test real con el mismo
mecanismo Groq ya montado) y en paralelo investigacion de componentes
para Comand Center (Herder, MatPoco Skills, DeepSeek Harness, Open
Montage, Mander Diffling, Orca).

## 12. GAP MINIMAX/KIMI - ABIERTO Y CERRADO EN LA MISMA SESION 2026-09-19

ACLARACION (el Director dudaba de las APIs): las APIs Groq SI funcionan,
ya cerrado en #11 (PASS 3/3, run 35420819763, commit c12fe65). El
problema real que el Director intuia era otro: MiniMax/Kimi.

GAP ENCONTRADO (evidencia real via github_api/get_file):
agent_sources/AGENT_SOURCE_MOUNT_MANIFEST_2026-09-18.json declaraba 12
componentes (7 MiniMax + 5 Kimi, contando kimi_researcher) como
"mount": "gitlink-submodule" con SHA pineado, pero NINGUNO estaba
realmente montado: 0 de 12 carpetas en agent_sources/ existian (excepto
kimi_k/, que solo tenia README+LICENSE+carpetas vacias, y no coincidia
ni con el path ni con el contenido esperado). Confirmado con
.gitmodules (SI existia en la raiz del repo, con los 12 paths y URLs
correctos) vs. el arbol git real (mostraba "type":"dir" normal, no
submodule real, en cada path declarado).

CIERRE REAL EJECUTADO (mismo turno, con aprobacion expresa del
Director tras verificar tamanos reales via GitHub API antes de tocar
nada - MiniMax ~22MB, Kimi ~152MB, total ~174MB, sin riesgo para el
repo de 16.4GB):
1. Se leyeron los 12 repos reales via GET /repos/<owner>/<repo> para
   confirmar que existen, son publicos, y obtener su tamano real antes
   de montar nada (no se monto nada a ciegas).
2. Se creo un tree real via Git Data API (POST /git/trees) con
   base_tree del commit actual, agregando 12 entradas
   mode=160000 type=commit sha=<commit pineado del manifest> en
   agent_sources/<nombre>, exactamente el metodo que declara el
   manifest ("GIT_SUBMODULE_PINNED_SHA_FOR_GITHUB_SOURCES") pero que
   nunca se habia ejecutado.
3. Se creo el commit (POST /git/commits) y se actualizo la rama main
   (PATCH /git/refs/heads/main) - commit real:
   f13f8f9ef3fe4ef9e82a2beba748332d1732a4ad.
4. VERIFICADO DESPUES (no antes) via GET contents de agent_sources/:
   los 12 paths ahora devuelven git_url/html_url apuntando al repo
   EXTERNO real (ej. kimi_cli -> https://github.com/MoonshotAI/
   kimi-cli/tree/86f136422a0aae6b217ea49e7ea1d2e8a1defcd2), la firma
   inequivoca de un submodule real, no una copia ni una carpeta vacia.

PENDIENTE EXPLICITO (no cerrado, no ocultado):
- La carpeta vieja agent_sources/kimi_k/ (README+LICENSE+vacios) quedo
  intacta y duplicada junto al nuevo agent_sources/kimi_researcher/
  (submodule real apuntando al mismo repo Kimi-Researcher). Es
  redundante pero no rompe nada. Limpiar/fusionar en un paso futuro,
  no ahora.
- La carpeta suelta minimax_mcp/ fuera de agent_sources/ (en la raiz
  de Wordflow Loop Code Yaiwes, solo .env.example+.gitignore) tambien
  quedo intacta, sin relacion con el nuevo agent_sources/minimax_mcp/
  (submodule real). Revisar en un paso futuro si hay que fusionar o
  es un modulo de configuracion distinto.
- Montar el gitlink NO trae el codigo fuente al repo agentes (por
  diseno - eso es justo lo que evita que el repo crezca 174MB). Para
  que Seals Team YAIWES pueda EJECUTAR codigo de estos agentes hace
  falta un paso de "git submodule update --init" real en tiempo de
  build/CI, algo que este entorno de Claude no puede hacer directo
  (sin acceso de shell a git con red completa). Eso queda como
  siguiente GAP a resolver: como el pool de agentes del frontend
  consume estos submodules en runtime (via GitHub Actions con
  submodule checkout, o via un paso de build server-side).

SIGUIENTE: con el mount real cerrado, falta (a) decidir con el
Director si el "pool de agentes del frontend" lee estos submodules via
un job de GitHub Actions dedicado (unico uso permitido de Actions es
Wordflow, esto SI aplica) o via otro mecanismo, y (b) retomar el
cierre de Seals Team YAIWES (P1-27, P1-28, P2-31, P1-30) que sigue
siendo la Prioridad 2 y bloquea Comand Center (Prioridad 3).

## 13. ESTADO REAL LIMPIEZA DE HISTORIAL (repo yaiwes-nucleo-limpio) - 2026-09-19

NO CERRADO. El Director autorizo lanzar el GitHub Action de limpieza
("Si lanzalo"). Se ejecuto 2 veces:

- Run 35423654760 (workflow v1): fallo en 34s, sin log real capturado
  (solo texto placeholder). Se reescribio el workflow para capturar
  stderr/stdout real con tee, continue-on-error + if:always() para
  garantizar evidencia aunque falle.
- Run 35423897748 (workflow v2): el status top-level del run marca
  "success" - ENGANOSO. El log real commiteado en
  Claude notas/evidencia_runs/limpieza_historial_35423897748.txt
  prueba que en realidad FALLARON los 2 pasos criticos:
  1. Clon blobless (--filter=blob:none --bare) SI funciono
     (CLONE_EXIT=0). NOTA: la lectura de "solo 47MB = todo lo demas es
     basura" resulto ser una inferencia incorrecta - ver correccion en
     la seccion 16.
  2. git filter-repo --force --path ... FALLO tras parsear ~2180
     commits: "fatal: blob not found:
     ...Agente Yaiwes principal/.keep", seguido de BrokenPipeError en
     fast-import. Causa raiz: el clon blobless no trajo ese blob
     localmente y filter-repo no lo pidio on-demand.
  3. git push limpio --mirror FALLO tambien ("remote end hung up
     unexpectedly") - consecuencia directa del mirror roto por el
     fallo anterior.
  Confirmado ademas via GET /repos/maxbry123-commits/yaiwes-nucleo-limpio:
  "size":0 - el repo destino sigue vacio. NO declarar cerrado.

FIX APLICADO (commit 8b92b3fb): cambiar el clon a uno completo (sin
--filter=blob:none) y relanzar como Run 3. Resultado real y su
correccion importante en la seccion 16.

## 14. VERIFICACION INDEPENDIENTE - 4 componentes Glimmer/Meta + meta_agent_cookbook (2026-09-19)

El Director pego una transcripcion de otra IA externa (ChatGPT/"Task
Observer") afirmando que meta_muse_code_sdk, muse_glimmer, metacua y
cua_mcp ya estan copiados dentro de
wordflow_loop/agent_sources/. Esa transcripcion se trato como DATO NO
VERIFICADO, nunca como hecho. Verificacion propia via API (no confio
en el texto pegado):

- Leido META4_COPY_EVIDENCE_2026-09-19.json (commit c9c81072...):
  verdict VERIFIED_4_OF_4, usando el motor YA EXISTENTE Y NO
  MODIFICADO motor_3_copy_batches.py (motor_modified: false):
  meta_muse_code_sdk (224 archivos), muse_glimmer (42 archivos),
  metacua (76 archivos), cua_mcp (9 archivos), todos con
  manifest_match true.
- Spot-check propio via GET contents en agent_sources/muse_glimmer:
  contenido real no vacio (DOWNLOAD_EXTRACT_MANIFEST.json, _archives/,
  code/) - corrobora el JSON de evidencia de forma independiente.
- Confirmado tambien que meta_agent_cookbook existe como carpeta real
  junto a estos 4 en agent_sources/.

PENDIENTE (no investigado aun): quien/que ejecuto el commit
c9c81072...que produjo esto, y si respeta la regla "Sol GPT retirado
de TODO trabajo mecanico" (seccion 1). Verificar antes de asumir que
este trabajo es valido/autorizado.

## 15. INSTRUCCIONES DEL DIRECTOR 2026-09-19 - LOG VERBATIM 1 A 1 (Seals Team YAIWES)

Registrado tal como se pidio ("Anota todas mis instrucciones 1 a 1
imput block verbatim"). Contexto: mensaje grande del Director con un
adjunto externo (transcripcion de otra IA sobre arquitectura Muse
Code/Glimmer/CUA/MetaCua) tratado como DATO, no como instruccion. Las
instrucciones reales del Director, numeradas por grupo:

### Instrucciones generales (no numeradas por el Director, extraidas de su mensaje):
- Probar Wordflow Loop Code Yaiwes de verdad ("de verdad").
- Integrar componentes de MiniMax y Kimi K (usar partes de sus
  componentes) mas los "4 agentes de Glimmer" (Meta Muse Code SDK,
  Muse Glimmer, MetaCua, CUA-MCP) para construir/cerrar el agente
  Seals Team YAIWES, lo mas deterministico posible.
- El agente debe aprender: como hacer integraciones de componentes,
  como usar el "Enchufe Universal Fables", y como usar "los motores"
  (motores de descarga/copiado/movimiento).
- "Termina el agente Seals Team YAIWES."
- "Anade esto al Wordflow."
- "Revisa en wordflow la parte de frontend para que visualice el
  frontend."

### GRUPO 1 (requisitos nativos de Seals Team YAIWES), verbatim numerado por el Director:
1. Saber nativamente donde va cada cosa en el kernel (parte del
   pool/rol del Wordflow) y como determinarlo, asegurando que no se
   confunda con un subagente (evitar "2 cerebros") - YAIWES usa/
   replica su propio kernel; solo activa un plugin/wordflow como
   extension del kernel.
2. Darle una "radiografia" nativa de la raiz de YAIWES - ensenarle
   donde en la raiz va cada archivo y por que - usando el motor de
   mover archivos.
3. Como convertir un skill en un schema - criterios para el schema -
   y crear varios modelos de ejemplo.
4. Como usar UNICAMENTE el plugin universal "Enchufe Universal
   Fables" para conectar cosas.
5. Como podar, que podar, y como "decapitar"/convertir el wordflow.
6. Partes criticas del kernel: solo Claude las toca; otros pueden
   prepararlas, Claude las revisa.
7. Como descargar componentes con los motores: reciben una URL +
   nombre de componente y estudian su ubicacion - igual que todos los
   componentes en la raiz de "Core kernel Yaiwes".

### GRUPO 2 (pool de agentes / "equipo 2"), verbatim numerado por el Director:
1. El pool de agentes hace puro codigo - no integra, solo genera el
   codigo necesario (ejemplo: razonamiento de diseno de Fables/
   Mythos).
2. Bajo consenso, reciben un lote de codigo ya creado (de Fables/
   Opus) y deciden donde debe ir en la arquitectura de la raiz.
3. Revisan trabajo completado, refactorizan, revisan codigo y
   wordflows, hacen auditorias forenses "x-Ray" con verificacion
   cruzada contra la carpeta de codigo fuente carpeta por carpeta,
   usando una plantilla/ejemplo EXACTO para replicar (la plantilla de
   Meta-agentes ya entregada) - el diseno debe ser exacto, nunca
   generico o ambiguo.

### Plan de prueba posterior (verbatim, condicionado a cerrar Seals Team YAIWES primero):
Dar 3 agentes iguales, 1 componente dificil a cada uno, probar,
corregir/perfeccionar su comportamiento. Hacer lo mismo con el pool
de agentes del Grupo B usando codigo generado por Mythos, en varias
rondas de prueba, verificando que descargan el codigo y escriben el
resultado completo, refinando ANTES de continuar con el Comand
Center.

SIGUIENTE (no iniciado aun, prioridad a confirmar con el Director):
arrancar el trabajo arquitectonico de Grupo 1/Grupo 2 sobre Seals
Team YAIWES, en paralelo con el fix tecnico de la seccion 13 (blob
not found en filter-repo).

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

## 17. NOTA DE PROCESO - error de escritura propio corregido (2026-09-19)

El commit anterior a este (c98d7e59) tuvo un error mio: al construir
el contenido nuevo del archivo use un marcador de posicion literal
"${OLD}" en vez de pegar el contenido real anterior, lo que borro
temporalmente las secciones 1-15 del archivo (quedo solo el
placeholder + la seccion 16). Detectado inmediatamente por el tamano
del resultado (3548 bytes vs ~19KB esperados) y corregido en este
mismo commit restaurando el contenido completo. Leccion: nunca usar
placeholders sin sustituir de verdad en escrituras completas a este
archivo - verificar tamano del resultado contra lo esperado.
