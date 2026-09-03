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
