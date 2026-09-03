# Research Download Chain

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
- Ningún cambio de destino, componente, autorización de overwrite/delete o semántica COPY/DOWNLOAD/RELOCATE.


### 2026-09-03 — v3.3.0

Hallazgos incorporados tras auditoría real de extracción en `router-universal-router-inteligente-`:

- El fallo repetitivo no era red: `.gitattributes` de componentes como Qdrant activaba filtros LFS y el runner intentaba publicar objetos ausentes.
- `actions/checkout lfs:false` por sí solo no evita que `git add/push` invoque filtros/hooks LFS heredados.
- Un árbol no puede llamarse `EXTRACTED_VERIFIED` si contiene texto puntero `version https://git-lfs.github.com/spec/v1`.
- Se añadió materialización HTTPS del objeto real sin instalar ni ejecutar `git lfs`, validando OID SHA-256 y tamaño exacto antes de reemplazar el puntero.
- `raw` puede devolver todavía el puntero; el fallback `media.githubusercontent.com/media/...` se usa únicamente contra fuente+commit+ruta fijados.
- Ningún objeto >=100 MiB se publica como blob Git normal; queda `GIT_BLOB_LIMIT_GAP`.
- Los filtros LFS se neutralizan localmente en el runner y el componente conserva sus `.gitattributes` originales.
- `git push --no-verify` solo se permite después de ZERO_POINTERS/SHA/SIZE PASS.
- Se confirmó un segundo GAP: `repository_dispatch` puede devolver HTTP 403 si el token efectivo no tiene autoridad suficiente; se clasifica `DISPATCH_PERMISSION_GAP`.
- El finalizador del LOOP debe usar `if: always()` para impedir que un fallo de push suprima read-back/checkpoint.
- El retry se limita a causas transitorias; puntero/fuente/hash/colisión/tamaño nunca se reintentan ciegamente.
