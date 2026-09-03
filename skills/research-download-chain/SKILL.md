---
name: research-download-chain
description: Copia, descarga+extrae, reubica y verifica componentes mediante GitHub Actions con deduplicación, fuente fijada, SHA, ZIP por partes, manifiesto y recuperación aislada de GAPS. Úsalo cuando YAIWES, Luna u otro agente deba incorporar código sin reescribirlo.
metadata:
  type: workflow
  version: "3.3.0"
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

Mismo repositorio: `git mv` solo si la orden autoriza explícitamente quitar el origen; de lo contrario usa `cp -a` y conserva el original. Para raíces o lotes, genera primero un mapa `origen → destino → hash`, crea todos los padres con `mkdir -p`, y procesa cada entrada con detección de colisión. Entre repositorios, ejecuta el workflow desde el repositorio destino y usa su propio `GITHUB_TOKEN` para escribir; obtiene el origen en modo solo lectura. No elimines el original sin autorización literal.

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
- No permitas jobs paralelos que hagan push a la misma rama.
- Para varios componentes, copia/verifica en paralelo solo dentro de áreas temporales y realiza un único commit/push secuencial.
- Si usas jobs separados, el job final único recoge artefactos y escribe.
- `concurrency.group` debe incluir repositorio y destino; no uses un grupo global compartido por tareas no relacionadas.
- `cancel-in-progress: false`.
- Antes del push: `git pull --rebase origin <branch>`.
- Reintenta push como máximo tres veces con espera creciente. Una colisión de contenido nunca se reintenta.

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

Crea un workflow nuevo; nunca reactives uno fallido. Debe continuar entre componentes independientes, pero el push será único. Incluye:

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


## 15. Materialización HTTP verificada y dispatch resiliente

Cuando una fuente GitHub fijada a commit contiene un puntero LFS, Git LFS continúa prohibido en esta cadena. No instales ni ejecutes `git lfs`. El reparador puede resolver el objeto real únicamente por HTTPS desde GitHub y convertirlo en blob Git normal, con estas condiciones fail-closed:

1. Parsear del puntero `oid sha256:<64hex>` y `size N`.
2. Resolver `owner/repo + commit + ruta relativa` desde el manifiesto fijado; nunca adivinar fuente/ref.
3. Descargar primero mediante `https://github.com/<owner>/<repo>/raw/<commit>/<path>`; si devuelve todavía el puntero, usar como fallback `https://media.githubusercontent.com/media/<owner>/<repo>/<commit>/<path>`.
4. Exigir `sha256(bytes_reales) == oid` y `len(bytes_reales) == size`.
5. Rechazar el objeto si queda puntero, si SHA/tamaño no coinciden, si la fuente cambia o si el blob final es `>=100 MiB`.
6. Sustituir el puntero únicamente en staging/árbol reparado; conservar el `.gitattributes` original para trazabilidad.
7. Publicar con filtros LFS locales neutralizados y `git push --no-verify` solo después de `ZERO_POINTERS + SIZE_PASS + SHA_PASS`.

Para el LOOP de GitHub Actions:

- el reparador nuevo usa un evento `repository_dispatch` exclusivo por versión;
- el workflow que despacha debe declarar al menos `contents: write` y `actions: write` cuando el repositorio requiera ambos scopes; un 403 se registra como `DISPATCH_PERMISSION_GAP`;
- el finalizador se ejecuta con `if: always()`;
- si falla materialización/publicación, no redispatch ciego;
- si push+read-back pasan y quedan GAPS, despacha el siguiente lote;
- cierre únicamente con `remaining_gaps=0`, `remaining_source_pointers=0`, `oversized_blobs=0`, read-back PASS y auditor independiente.
