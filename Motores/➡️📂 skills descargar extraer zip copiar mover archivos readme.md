# SKILL — descargar, extraer ZIP, copiar y mover archivos

Estado: CANÓNICO / FAIL-CLOSED / MOTORES INMUTABLES
Repositorio plantilla: `maxbry123-commits/frontend`

## 1. Regla principal

Los motores de esta raíz son **INTOCABLES**.

- PROHIBIDO editar, reescribir, refactorizar, formatear, regenerar o parchear el código fuente de un motor.
- PROHIBIDO crear una variante del motor para resolver un error.
- El código de un motor solo puede transferirse mediante **COPIA EXACTA desde GitHub**.
- Antes de usar o copiar un motor se debe validar su blob SHA contra `MOTOR-CODE-LOCK.json`.
- Si el SHA no coincide: `MOTOR_CODE_LOCK_GAP` y no se ejecuta.
- Un cambio de código requiere autorización explícita del Director/usuario en el chat actual.

## 2. Entorno de trabajo

Todos los archivos operativos del sistema de motores deben permanecer dentro de esta raíz: estados, colas, balances, manifests, locks, logs e índices auxiliares.

No crear nuevas raíces de motores ni archivos auxiliares fuera de este entorno. Un archivo destino de una operación de descarga/copia/movimiento solo puede estar fuera de esta raíz cuando el usuario entregue explícitamente ese destino para esa operación.

## 3. Destinos — regla obligatoria

**Nunca inferir, recordar ni reutilizar un destino anterior.** El usuario entrega el destino en cada operación.

Antes de ejecutar:

- Motor 1: exigir `ARCHIVE_INPUT`, `DEST_DIR`, `STATE_FILE`.
- Motor 2: exigir `QUEUE_FILE`, `STATE_FILE`, `ENGINE_PATH`, `INDEX_PATH`; si publica, exigir además `DEST_REPO`, `DEST_BRANCH`, `DEST_ROOT` y credencial runtime autorizada.
- Engine combinado del Motor 2: exigir `SOURCE_REPO`; si publica, exigir explícitamente `DEST_REPO`, `DEST_BRANCH`, `DEST_ROOT`.
- Motor 3: exigir `SOURCE_DIR`, `DEST_DIR`, `STATE_FILE`, `BATCH_SIZE`.
- Motor 4: exigir `SOURCE_DIR`, `DEST_DIR`, `STATE_FILE`, `BATCH_SIZE`.

Aunque un motor heredado contenga un valor default, **el default está operativamente prohibido**. Si falta un destino explícito, detener con `DESTINATION_INPUT_GAP` y no ejecutar.

## 4. Motor 1 — solo extracción ZIP

Ruta: `➡️📂 Motor de extracción zip/motor_1_extract_only.py`

Función: reconstruir ZIP fragmentado cuando aplique, validar CRC/rutas seguras y extraer en lotes persistentes de 1 a 100.

Aceptación: `VERIFIED_CLOSED`, `failed=0`, `pending=0` y tree hash generado.

## 5. Motor 2 — descarga + extracción en cola persistente

Controlador: `📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`
Engine: `📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`

Función: procesar una cola de repositorios, descargar un ref exacto, crear ZIP determinista, fragmentar cuando sea necesario, reconstruir, extraer, verificar árbol y mantener estado/reintentos.

Balance obligatorio al finalizar:

- total
- download_verified
- extraction_verified
- published_readback_verified
- failed
- pending

También debe generar/actualizar un README índice en la ubicación `INDEX_PATH` entregada explícitamente por el usuario.

## 6. Motor 3 — copiar archivos en lotes

Ruta: `➡️📂motor de copiar archivos/motor_3_copy_batches.py`

Función: copiar archivos en lotes `BATCH_SIZE=1..100` usando staging, `copy2`, SHA-256 y read-back.

Política por defecto de operación recomendada: `COLLISION_POLICY=fail`.

Aceptación: `VERIFIED_CLOSED`, `failed=0`, `pending=0`.

## 7. Motor 4 — mover archivos en lotes

Ruta: `➡️📂motor de moves archivos/motor_4_move_batches.py`

Función: mover archivos en lotes `BATCH_SIZE=1..100`, verificar SHA-256 destino y soportar reanudación segura.

Política por defecto de operación recomendada: `COLLISION_POLICY=fail`.

Aceptación: `VERIFIED_CLOSED`, `failed=0`, `pending=0`; para traslado completo, `source_files_remaining=0`.

## 8. Proceso para copiar estos motores a otro repositorio

1. Leer este skill.
2. Leer `MOTOR-CODE-LOCK.json`.
3. Fetch del código canónico desde GitHub `main`.
4. Verificar que el blob SHA coincide con el lock.
5. Ejecutar Motor 3 sobre una copia de trabajo en lotes de 1 a 100.
6. Verificar SHA/read-back de la copia.
7. Publicar la copia exacta mediante comandos GitHub en el `main` del repo destino.
8. La raíz destino se llama `➡️📂motores de descarga extracción copiado movimiento archivos <NOMBRE_REPO>/`.
9. Solo cambia `<NOMBRE_REPO>`; el código fuente de los motores no cambia.
10. Releer desde `main` y comparar blob SHA.

## 9. Registro obligatorio

Cada operación debe dejar una entrada en `OPERATIONS-LEDGER.jsonl` con:

`timestamp`, `repository`, `motor`, `action`, `source`, `destination`, `batch_size`, `code_blob_sha`, `result`, `commit`, `readback`.

Sin registro + evidencia de read-back, la operación no se considera cerrada.

## 10. Índice de componentes

Cuando Motor 2 procese una cola, se debe generar un `README-INDICE-COMPONENTES.md` en el destino de índice que entregue el usuario. El índice debe listar componente, URL fuente visible, estado, commit fuente y balance descarga/extracción.

## 11. Prohibiciones

- NO LFS.
- NO FORCE PUSH.
- NO sobreescritura silenciosa.
- NO destinos recordados de tareas anteriores.
- NO PASS sin hashes/read-back.
- NO editar motores para adaptarlos a un repositorio.
- NO crear motores alternativos si uno falla; registrar GAP y resolver por configuración/entorno sin alterar el código.
