---
name: research-download-chain
description: Copia, descarga+extrae, reubica y verifica componentes mediante GitHub Actions y APIs Git de GitHub con deduplicación, fuente fijada, SHA, ZIP por partes, manifiesto y recuperación aislada de GAPS. Úsalo cuando YAIWES, Luna u otro agente deba incorporar o reorganizar código sin reescribirlo.
metadata:
  type: workflow
  version: "3.6.0"
---

# Research Download Chain

Ejecuta, no te limites a explicar. Conserva el alcance literal y usa una sola modalidad por componente: `COPY`, `DOWNLOAD` o `RELOCATE`.

## 1. Entrada obligatoria

Antes de mutar, construye este objeto y detente con `INPUT_GAP` si falta un campo:

```yaml
destination_repository: owner/repo
destination_branch: main
destination_root: ruta/exacta
components:
  - name: nombre-canónico
    source_url: https://github.com/owner/repo
    source_ref: commit_sha_o_tag
    mode: COPY|DOWNLOAD|RELOCATE
    selected_paths: []
rules:
  overwrite: false
  delete: false
  reactivate_old_workflows: false
  single_writer: true
```

Normaliza URL eliminando `.git`, barra final, parámetros de rastreo y diferencias de mayúsculas solo para comparar. No cambies nombres o destinos proporcionados.

## 2. Preflight determinista

Busca antes de descargar en:

1. árbol completo de la rama destino;
2. manifiestos `*.jsonl`, `*.json`, `*.yaml` y `SOURCE_*.txt`;
3. URL normalizada, slug, nombre canónico y SHA;
4. ZIP y partes existentes;
5. runs nuevos activos o terminados para el mismo destino.

Clasificación:

- mismo origen y mismo contenido: `VERIFIED_EXISTING`;
- mismo origen en ruta distinta: `RELOCATE`;
- ausente: modalidad solicitada;
- ruta ocupada con contenido diferente: `COLLISION_BLOCKED`;
- evidencia insuficiente: `INSUFFICIENT_EVIDENCE`.

Nunca uses existencia de carpeta como prueba suficiente.

## 3. Plantillas autorizadas

No redactes de memoria workflows extensos. Copia y edita quirúrgicamente:

- `assets/FORENSIC-PASS-research-download-chain-final.yml`;
- `assets/FORENSIC-PASS-research_download_chain.py`;
- `scripts/research_download_chain.py`.

No invoques plantillas que no existan. Para COPY o RELOCATE crea un workflow nuevo copiando la estructura del asset YAML existente y sustituye únicamente operación, fuentes, rutas, destino, manifiesto y pruebas. Antes de ejecutar, confirma por API que cada archivo de plantilla realmente existe.

Cambios permitidos: nombre nuevo, trigger del archivo nuevo, fuentes, ref fijada, rutas seleccionadas, destino, contadores y nombres de manifiesto/checkpoint.

## 4. Reglas por modalidad

### COPY

Usa `actions/checkout@v4` para destino y origen. Fija `ref` al SHA resuelto. Copia con `cp -a`. Para cada archivo:

```bash
if test -e "$out"; then
  cmp -s "$src" "$out" || exit 31
else
  cp -a "$src" "$out"
fi
```

Código mayor de 100 líneas se copia desde el origen; no se reescribe.

### DOWNLOAD

Usa la plantilla y script existentes. Registra URL, ref/SHA, licencia, destino, estado, partes y hash. Distingue obligatoriamente:

- `ARCHIVE_ONLY`: conservar ZIP/partes como artefacto; no afirmar que el código está instalado.
- `EXTRACTED_TREE`: reconstruir las partes, validar `unzip -tq`, extraer primero en staging temporal, comprobar que contiene archivos reales y copiar el árbol extraído al destino con control de colisiones.

Si el destino solicitado es código utilizable, el modo predeterminado es `EXTRACTED_TREE`. Divide ZIP solo si el límite real del repositorio lo exige. Verifica cada parte, SHA256 del archivo reconstruido y SHA256 del árbol extraído antes de PASS. No dejes ZIP como sustituto del árbol solicitado.

### RELOCATE

Mismo repositorio: para lotes usa preferentemente Git Trees API; `git mv` queda como método de runner solo si la orden autoriza explícitamente quitar el origen. Si no hay autorización para retirar el origen, copia el mismo blob SHA al destino y conserva el original. Para raíces o lotes, genera primero un mapa `origen → destino → blob/hash`, crea todos los padres y procesa cada entrada con detección de colisión. Entre repositorios, ejecuta el workflow desde el repositorio destino y usa su propio `GITHUB_TOKEN` para escribir; obtiene el origen en modo solo lectura. No elimines el original sin autorización literal.

## 5. Selección inequívoca de operación

- URL/repositorio externo → destino: `DOWNLOAD + EXTRACTED_TREE`.
- Archivo o raíz ya presente → nueva ubicación conservando origen: `COPY`.
- Archivo o raíz ya presente → nueva ubicación retirando origen: `RELOCATE`, solo con autorización literal.
- ZIP/partes existentes → código utilizable: `EXTRACT_ONLY`; no redescargues.
- Mismo URL+commit+hash ya en destino: `VERIFIED_EXISTING`; no copies ni descargues.

Cada tarea paralela debe tener `TASK_ID`, workflow, `concurrency.group`, destino, manifiesto y checkpoint exclusivos. Nunca reutilices el estado de otro chat o tarea.

## 6. Extracción segura y verificación

Reconstruye partes en orden natural dentro de staging. Rechaza rutas absolutas, `../`, enlaces que escapen del destino y archivos especiales. Ejecuta:

1. SHA256 de cada parte;
2. reconstrucción;
3. `unzip -tq`;
4. inspección de rutas contra Zip Slip;
5. extracción temporal;
6. conteo de archivos y bytes;
7. hash determinista del árbol;
8. copia con `cmp` y bloqueo de colisión;
9. read-back desde GitHub tras el push.

No borres ZIP ni staging del repositorio salvo autorización; el staging del runner sí puede limpiarse.

## 7. Concurrencia y escritura

- Un destino tiene un solo escritor.
- No permitas jobs paralelos que hagan push a la misma rama si escriben rutas solapadas. Shards con destinos disjuntos pueden ejecutarse en paralelo si cada uno rebasa sobre el `main` remoto antes del push y hace read-back propio.
- Para varios componentes, copia/verifica en paralelo solo dentro de áreas temporales y realiza un único commit/push secuencial por conjunto de rutas solapadas.
- Si usas jobs separados, el job final único recoge artefactos y escribe cuando exista un destino común.
- `concurrency.group` debe incluir repositorio y destino; no uses un grupo global compartido por tareas no relacionadas.
- `cancel-in-progress: false`.
- Antes del push desde runner: `git fetch origin <branch> && git rebase --autostash origin/<branch>`.
- Reintenta push como máximo tres veces con espera creciente. Una colisión de contenido nunca se reintenta.
- Para mutaciones directas por API usa CAS optimista: lee `HEAD=H` y `TREE=T`, construye el tree sobre `T`, crea commit con padre `H`, vuelve a leer `HEAD` y actualiza el ref con `force=false` solo si sigue siendo `H`; si cambió, reconstruye sobre el nuevo snapshot.

## 8. Trazabilidad mínima por componente

En la raíz del componente crea sin sobrescribir:

- `SOURCE_URL.txt`;
- `SOURCE_COMMIT.txt`;
- `SOURCE_LICENSE.txt`;
- `SOURCE_SHA256SUMS.txt`;
- entrada en manifiesto/checkpoint.

Genera hashes con rutas relativas y excluye el propio manifiesto:

```bash
(cd "$root" && find . -type f ! -name SOURCE_SHA256SUMS.txt -print0 |
  sort -z | xargs -0 sha256sum > SOURCE_SHA256SUMS.txt)
(cd "$root" && sha256sum -c SOURCE_SHA256SUMS.txt)
```

## 9. GitHub Actions

GitHub Actions es el mecanismo primario para **adquisición externa, descarga, reconstrucción/extracción, entrega final del payload y read-back**. La reorganización masiva de archivos que ya existen en el mismo repositorio usa preferentemente Git Trees API para evitar runners innecesarios y commits intermedios.

Para adquisición crea un workflow nuevo; nunca reactives uno fallido. Debe continuar entre componentes independientes, pero el push será único por destino solapado. Incluye:

1. checkout destino;
2. checkout/fetch de fuentes con SHA fijado;
3. preflight y deduplicación;
4. copia/descarga/reubicación;
5. manifiestos y hashes;
6. verificación antes de commit;
7. commit único y push seguro;
8. read-back en un job posterior cuando sea necesario.

Un job activo no es PASS. `skipped` solo es aceptable cuando el manifiesto prueba `VERIFIED_EXISTING`.

## 10. Recuperación de GAPS

Inspecciona primero job, paso y logs. Crea `repair-NN` nuevo exclusivamente para el GAP comprobado. No reejecutes ni edites el workflow viejo para ocultar historial.

Mapa de fallos:

- `fetch first/non-fast-forward`: nuevo repair con escritor único;
- `404`: comprobar fuente oficial; no sustituir sin evidencia;
- `COLLISION`: bloquear y reportar ambas huellas;
- SHA incorrecto: regenerar desde archivos reales y verificar read-back;
- parte ZIP ausente: reparar solo esa fuente/componente;
- timeout/red: retry acotado; después GAP;
- dependencia ausente: registrar, no declarar PASS.

## 11. Gate de autoevolución YAIWES

La investigación produce propuesta y estado `AWAITING_DIRECTOR`. Solo tras autorización explícita se adquiere código. Después deben pasar: licencia, sandbox, Sheriff, pasaporte, ABI/adapter, pruebas, hot-swap y rollback. El LLM propone; nunca autoriza mutaciones ni declara PASS.

## 12. Cierre obligatorio

Entrega URLs de workflow/run, destino, manifiesto y checkpoint; además:

```yaml
expected_components: N
verified_components: N
gaps: 0
skipped_without_evidence: 0
collisions: 0
active_jobs: 0
sha_check: PASS
read_back: PASS
verdict: VERIFIED_CLOSED
```

No declares `100% PASS` si hay job activo, GAP, colisión, SHA no verificado, enlace roto o evidencia incompleta.

## 13. Auditor externo y autorreparación

El workflow que descarga o extrae nunca puede certificarse a sí mismo como cierre final. Para destinos de código utilizable crea dos workflows nuevos y separados:

1. **Repair Guardian:** procesa únicamente grupos ZIP cuyo árbol extraído no exista, conserva los archivos comprimidos, rechaza Zip Slip, symlinks y colisiones, publica por lotes pequeños y hace read-back.
2. **Watchdog Auditor:** se ejecuta manualmente y por calendario; usa permisos de contenido en solo lectura, realiza cuatro pasadas (`Action/logs`, `SHA/CRC`, `árbol+destino`, `read-back+manifiesto`) y activa el Repair Guardian mediante `repository_dispatch` solo si hay GAPS.

Reglas obligatorias:

- `COMPLETE` en un manifiesto de descarga solo significa archivo adquirido; no significa `EXTRACTED_TREE`.
- Un ZIP válido no demuestra que el código esté instalado.
- `EXTRACTED_VERIFIED` requiere al menos un archivo real no ZIP en la ruta exacta, hash determinista del árbol y, cuando exista mirror, verificación independiente del mirror.
- El productor y el auditor usan `concurrency.group` diferentes y `cancel-in-progress: false`.
- El reparador limita cada corrida; si quedan GAPS se vuelve a despachar sin reactivar workflows antiguos.
- Un `GITHUB_TOKEN` que hace push no activa normalmente otros workflows. Para encadenar usa explícitamente `workflow_dispatch` o `repository_dispatch`, con `actions: write`, y conserva un límite de cierre para evitar recursión infinita.
- No declares `VERIFIED_CLOSED` hasta que el auditor independiente reporte `remaining_gaps=0`, `failures=0`, `active_jobs=0` y confirme la ruta final solicitada.

## 14. Guardia NO-LFS y resiliencia de descarga/extracción

Regla inmutable: **Git LFS está prohibido** para esta cadena. No instalar, ejecutar, hacer fetch/pull/push con `git lfs`, no usar `lfs.allowincompletepush` y no aceptar punteros LFS como archivos extraídos válidos. `actions/checkout` con `lfs: false` es obligatorio, pero no demuestra por sí solo ausencia de filtros heredados.

Antes de `git add` o `git push`:

1. Detecta archivos cuyo contenido empiece por `version https://git-lfs.github.com/spec/v1`. Si aparecen en el payload adquirido o extraído, clasifica `SOURCE_LFS_POINTER_GAP`; no los publiques como si fueran el archivo real.
2. Si el archivo real existe pero un `.gitattributes` heredado aplica `filter=lfs`, neutraliza únicamente en el runner: `filter.lfs.clean=cat`, `filter.lfs.smudge=cat`, `filter.lfs.process=` y `filter.lfs.required=false`. Nunca modifiques el `.gitattributes` del componente para ocultar el origen.
3. Ejecuta `git check-attr filter` sobre los candidatos y exige que ningún archivo nuevo termine con filtro LFS efectivo.
4. Aplica gate de tamaño antes de publicar árbol extraído: un blob individual `>=100 MiB` no puede entrar en Git normal; emite `GIT_BLOB_LIMIT_GAP`. No uses LFS como bypass.
5. Solo después de `ZERO_LFS_POINTERS + ZERO_LFS_FILTERS + SIZE_PASS` se permite staging. Si se necesita bypass de filtros, usa `git hash-object -w --no-filters` + `git update-index --cacheinfo` conservando exactamente los mismos bytes.
6. `git push --no-verify` solo puede usarse después de los gates anteriores para impedir que un hook `pre-push` heredado invoque LFS; nunca para ocultar un puntero o un archivo faltante.

### Descarga resiliente

- Fuente/ref siempre fijada a commit SHA cuando el contrato lo exija.
- Máximo tres intentos por fallo transitorio con espera incremental; elimina staging parcial antes del reintento.
- Para HTTP sigue redirects, usa timeouts y retry de errores transitorios. No declares COMPLETE por HTTP 200 solamente: valida tamaño, SHA/commit y contenido.
- Para archivos automáticos de GitHub no uses el hash del ZIP/tar como identidad primaria del código; usa commit fijado + hash determinista del árbol. Un release asset con checksum publicado puede conservar además su checksum de archivo.
- Si el origen entrega un puntero LFS en lugar del objeto real, no reintentes ciegamente: queda GAP no reintentable hasta localizar una fuente oficial no-LFS compatible con el mismo alcance.

### Extracción endurecida

Antes de escribir en destino valida todos los miembros del archivo: CRC, rutas absolutas, `../`, variantes con `\\`, symlinks, hardlinks, dispositivos/archivos especiales y nombres duplicados que puedan sobrescribirse. Extrae siempre en staging temporal aislado; después compara conteo de archivos, bytes y hash de árbol. Conserva ZIP/partes salvo autorización literal.

### LOOP persistente

`ACQUIRE → VERIFY_ARCHIVE → EXTRACT_STAGING → POINTER/SIZE/ZIP_GUARD → SINGLE_WRITER → PUSH → READ_BACK → CLASSIFY`.

- `retryable(network|timeout|non-fast-forward)` → repair nuevo con máximo tres intentos por causa.
- lote parcial correcto con GAPS restantes → `repository_dispatch` del siguiente repair acotado.
- `SOURCE_LFS_POINTER_GAP|GIT_BLOB_LIMIT_GAP|COLLISION_BLOCKED|UNSAFE_ZIP` → no repetir el mismo push; registrar GAP y esperar reparación de causa.
- El finalizador/auditor debe ejecutarse con `if: always()` o job separado equivalente para que un fallo de push no mate el bucle ni omita el checkpoint.
- Nunca declarar `VERIFIED_CLOSED` sin read-back independiente y `remaining_gaps=0`.
- No ejecutes `git diff --check`, autoformat, trim de whitespace ni normalización de contenido sobre árboles copiados/descargados; el payload debe conservar bytes fuente. Los validadores estructurales solo pueden inspeccionar, no reescribir ni bloquear por estilo.

## 15. Punteros LFS fail-closed y dispatch resiliente

Git LFS está absolutamente prohibido en esta cadena. Si una fuente fijada contiene un puntero LFS:

1. Detecta el prefijo `version https://git-lfs.github.com/spec/v1`.
2. Clasifica el componente como `SOURCE_LFS_POINTER_GAP`.
3. No ejecutes `git lfs`, no uses fetch/pull/push LFS, no uses `lfs.allowincompletepush` y no derives ni descargues el objeto real a partir del OID del puntero.
4. No sustituyas el puntero por bytes obtenidos mediante endpoints de media/LFS ni por ningún mecanismo equivalente.
5. Conserva ZIP, manifiesto, commit fuente, ruta y evidencia del puntero.
6. Aísla el componente bloqueado y continúa únicamente con componentes independientes que no dependan de ese GAP.
7. Solo puede cerrarse el GAP si existe una fuente ordinaria independiente, trazable y autorizada que entregue el archivo real sin usar el puntero/OID LFS como mecanismo de recuperación; SHA, tamaño, ruta y equivalencia deben verificarse antes de publicar.
8. Nunca marques `EXTRACTED_VERIFIED` ni `VERIFIED_CLOSED` mientras el árbol final contenga un puntero LFS o falten archivos obligatorios del alcance seleccionado.

Para el LOOP de GitHub Actions:

- usa un evento `repository_dispatch` exclusivo por versión de repair;
- el workflow que despacha debe declarar `contents: write` y `actions: write` cuando sean necesarios; un 403 se registra como `DISPATCH_PERMISSION_GAP`;
- el finalizador se ejecuta con `if: always()`;
- un GAP no reintentable se persiste y no genera redispatch ciego;
- si push + read-back pasan y quedan GAPs reintentables, despacha el siguiente lote;
- cierre únicamente con `remaining_gaps=0`, `remaining_source_pointers=0`, `missing_required_files=0`, `oversized_blobs=0`, read-back PASS y auditor independiente.

## 16. Hardening de archivos, límites y reproducibilidad

Antes de extraer cualquier ZIP:

- construye el inventario completo de miembros antes de escribir un solo byte;
- rechaza nombres duplicados que resolverían a la misma ruta, colisiones por normalización/case-fold cuando el destino pueda colisionar, rutas UNC, letras de unidad Windows, NUL, rutas absolutas y traversal;
- calcula `declared_uncompressed_bytes = sum(file_size)` y `declared_compressed_bytes = sum(compress_size)`;
- compara el tamaño declarado con un presupuesto explícito y con el espacio libre del runner; si la expansión prevista puede agotar disco/memoria, emite `ARCHIVE_RESOURCE_LIMIT_GAP`;
- limita también ratio de expansión por miembro y acumulado; una entrada sospechosa nunca se extrae parcialmente al destino;
- el tamaño del lote debe presupuestarse por volumen acumulado (partes ZIP/bytes previstos), no solo por número de componentes; si un componente individual domina el presupuesto, procésalo solo y no permitas que quede oculto detrás de componentes pequeños;
- cuando la fuente sea GitHub y el commit esté fijado, usa el tree del commit para estimar `blob_count`, `source_tree_bytes` y `max_blob_bytes` sin descargar el payload; si el árbol individual es grande, aísla ese componente antes de la extracción y verifica el límite de blob;
- extrae en staging y vuelve a contar bytes reales después de la extracción.

Para archivos fuente generados por GitHub:

- un archivo ZIP/tar de un commit puede regenerarse con distinta compresión aunque el contenido extraído sea el mismo; no uses el SHA del contenedor generado como identidad canónica permanente;
- la identidad reproducible es `source_commit + deterministic_tree_sha256`; conserva SHA del archivo descargado como evidencia de transporte de esa corrida;
- ramas/tags deben resolverse a commit antes de adquirir.

Para HTTP/API:

- sigue redirects;
- usa peticiones seriales para no provocar secondary rate limits;
- respeta `Retry-After` y `x-ratelimit-reset`;
- aplica backoff acotado solo a errores transitorios;
- no repitas mutaciones a ciegas y no conviertas 403/404/422 en retry infinito.

## 17. Supervisor único, Sentinel pasivo y LOOP sin tormenta de dispatch

Una cadena de recuperación tiene **una sola autoridad de mutación/dispatch por destino**. No permitas que Repair Guardian, Watchdog Auditor, Sentinel y Supervisor despachen reparaciones simultáneamente para el mismo `repository + branch + destination_root`.

Roles:

- **Repair Guardian / Single Writer:** único escritor del árbol y único proceso que puede publicar el lote actual.
- **Supervisor:** único actor autorizado para decidir el siguiente `repository_dispatch` cuando termina el lote y el read-back confirma que quedan GAPs reintentables.
- **Watchdog Auditor / Sentinel:** solo inspeccionan estado, jobs, logs, hashes, árbol, destino y read-back. No despachan si ya existe Supervisor activo para la misma cadena.
- **Judge/Guardian de cierre:** solo certifica; nunca muta ni reabre trabajo.

Reglas anti-duplicación:

1. Antes de despachar, consulta runs `queued|pending|in_progress` del mismo repair/concurrency group.
2. Si existe uno activo, registra `ACTIVE_REPAIR_EXISTS` y no crees otro.
3. Usa un `concurrency.group` estable por `repository + branch + destination_root`; `cancel-in-progress: false`.
4. Runs cancelados por exclusión de concurrencia no cuentan como fallo de contenido; clasifícalos `CONCURRENCY_SUPERSEDED`.
5. No uses simultáneamente auto-dispatch del Repair Guardian y dispatch del Watchdog para la misma cadena.
6. Un Sentinel externo o tarea horaria puede auditar, pero no debe crear una segunda cola de escritores.

### Read-back después de un push válido

Si `commit/push=PASS` pero falla el paso posterior de read-back, no vuelvas a extraer ni publiques el mismo lote a ciegas.

Secuencia obligatoria:

`PUSH_PASS → FETCH_REMOTE_MAIN → VERIFY_COMMIT_REACHABLE → VERIFY_PATHS/HASHES → REBUILD_CHECKPOINT → CONTINUE`.

Clasificación:

- commit alcanzable y archivos/hashes correctos → `READ_BACK_CONTROL_GAP`; repara solo el control/checkpoint.
- commit ausente → `PUSH_VISIBILITY_GAP`; verifica ref/branch antes de cualquier retry.
- contenido remoto distinto → `READ_BACK_CONTENT_MISMATCH`; bloquear y auditar colisión/origen.
- no vuelvas a adquirir ZIP si el archivo existente y su SHA ya están verificados.

El finalizador debe conservar evidencia aunque falle el control posterior al push. Usa `if: always()` y separa `content_result` de `control_result`.

### Política de lote adaptativa

El límite por número de componentes es secundario al volumen real:

- calcula bytes ZIP, bytes previstos de extracción, cantidad de archivos y mayor blob;
- componentes pequeños pueden agruparse;
- componentes grandes se procesan solos;
- un GAP no reintentable se aísla y no consume los siguientes ciclos;
- si el throughput cae por cola/concurrency, reduce fuentes de dispatch antes de aumentar paralelismo.

### Gate final del LOOP

El Supervisor solo puede emitir otro dispatch cuando:

`active_writer_jobs=0 AND last_push=PASS AND read_back=PASS AND retryable_gaps>0`.

Debe detener el LOOP automático cuando:

- `remaining_gaps=0` → pasar a auditor independiente;
- `retryable_gaps=0 AND blocked_gaps>0` → `GAPS_PENDING_NONRETRYABLE`;
- `active_writer_jobs>0` → esperar sin duplicar;
- `read_back!=PASS` → reparar primero el control/read-back;
- cualquier intento de LFS → `SOURCE_LFS_POINTER_GAP` o GAP de política, sin workaround.

`VERIFIED_CLOSED` requiere además `active_jobs=0`, cero colisiones/failures, SHA/CRC/tree/destination/read-back PASS y auditor independiente PASS.

## 18. Métodos de MOVE/COPY/DELETE en el mismo repositorio

### Método primario: Git Trees API

Úsalo para organización masiva o movimientos de muchos archivos ya existentes:

1. lee el commit HEAD `H` y su tree `T`;
2. crea el mapa exacto `source_path → destination_path → mode/type/blob_sha`;
3. COPY: añade `destination_path` con el mismo `blob_sha` y conserva origen;
4. MOVE: añade destino con el mismo `blob_sha` y marca el origen con `sha:null` solo cuando la retirada esté autorizada;
5. DELETE: `sha:null` únicamente para un archivo cuya eliminación esté explícitamente autorizada y que no sea código/componente protegido;
6. crea tree con `base_tree=T` y después commit con padre `H`;
7. vuelve a leer HEAD; si cambió, descarta el intento de publicación y reconstruye sobre el nuevo snapshot;
8. actualiza el ref con `force=false`;
9. read-back recursivo y comparación de rutas + blob SHA.

Este método evita descargar/re-subir bytes y conserva identidad de blob. Para un árbol movido, enumera cada archivo: Git no almacena carpetas vacías y una carpeta no es una entidad movible por sí sola.

### Método secundario: Contents API

Úsalo para pocos archivos de texto o cambios puntuales. Siempre lee primero el SHA actual. Ejecuta create/update/delete de forma serial cuando afecten la misma rama o área; no mezcles create/update y delete en paralelo porque pueden entrar en conflicto. Después haz read-back.

### Método runner/local Git

Úsalo cuando la operación forma parte natural de una Action de adquisición/extracción o cuando se necesita una transformación Git que la API no expresa cómodamente. Para MOVE autorizado usa `git mv`; para COPY usa `cp -a`; para publicación usa fetch + rebase y push sin force. No uses runner solo para reorganización masiva si Git Trees API resuelve la operación de manera atómica.

### Método branch + commit + PR

Úsalo cuando la rama destino está protegida, existe una política de review o se necesita una barrera humana. Construye el cambio en una rama dedicada, verifica hashes/rutas, abre PR y fusiona únicamente cuando las reglas del repositorio lo permitan.

### Matriz de selección

| Situación | Método |
|---|---|
| Muchos MOVE/COPY/DELETE en el mismo repo | Git Trees API |
| 1–pocos archivos de texto | Contents API serial |
| Descarga/extracción externa y entrega | GitHub Actions |
| Rama protegida / revisión requerida | Branch + PR |
| Operación Git especial dentro de adquisición | Runner/local Git |

Reglas universales:

- **Nunca borres código ni componentes por deduplicación.** Si dos árboles de código son idénticos, conserva el canónico y solo retira otro si la orden lo autoriza literalmente como MOVE; en caso contrario conserva ambos y registra la identidad.
- Para documentación no-code, deduplica solo tras probar SHA/hash idéntico y conservar una copia canónica.
- Si no puedes demostrar que un archivo no es código/componente, no lo borres: `CLASSIFICATION_GAP`.
- No muevas, borres ni reescribas una ruta destino sobre la que exista una GitHub Action activa. Espera su cierre o trabaja únicamente sobre rutas disjuntas.
- Nunca uses `force=true`/force-push para organización.
- Un commit creado pero no alcanzable desde la rama no cuenta como cambio aplicado.
- El cierre exige read-back desde la rama publicada, no desde el tree/commit local recién creado.
