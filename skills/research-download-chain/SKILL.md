---
name: research-download-chain
description: Copia, descarga+extrae, reubica y verifica componentes mediante GitHub Actions y Git Data API con verificación fail-closed.
metadata:
  type: workflow
  version: "3.6.0"
---
# Research Download Chain

Ejecuta en LOOP hasta cierre verificable. Para adquisición externa usa GitHub Actions; para MOVE/COPY/DELETE masivo dentro del mismo repositorio usa Git Trees API; para una edición textual pequeña usa Contents API.

## Selección y seguridad
- DOWNLOAD/EXTRACT externo: Actions, checkout lfs:false, staging, CRC/Zip Slip, SHA/hash de árbol, cero punteros/filtros LFS, blob <100MiB, read-back.
- MOVE/COPY interno: Git Trees API reutilizando blob SHA. MOVE retira origen solo con autorización; COPY conserva origen.
- DELETE: solo documentación/basura expresamente autorizada. Nunca borrar código/componentes; incertidumbre=GAP_REVIEW.
- No tocar destinos de Actions activos. Un destino = un escritor.

## Escritura concurrente
Antes de mutar leer HEAD y tree. Crear tree+commit con HEAD como parent y actualizar ref con force=false. Si devuelve non-fast-forward/409/422 porque HEAD avanzó, descartar el commit huérfano, releer HEAD/tree, reconstruir exactamente el mismo cambio sobre el nuevo tree y reintentar. Nunca force-push ni sobrescribir commits ajenos. Para Contents API usar SHA actual del archivo; un cambio en otro path puede coexistir mediante el endpoint, pero cualquier 409/422 obliga a releer y reintentar de forma serial.

En runner: git fetch origin <branch> && git rebase --autostash origin/<branch> && git push --no-verify origin HEAD:<branch>. Máximo tres retries por intento transitorio; si el repositorio sigue recibiendo escrituras, serializar el escritor con concurrency group específico del destino, cancel-in-progress:false.

## Paralelismo
Actions pueden descargar/verificar componentes independientes en paralelo, pero consolidan publicación mediante un único writer. Workflows distintos que escriben la misma rama/destino deben compartir grupo de exclusión; destinos independientes pueden usar grupos distintos. No reactivar workflows fallidos para ocultar historial: crear repair-NN para GAP probado.

## LOOP
AUDIT → CLASSIFY → SELECT_METHOD → EXECUTE → READ_BACK → GAP_ANALYSIS → REPAIR → REPEAT.
Retryable: red/timeout/non-fast-forward. Fail-closed: SOURCE_LFS_POINTER_GAP, GIT_BLOB_LIMIT_GAP, COLLISION_BLOCKED, UNSAFE_ZIP, evidencia insuficiente.

## Cierre
VERIFIED_CLOSED únicamente con expected=verified, gaps=0, failures=0, collisions=0, active_jobs=0, sha_check=PASS y read_back=PASS. Un ZIP adquirido no equivale a árbol extraído; un job activo nunca es PASS.
