# EVIDENCE — PLAN30 T17 — osquestador-auditor plugin semantics refutation

Contrato operativo: `tel.workflow/v4`
Modo: `FAIL_CLOSED_EXECUTION_LOOP`
Nodo: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Paso Director: `2 — COPY_ONLY`
Cola: `1x1`

## Sheriff / pre-delta
- Repo principal: `maxbry123-commits/agentes`.
- HEAD pre-delta: `b33361bd9778ec9424f95e48279880be40703971`.
- CHECKPOINT: `WFLOOP-PLAN30-0017-ACTIVE`.
- T01–T16 `VERIFIED_CLOSED` preservadas; T17 activo.
- GAP literal: Capability Registry/plugin lifecycle runtime compatible aún no demostrado.
- Concurrencia: HEAD real fue releído inmediatamente antes de esta escritura y permanecía en `b33361bd9778ec9424f95e48279880be40703971`; no se observó commit interpuesto.
- Delta 1×1: auditar una rama semántica materialmente distinta en el siguiente repo autorizado por la trazabilidad, sin COPY si no produce donor seleccionable.

## Donor/repo inspeccionado
- Repo autorizado: `maxbry123-commits/osquestador-auditor`.
- Commit observado: `48989743ac454da41b42ed2dbef3eaf4614c3e62`.
- Tree observado: `fcfae05188394392d4d68144239976d915a8036f`.
- URL: https://github.com/maxbry123-commits/osquestador-auditor/tree/48989743ac454da41b42ed2dbef3eaf4614c3e62
- Justificación: `TRAZABILIDAD-PROYECTO-WORDFLOW-YAIWES.md` fija este repo en el orden de búsqueda antes de programar, después de `router-universal-router-inteligente-`.

## StrategyDelta inspeccionado
La rama anterior de RESEARCH_REUSE había probado consultas generales (`plugin manager register loader slot mount`, `register(`, `factory`) sin donor seleccionable. Para no repetirla se usaron mecanismos concretos equivalentes de runtime de plugins:

1. `class PluginRegistry OR CapabilityRegistry OR mount_guard OR plugin_loader OR bind(`
2. `registry`
3. `PluginManager OR load_plugin OR entry_points OR importlib.metadata`

Resultado del GitHub code search sobre `maxbry123-commits/osquestador-auditor`: `0` resultados para las tres ramas concretas.

## Verify/refute
Carril requerido T17: `Ficha Contract v2 → validator → adapter/plugin → registry/slot → mount_guard/loader → wiring/router/handoff`.

- No se obtuvo ruta de código candidata con `PluginRegistry`/`CapabilityRegistry`.
- No se obtuvo ruta con `mount_guard`/`plugin_loader`/`load_plugin`.
- No se obtuvo ruta con `PluginManager` ni discovery por `entry_points`/`importlib.metadata`.
- No se obtuvo ruta seleccionable bajo `registry` en esta búsqueda.
- Por fail-closed, cero resultados de estas consultas NO se elevan a prueba de ausencia absoluta del repo completo.
- Sí cierran esta rama StrategyDelta concreta y evitan repetirla.
- Sin repo+ruta+blob+función seleccionable no se ejecuta COPY_ONLY.

## Veredicto
`REFUTED_BRANCH_AS_T17_DONOR_SEARCH`.

No se declara `NO_REUSE_FOUND` global; solo queda refutada esta rama semántica específica dentro de `osquestador-auditor`. T17 permanece abierto.

## Seguridad
- `NO_FORCE_GIT`: respetado.
- `NO_REESCRIBIR_TRABAJO_VERIFICADO`: respetado.
- `NO_MONOLITO`: respetado.
- Repo donor: solo lectura.
- No COPY, MOVE, PATCH ni generación runtime ejecutada.
- T01–T16 no se tocaron.

## Estado posterior
- T17: `ACTIVE_LOOP`.
- GAP: Capability Registry/plugin lifecycle compatible aún no demostrado.
- Siguiente delta 1×1: inspeccionar un source-root físico de `osquestador-auditor` o el siguiente donor autorizado únicamente si su tree/ruta muestra semántica explícita `plugin|loader|registry|binding|slot`; aceptar solo con repo+ruta+URL+commit/blob SHA+función+destino y prueba ejecutable.
