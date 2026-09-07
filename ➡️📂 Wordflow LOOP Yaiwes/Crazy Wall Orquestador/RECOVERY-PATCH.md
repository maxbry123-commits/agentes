# RECOVERY PATCH — Wordflow LOOP Yaiwes

Contrato `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.

## Anclas históricas preservadas
- Recovery anterior recuperable por blob `10f867caef72b284cad2a2e6b349e7e6eb8750eb`.
- Snapshot v3/T16 inmediatamente anterior: blob `5813ded8bdfa00fc866d722216ca5af0bebb4d39`.
- No reconstruir desde memoria ni degradar evidencia posterior.

## Estado reconciliado actual
- Checkpoint: `WFLOOP-PLAN30-0017-ACTIVE`.
- T01–T16 `VERIFIED_CLOSED`; T17 `EN_CURSO`; T18–T30 `PENDIENTE`.
- Avance verificable PLAN30: 16/30 = 53.33%.
- Nodo único: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`.
- Cola: `1x1`.
- O01/O02/O03 `VERIFIED_CLOSED`; O04 `IN_PROGRESS_T17`; O05–O11 `PENDING`.

## Evidencia que no puede degradarse
T16 quedó cerrado por evidencia real:
- artifact `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/EVIDENCE-PLAN30-T16-CLOSED.md`
- artifact blob `bd7aa684e215234616f4bd031a7587219fe9133e`
- workflow run `34075371938`
- workflow job `101600311787`
- workflow head SHA `0cdca40f7653e32c8db3df2e26d6a7b8f4b61f35`
- resultado `YAIWES_T16_CANONICAL_VERIFY=PASS 4/4`
- validador canónico commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`, blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`

STATE reconciliado v4 blob `f2ebd5931676c7afd285438603785a723ca5d260`; commit `42edd7382a8a4e88c3c0d7aea1b323a5dfe855c1`.
CHECKPOINT reconciliado v4 blob `414a16d0b43206fbe01dcf6aa677c20dfeb79539`; commit `922ed1686a1cde25580975910760fbb7f06379c9`.
PLAN v4 blob `185986bfdd6dea4cf9e9beeb85e5c68f171e8324`.

## GAP activo T17
`Agente Yaiwes principal/definition-registry/` contiene estructura/placeholder, pero un Capability Registry runtime compatible todavía no está demostrado. Presencia de carpeta/archivo no equivale a integración.

## Reanudación exacta 1×1
1. Releer guía v4 + STATE + CHECKPOINT + PLAN + este RECOVERY + BITACORA + README arquitectura + HEAD real.
2. Mantener exactamente los 11 objetivos O01–O11 y los 4 pasos del Director.
3. No reabrir T16 ni repetir su validación salvo evidencia nueva de corrupción.
4. Para T17 ejecutar `RESEARCH_REUSE`: buscar Capability Registry runtime reusable primero en Wordflow Yaiwes, todo `agentes`, `Agentes-motores-Wordflow-YAIWES` y repos auxiliares autorizados.
5. Registrar antes de copiar: repo + ruta + URL + commit/blob SHA + función + destino.
6. Prioridad: REUSE > COPY-only > PATCH quirúrgico > ADAPTER > GENERATE.
7. Ejecutar un solo wiring seguro: Ficha Contract v2 → validator → adapter/plugin → registry/slot → mount_guard/loader.
8. Verificar ruta, blob/commit, read-back, imports, registry real, fail-closed y test determinista/runtime según corresponda.
9. Si falla, mantener T17 `GAP` y aplicar StrategyDelta materialmente distinto; no tocar T18.
10. Si PASS real, persistir BITACORA + STATE + CHECKPOINT + PLAN + RECOVERY y activar T18.

## Fail-closed / concurrencia
- `NO_FORCE_GIT`.
- No monolito.
- No mover ni reescribir código ya seleccionado del Director; en Paso 2 solo copiar.
- Antes de cada escritura refrescar HEAD y reconciliar cualquier commit concurrente que toque la misma ruta.
- `PASS_MOCK_ONLY` o presencia no sustituyen runtime real cuando el nodo lo exige.
