# Skills Github acción

## Registro de hardening

### 2026-09-03 — v3.2.0

Parche quirúrgico sobre v3.1.0. Alcance exclusivo: guardia NO-LFS, recuperación de GAP, resiliencia de descarga/extracción y cierre del LOOP.

- Git LFS queda prohibido; `lfs: false` no se considera defensa suficiente.
- Se detectan punteros LFS antes de empaquetar/publicar y se clasifican como `SOURCE_LFS_POINTER_GAP`.
- Los filtros LFS heredados se neutralizan localmente en el runner sin modificar los `.gitattributes` del componente.
- Push sin hooks solo después de gates de puntero/filtro/tamaño.
- Retry acotado para fallos transitorios; no se repite ciegamente una causa no reintentable.
- Extracción: CRC + Zip Slip + symlink/especiales + staging + conteo/bytes + SHA de árbol + read-back.
- El finalizador debe sobrevivir al fallo del escritor para conservar checkpoint y continuidad del watchdog.

### 2026-09-03 — v3.3.0

- El fallo repetitivo principal observado no era red: `.gitattributes` podía activar filtros LFS y provocar GH008/objetos ausentes.
- `actions/checkout lfs:false` no evita por sí solo que `git add/push` invoque filtros/hooks LFS heredados.
- Un árbol con `version https://git-lfs.github.com/spec/v1` nunca es `EXTRACTED_VERIFIED`.
- Un puntero LFS es `SOURCE_LFS_POINTER_GAP`; no se materializa usando su OID.
- Un blob >=100 MiB queda `GIT_BLOB_LIMIT_GAP`.
- `repository_dispatch` con 403 queda `DISPATCH_PERMISSION_GAP`.
- El finalizador usa `if: always()` cuando corresponda para no perder checkpoint/read-back.
- No ejecutar `git diff --check` sobre payload adquirido; se preservan bytes fuente.

### 2026-09-03 — v3.4.x

- Preflight anti-ZIP-bomb y detección de rutas duplicadas/traversal/UNC/drive letters/NUL.
- Identidad reproducible: `source_commit + deterministic_tree_sha256`.
- Requests seriales y backoff solo para errores transitorios.
- Un GAP no reintentable se aísla y no crea tormenta de dispatch.

### 2026-09-04 — v3.7.1 / cierre del bucle repetitivo

Raíz canónica única de este skill: `skills/skills Github acción/`.

Hallazgos obligatorios para Luna y cualquier agente:

1. Separar siempre `remaining_component_gaps`, `control_gaps` y `historical_baseline_rows`; nunca sumar evidencias históricas como fallos nuevos.
2. Un destino tiene un solo publisher/escritor. Preparación puede paralelizarse; publicación sobre la misma rama/destino es serial.
3. Tras conflicto/non-fast-forward de un commit de payload generado: obtener `origin/main` fresco y reconstruir; no rebasear ese commit generado.
4. Antes del commit verificar el índice staged, no solo el working tree: cero punteros LFS y ningún blob >=100 MiB.
5. Si hay que fragmentar, usar partes conservadoras <=45 MiB.
6. Máximo tres retries solo para fallos transitorios. LFS, colisión, tamaño, permisos o fuente incorrecta se diagnostican; no se repiten ciegamente.
7. `PUSH_PASS` no equivale a cierre: exige read-back independiente, hashes/rutas correctos, `remaining_component_gaps=0` y `active_jobs=0`.
8. Un run `queued|in_progress` >24 h es `STALE_RUN_CONTROL_GAP`, no un nuevo GAP de componente.

### Punto operativo confirmado — trigger exclusivo por workflow

Ya confirmé un punto operativo importante: no existe una acción de “dispatch” conectada aquí, así que voy a disparar cada workflow con un archivo **trigger exclusivo**. Eso evita reactivar workflows viejos o que los 11 nuevos se ejecuten uno sobre otros.

## Código ejemplo inmutable

El código de ejemplo **no se redacta otra vez desde cero**. El agente debe copiar el archivo exacto de esta raíz y editar únicamente campos quirúrgicos autorizados (TASK_ID, origen/ref, rutas, destino, operación, manifiesto/checkpoint y grupo de concurrencia). Antes de usar cualquier ejemplo debe leer `ADVERTENCIA-CODE.json`.

- `Code Github acción descargar y extracción/` — workflow + locks Python/YAML para descarga/extracción.
- `Copiar lotes de archivos/` — ejemplos exactos para copia de archivo/lote.
- `Mover lotes de archivos/` — ejemplos exactos para mover archivo/lote/raíz con autorización de retiro.

Los SHA de los locks exactos están registrados en `ADVERTENCIA-CODE.json`; si un SHA cambia, Luna debe detenerse y auditar antes de ejecutar.
