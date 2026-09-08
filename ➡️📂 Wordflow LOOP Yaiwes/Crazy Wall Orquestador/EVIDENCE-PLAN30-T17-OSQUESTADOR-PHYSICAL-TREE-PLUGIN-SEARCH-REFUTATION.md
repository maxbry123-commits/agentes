# EVIDENCE — PLAN30 T17 — osquestador-auditor physical-tree/plugin search refutation

Contrato operativo: `tel.workflow/v4`
Modo: `FAIL_CLOSED_EXECUTION_LOOP`
Nodo: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Paso Director: `2 — COPY_ONLY`
Cola: `1x1`

## Sheriff / pre-delta
- Repo principal: `maxbry123-commits/agentes`.
- HEAD pre-delta: `91b7a2c626c3eca50d2643653f46c36b744273a1`.
- T01–T16 se preservan; T17 permanece activo.
- GAP literal: Capability Registry/plugin lifecycle runtime compatible aún no demostrado.
- Concurrencia: HEAD real fue releído inmediatamente antes de escribir y permanecía en `91b7a2c626c3eca50d2643653f46c36b744273a1`.
- Delta 1×1: complementar la refutación semántica previa con inspección física del tree del repo autorizado y una búsqueda literal simple de `plugin`, sin COPY si no aparece donor seleccionable.

## Donor/repo inspeccionado
- Repo autorizado: `maxbry123-commits/osquestador-auditor`.
- Commit/tree inspeccionado: `48989743ac454da41b42ed2dbef3eaf4614c3e62`.
- URL: https://github.com/maxbry123-commits/osquestador-auditor/tree/48989743ac454da41b42ed2dbef3eaf4614c3e62
- Trazabilidad canónica: orden de búsqueda antes de programar incluye `osquestador-auditor` después de `router-universal-router-inteligente-`.

## Evidencia física
Se leyó el tree recursivo real del commit `48989743...`. El tree contiene código y vendor roots extensos (por ejemplo `AFFiNE/...`) y workflows, por lo que la ausencia de resultados en una búsqueda de índice no se interpreta como ausencia absoluta del repositorio.

Búsqueda literal adicional sobre el repo autorizado:
- Query: `plugin`
- Resultado del GitHub code search: `0` resultados.

## Verify/refute
Carril requerido T17: `Ficha Contract v2 → validator → adapter/plugin → registry/slot → mount_guard/loader → wiring/router/handoff`.

- La inspección física confirma que el repo no está vacío y que existen múltiples roots/vendor trees.
- La búsqueda literal `plugin` no produjo ruta de código seleccionable mediante el índice disponible.
- No se obtuvo en este delta un archivo con repo+ruta+blob SHA+función que demuestre `registry/slot/loader/mount_guard/binding` compatible.
- Por fail-closed, `0` resultados del índice NO prueba ausencia absoluta dentro de todos los vendor roots del tree.
- Por la regla `NO_MONOLITO` y `SOLO COPIAR`, tampoco se autoriza copiar un vendor root completo para “buscar después”.
- Sin donor mínimo trazable y seleccionable, no se ejecuta COPY_ONLY.

## Veredicto
`REFUTED_INDEX_BRANCH_AS_T17_DONOR_SEARCH`.

Este delta cierra únicamente la rama de búsqueda literal indexada `plugin` y confirma físicamente que el repo requiere inspección dirigida de roots si se continúa. T17 permanece abierto.

## Seguridad
- `NO_FORCE_GIT`: respetado.
- `NO_REESCRIBIR_TRABAJO_VERIFICADO`: respetado.
- `NO_MONOLITO`: respetado.
- Repo donor: solo lectura.
- No COPY, MOVE, PATCH ni generación runtime.
- T01–T16 no se tocaron.

## Estado posterior
- T17: `ACTIVE_LOOP`.
- GAP: Capability Registry/plugin lifecycle compatible aún no demostrado.
- Siguiente delta 1×1: seleccionar un único root físico del tree `osquestador-auditor` que por nombre/estructura tenga semántica de extensión/runtime y auditarlo por ruta+blob; si no existe candidato claro, avanzar al siguiente donor autorizado por trazabilidad sin programar código nuevo.