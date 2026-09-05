# LEDGER CANÓNICO — PARTES 1–4 — WORDFLOW LOOP YAIWES

Contrato: `tel.workflow/v3`
Regla: no reconstruir texto histórico de memoria; solo literal Git/chat disponible o registro aprobado inmutable.

## PARTE 1 — LITERAL DISPONIBLE
Fuente: commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc`, blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`, INPUT BLOCK 013.
Estado: `LITERAL_GIT_VERIFIED`.
El README canónico contiene físicamente ese INPUT 013 restaurado 1:1.

## PARTE 2 — LITERAL + INTEGRACIÓN
Fuente literal: INPUT BLOCK 014.
Trazabilidad: commit `26760e498a59cb65bb2cdab14f1ac7554e0af0a1` mapea la orden al lote `📂 archivos download/📂Archivo download 1`.
Integración por reuse exacto: commit `4b1c705f891199bb28ec1d0efb14bca223dd440f`.
Estado: `LITERAL_GIT_VERIFIED / READY_DOCUMENTAL`; runtime E2E sigue separado.

## PARTE 3 — REGISTRO APROBADO INMUTABLE
Fuente Git: commit `6b59f4a1514ba419cbeade7c948e68b65d02fe5d` (`record approved Wordflow LOOP programming layer part 3`).
El commit introduce exactamente el contrato aprobado de 12 puntos que permanece en el README bajo `PARTE 3 — CAPA DE PROGRAMACIÓN — APROBADA/ANOTADA`.
Estado de autoridad operativa: `APPROVED_CANONICAL_RECORD`.
Nota de procedencia: Git demuestra el registro aprobado; no se etiqueta falsamente ese contrato como transcripción del mensaje original si el mensaje original no está disponible.

## PARTE 4 — APROBACIÓN LITERAL + MAPA APROBADO
Fuente Git: commit `a4fcb2c9d1286f7a8f9695ff2e54805744e8f7d9` (`record Director Part 4 approval and next LOOP plan literally`).
El commit conserva literalmente el INPUT BLOCK 015, empezando por `Ok anotalo aprobado parte 4 anotalo 1 a 1 ✅`, y el README conserva el mapa funcional aprobado inmediatamente asociado.
Estado de autoridad operativa: `LITERAL_APPROVAL_VERIFIED + APPROVED_CANONICAL_MAP`.

## RATIFICACIÓN DE CORRECCIÓN — DIRECTOR — 2026-09-04
El Director ordena corregir inmediatamente la discrepancia entre lo que se había confirmado como anotado 1:1 y el estado posterior que lo marcó como GAP. Esta orden autoriza fijar como autoridad operativa los registros aprobados Git anteriores, sin inventar wording histórico inexistente.

## REGLA RESULTANTE
- Para ejecución futura, Parte 1–4 se leen desde este ledger + README + commits fijados.
- Parte 3 no se reconstruye desde memoria: se usa el registro aprobado `6b59f4a...`.
- Parte 4 no se reconstruye desde memoria: se usa la aprobación literal `a4fcb2...` + mapa aprobado del README.
- La ausencia de una transcripción histórica adicional no invalida un registro aprobado e inmutable ya existente; sí prohíbe atribuirle wording que Git no demuestra.
- Implementación física, tests y deploy siguen requiriendo evidencia propia; aprobación documental no equivale a `VERIFIED_CLOSED`.