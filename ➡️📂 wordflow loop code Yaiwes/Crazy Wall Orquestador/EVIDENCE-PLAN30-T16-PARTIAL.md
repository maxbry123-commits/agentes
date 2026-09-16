# EVIDENCE — PLAN30 T16 — PARTIAL / FAIL-CLOSED

Contrato `tel.workflow/v3`; nodo `PLAN30_T16_FICHA_CONTRACTS`; estado `EN_CURSO`.

## GAP detectado
Los commits `a7655bb806808a52e3359464b868d708ef55f61f` y `9bb7e01b02f5ec82bcaad6c8136e63f59fa80601` materializaron un descriptor provenance propio, pero no implementaban la estructura canónica **Ficha Contract v2.0**. La fuente histórica autorizada `skills/research-download-chain/assets/plugin-bus/ficha_contract_v2.py`, commit `37bef3a8a8f6dadca067638b8ea0c32995fc1d63`, blob `b27f14b4d64f77bccf53a893c49b6f20bd58e745`, exige `artifact_id/version/estado/contrato/ejecucion/seguridad/firma` y las invariantes v2.

## Research ≥10 vías, deduplicado
1. PLAN30 actual — confirma T16 único nodo O04.
2. EVIDENCE T10–T15 — fija 4 capacidades reales porque T12/T13 comparten módulo.
3. README arquitectura YAIWES — exige Ficha/contrato y microkernel modular.
4. `ficha.aws_step_functions.v2.json` — ejemplo real Ficha v2 en `main`.
5. Historial Git `ficha` — descubre fuente `ficha_contract_v2.py` y commits Ficha previos.
6. Commit `37bef3a...` — fuente canónica del validador de 36 invariantes.
7. Commit `a7655bb...` — descriptor schema T16 previo inspeccionado/refutado como sustituto de Ficha v2.
8. Commit `9bb7e01...` — manifiesto provenance T16 previo inspeccionado/refutado como sustituto.
9. Repo `Agentes-motores-Wordflow-YAIWES` — árbol revisado; no aporta Ficha v2 alternativa para estas capacidades.
10. Repo `router-universal-router-inteligente-` — árbol revisado; no aporta Ficha YAIWES aplicable.
11. Repo `osquestador-auditor` — árbol revisado; no aporta Ficha YAIWES aplicable.
12. Read-back de los módulos T10–T14 actuales — entry points y blobs verificados antes de generar contrato.

## StrategyDelta aplicado
Se conserva el descriptor provenance y se separa del contrato ejecutable. Se añadieron Fichas Contract v2 reales y el descriptor ahora las referencia mediante `ficha_path`.

### Fichas actuales
- `Agente Yaiwes principal/execution-orchestration/deterministic-execution/ficha.serial_dispatch.v2.json` blob `bc885059ed0a97f73aad02572853d1b0a4f8117d`.
- `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/ficha.run_control.v2.json` blob `7fdb64b7a21fe51c278dcc907b09eb800f2a2770`.
- `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/ficha.resume_identity.v2.json` blob `4ce82a32faa939177dd22603f097402e9b9e6ed9`.
- `Agente Yaiwes principal/control-governance/ficha.strategy_delta.v2.json` blob `44aeb5cb48db6d42499bc940e47e912942d7fd40`.
- provenance schema blob `5c3aa0b42fb9737baeb1f151a933fa83cc72c27d`.
- provenance registry blob `5274c96b79a4862d4081be18b80c1c0b09d9607a`.

Commits del delta: `a939ac70a2cd7bca4ba561541e81e7a37f687e45`, `44ff595c2a861259628e54541af686f714aaeaf9`, `2380fe36ecd861a04df03cade54917ae15c9bc64`, `47c3410f6ab85e2fe4059421b719726a901edfc8`, `913c0cc63b6216f222a63dd3520b739b0f438601`, `20bd9d6b56db48be85c072b0b42b2efe1924aabc`.

## Verificación
- Read-back GitHub: PASS para 4/4 Fichas y blobs anteriores.
- Check determinista local de invariantes visibles del validador v2: 4/4 sin errores para ID/semver/estado/transform IO/kind/runtime/LLM ratio/timeouts/categoría/etapa/repetición.
- Ejecución del archivo canónico exacto: **NO COMPLETADA** en esta corrida; el raw histórico no pudo materializarse en el runtime local por fallo de resolución de red. No se sustituye ese check por una afirmación de PASS.

## 6 causas/cuestionamientos del GAP
1. ¿Se confundió provenance con contrato ejecutable? Sí; corregido mediante separación.
2. ¿Existía patrón Ficha v2 real? Sí; AWS + `ficha_contract_v2.py`.
3. ¿Debe T15 tener Ficha propia? No hay módulo independiente: T15 fue patch/test de T10–T14.
4. ¿Los destinos siguen en los blobs verificados? Sí, read-back T10–T14.
5. ¿Se ejecutó el validador canónico exacto? No; bloqueo explícito.
6. ¿Puede cerrarse T16 sin ese verify_final? No, por FAIL_CLOSED_LOOP.

Evidence hash del delta material: `75e2ec13ccfac3d24344a30ba4cfeb438164b2d24ea737bdf46fd97e0bf9b5a6`.

## Resultado
T16 permanece `EN_CURSO`; T17 permanece bloqueado. Siguiente delta: ejecutar la fuente canónica exacta del validador contra las 4 Fichas, registrar stdout/veredicto y, solo si 4/4 PASS + cross-check de paths, cerrar T16 y avanzar T17.