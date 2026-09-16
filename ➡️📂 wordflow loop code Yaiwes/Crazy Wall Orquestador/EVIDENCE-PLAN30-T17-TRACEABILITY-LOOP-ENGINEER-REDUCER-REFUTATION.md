# EVIDENCE — PLAN30 T17 — Loop Engineer reducer.py refutation

Contrato operativo: `tel.workflow/v4`
Modo: `FAIL_CLOSED_EXECUTION_LOOP`
Nodo: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`
Paso Director: `2 — COPY_ONLY`
Cola: `1x1`

## Sheriff / pre-delta
- Repo principal: `maxbry123-commits/agentes`
- HEAD pre-delta: `81470bc5e7ab95073692957e55e5883e3e8e3810`
- CHECKPOINT actual: `WFLOOP-PLAN30-0017-ACTIVE`.
- T01–T16 VERIFIED_CLOSED preservadas.
- GAP literal: Capability Registry/plugin lifecycle runtime compatible aún no demostrado.
- Delta autorizado: inspeccionar un único donor REFERENCE aún no refutado; no copiar si no cumple.

## Donor inspeccionado
- Repo: `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
- Repo HEAD observado: `0ca97d7c7e8a2e20e986d18e273c6171a2684d30`
- Ruta: `Loop Engineer/Loop-Engineer/loop/reducer.py`
- Blob: `4860716a67238f9c9436ce5ca4a667731f3286d1`
- URL: https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/blob/0ca97d7c7e8a2e20e986d18e273c6171a2684d30/Loop%20Engineer/Loop-Engineer/loop/reducer.py
- Función observada: reducer determinista puro de eventos `event@1`; reconstruye proyección de estado, valida secuencia/hash-chain, FSM, terminales, approvals, pausas/reanudaciones y evidencia estructural.

## Verify/refute T17
Carril requerido para aceptar donor T17: `Ficha Contract v2 → adapter/plugin → registry/slot → mount_guard/loader → wiring/router/handoff`.

Resultado de inspección directa:
- `reducer.py` declara explícitamente `Pure deterministic event@1 reducer; persistence is deliberately not involved.`
- Implementa `reduce_events`, `_reduce_one`, validación de transición FSM y semántica de terminal/evidence.
- No implementa Capability Registry de plugins/capacidades.
- No implementa registro dinámico de plugin por Ficha Contract v2.
- No implementa slots/capability map.
- No implementa loader ni mount_guard de plugins.
- No implementa binding adapter/plugin→registry→engine.
- No ejecuta lifecycle de plugins ni wiring/router/handoff.

## Veredicto
`REFUTED_AS_T17_DONOR`.

`reducer.py` es reutilizable para replay determinista, validación FSM y reconstrucción de estado, pero es materialmente distinto del runtime registry/loader/binding exigido por T17. Por regla `archivo presente ≠ integrado`, no se copia, no se mueve y no se modifica.

## Seguridad / concurrencia
- `NO_FORCE_GIT`: respetado.
- `NO_REESCRIBIR_TRABAJO_VERIFICADO`: respetado.
- `NO_MONOLITO`: respetado.
- Origen intacto: solo lectura.
- Destino de runtime T17: sin modificación.
- No COPY/PATCH/ADAPTER ejecutado porque el donor no superó verify/refute.

## Estado posterior del nodo
- T17 permanece `ACTIVE_LOOP`.
- GAP permanece: falta Capability Registry/plugin lifecycle ejecutable compatible con el carril de Enchufe Universal.
- Siguiente StrategyDelta 1×1: continuar con el siguiente source-root/candidato `SELECTED/REFERENCE` de trazabilidad aún no refutado y aceptar solo con provenance completa + registry/slot + loader/mount_guard + binding ejecutable.