# ⚠️ SKILL CANÓNICO — DESCARGAR / EXTRAER ZIP / COPIAR / MOVER ARCHIVOS

> **ADVERTENCIA CRÍTICA — LECTURA OBLIGATORIA ANTES DE EJECUTAR**
>
> 1. **LOS MOTORES SON INTOCABLES.** Está prohibido editar, reescribir, refactorizar, formatear, regenerar, parchear o adaptar su código.
> 2. **SOLO SE PUEDE COPIAR EL CÓDIGO FUENTE EXACTO DE LOS MOTORES.** La copia debe conservar el mismo blob SHA de GitHub.
> 3. **NINGÚN DESTINO PUEDE QUEDAR FIJADO POR LA IA.** El usuario entrega el destino de cada operación. Está prohibido inferir, recordar o reutilizar un destino anterior.
> 4. **EL PROCESO DE ESTOS MOTORES SOLO PUEDE OPERAR DENTRO DE SU RAÍZ DE MOTORES**, salvo el destino explícito entregado por el usuario para la operación.
> 5. **NO CREAR RAÍCES, ARCHIVOS AUXILIARES, LOCKS, LEDGERS, TESTS, COLAS O MANIFESTS EXTRA DENTRO DE LA RAÍZ FINAL.**
> 6. **NO LFS. NO FORCE PUSH. NO SOBREESCRITURA SILENCIOSA.**
> 7. **NO PASS SIN READ-BACK.** Una copia solo es válida después de releer `main` y comprobar nombre, allowlist y hashes.
> 8. **MODIFICAR UN MOTOR REQUIERE AUTORIZACIÓN EXPLÍCITA DEL USUARIO EN EL CHAT ACTUAL.** Sin esa autorización: `MOTOR_CODE_LOCK_GAP`.

Estado: `CANONICAL / FAIL_CLOSED / COPY_ONLY / IMMUTABLE_MOTORS`  
Repositorio fuente canónico: `maxbry123-commits/frontend`  
Rama canónica: `main`

---

## 1. Objetivo

Esta raíz contiene los motores autorizados para:

- descargar componentes;
- extraer ZIP;
- copiar archivos;
- mover archivos;
- copiar esta raíz completa de motores + skill a otro repositorio.

La raíz destino siempre debe llamarse:

`➡️📂motores de descarga extracción copiado movimiento archivos <NOMBRE_REPO>/`

El nombre se define **desde la copia inicial**. No se crea con un nombre temporal para renombrarlo después.

---

## 2. Contenido final autorizado de la raíz

La raíz final contiene **solamente** estos siete archivos distribuidos en cuatro carpetas de motores + este skill:

1. `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`
2. `➡️📂 Motor de extracción zip/motor_1_extract_only.py`
3. `📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`
4. `📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`
5. `➡️📂motor de copiar archivos/motor_3_copy_batches.py`
6. `➡️📂motor de copiar archivos/motor_copy_root_to_repo.py`
7. `➡️📂motor de moves archivos/motor_4_move_batches.py`

Cualquier otro archivo dentro de esta raíz produce:

`SOURCE_ALLOWLIST_GAP` o `DESTINATION_ALLOWLIST_GAP`.

---

## 3. Bloqueo de integridad del código

Los siguientes blobs son canónicos e inmutables:

| Archivo | Blob SHA GitHub |
|---|---|
| `motor_1_extract_only.py` | `a52d5dc0e6ff26f75d753b848dcc1a40c5dd4500` |
| `motor_2_queue_download_extract.py` | `84d566e2ee4e98e42eb3a864026d067d48caabd9` |
| `hf_download_extract_engine.py` | `91e6e4486692eab314be5c7130d8310d3c855397` |
| `motor_3_copy_batches.py` | `3689924361ce4a1a9fde4ae2b6f6009c37a6042d` |
| `motor_copy_root_to_repo.py` | `8281211da76db3080fe1f1ea38b3eb0c45d655cb` |
| `motor_4_move_batches.py` | `9a21facfe11327cf60a2afca8f415ad52f0ecbe5` |

Regla: si una copia de cualquiera de esos motores devuelve un blob distinto, la operación falla y no se publica como PASS.

---

## 4. Destino obligatorio y no persistente

El usuario entrega el destino en cada operación.

Está prohibido:

- deducir el repo destino;
- usar un destino de una conversación anterior;
- reutilizar un path anterior;
- confiar en defaults heredados dentro de un motor;
- escribir un destino fijo nuevo dentro del código del motor.

Si falta el destino: `DESTINATION_INPUT_GAP`.

Aunque un motor heredado contenga un default histórico, ese default queda **operativamente prohibido** por este skill.

---

## 5. Motor de extracción ZIP

Ruta:

`➡️📂 Motor de extracción zip/motor_1_extract_only.py`

Entradas obligatorias:

- `ARCHIVE_INPUT`
- `DEST_DIR`
- `STATE_FILE`

Funciones:

- reconstrucción de ZIP fragmentado;
- comprobación CRC;
- bloqueo de rutas inseguras;
- bloqueo de symlink ZIP;
- extracción por lotes;
- persistencia;
- SHA-256/tree hash;
- read-back físico.

PASS:

`VERIFIED_CLOSED` + `failed=0` + `pending=0`.

---

## 6. Motor de descarga + extracción

Controlador:

`📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`

Engine:

`📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`

Entradas de destino, cuando exista publicación, deben ser explícitas:

- `DEST_REPO`
- `DEST_BRANCH`
- `DEST_ROOT`

Además, `ENGINE_PATH`, `QUEUE_FILE`, `STATE_FILE` e `INDEX_PATH` deben entregarse explícitamente cuando correspondan.

PASS solo después de descargar, reconstruir, extraer y verificar read-back.

---

## 7. Motor de copia por lotes

Ruta:

`➡️📂motor de copiar archivos/motor_3_copy_batches.py`

Uso:

- `SOURCE_DIR`
- `DEST_DIR`
- `STATE_FILE`
- `BATCH_SIZE=1..100`

Política recomendada:

`COLLISION_POLICY=fail`

PASS:

`VERIFIED_CLOSED` + `failed=0` + `pending=0`.

---

## 8. Motor dedicado para copiar esta raíz a otro repo

Ruta:

`➡️📂motor de copiar archivos/motor_copy_root_to_repo.py`

Este motor está diseñado exclusivamente para copiar:

**4 carpetas de motores + skill, y nada más.**

Entradas obligatorias:

- `SOURCE_ROOT`
- `DEST_ROOT`
- `DEST_REPO_NAME`
- `BATCH_SIZE` opcional, recomendado `2`

Controles:

1. valida el nombre exacto de la raíz destino;
2. valida que el origen contenga exactamente la allowlist de siete archivos;
3. copia por lotes;
4. usa `.partial` únicamente dentro de la raíz destino durante la operación;
5. verifica SHA-256 antes y después de cada reemplazo;
6. elimina la raíz destino si la operación falla;
7. rechaza colisiones no idénticas;
8. no crea archivos de estado, ledger o manifests;
9. produce el balance únicamente por `stdout`;
10. termina en `VERIFIED_CLOSED` o falla cerrado.

---

## 9. Motor de movimiento

Ruta:

`➡️📂motor de moves archivos/motor_4_move_batches.py`

Entradas:

- `SOURCE_DIR`
- `DEST_DIR`
- `STATE_FILE`
- `BATCH_SIZE=1..100`

PASS:

`VERIFIED_CLOSED` + `failed=0` + `pending=0`.

---

## 10. Protocolo profesional para copiar la raíz a un repo

1. Leer este skill completo.
2. Confirmar que el usuario entregó el repo destino.
3. Leer desde `frontend/main` los motores canónicos.
4. Validar los blob SHA del apartado 3.
5. Definir directamente la raíz:
   `➡️📂motores de descarga extracción copiado movimiento archivos <NOMBRE_REPO>/`
6. Ejecutar la lógica de `motor_copy_root_to_repo.py` en lotes.
7. Publicar mediante GitHub sin force.
8. No copiar ningún archivo que no esté en la allowlist.
9. Releer `main`.
10. Verificar la raíz y los siete archivos.
11. Comparar los seis blob SHA de motores.
12. Registrar la operación mediante el commit GitHub y su evidencia de read-back; **no crear un ledger adicional**.
13. Solo entonces declarar `100% PASS ✅`.

---

## 11. Fallos fail-closed

- Motor modificado: `MOTOR_CODE_LOCK_GAP`
- Destino ausente: `DESTINATION_INPUT_GAP`
- Nombre incorrecto: `DESTINATION_NAME_GAP`
- Archivo extra en origen: `SOURCE_ALLOWLIST_GAP`
- Archivo extra en destino: `DESTINATION_ALLOWLIST_GAP`
- Colisión: `DESTINATION_COLLISION`
- Hash de copia distinto: `COPY_HASH_MISMATCH`
- Hash de read-back distinto: `READBACK_HASH_MISMATCH`
- Branch avanzó durante publicación: no force; releer `main` y reconstruir sobre el nuevo parent.

---

## 12. Criterio de cierre

Una operación está cerrada únicamente cuando:

- la raíz existe en `main`;
- el nombre de la raíz coincide exactamente con el repo;
- contiene únicamente la allowlist autorizada;
- los seis motores conservan sus blob SHA canónicos;
- el skill está presente;
- no existe ningún archivo extra;
- la publicación fue sin force;
- se realizó read-back posterior al commit.

Resultado final permitido:

`100% PASS ✅`
