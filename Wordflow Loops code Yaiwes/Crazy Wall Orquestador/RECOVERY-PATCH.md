# RECOVERY PATCH — Wordflow LOOP Yaiwes

Contrato `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.

## RAÍZ ÚNICA
Toda recuperación y modificación parte exclusivamente de `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## HISTÓRICO QUE NO SE REEJECUTA
El cierre local anterior permanece verificado: fleet 18, Council12=12, fail-closed local, router prioridad/failover y persistencia. Evidence: `wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json`, commit `6c4b10a49fa8de3bd85348f15bd5f5fa461d128c`.

No declarar PASS_REAL externo: `AUTH_PROVIDER_TEST_PENDING` permanece hasta ejecución autenticada real.

# ESTADO ACTIVO DE RECOVERY
- Fase: `CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP`.
- Estado: `ACTIVE_LOOP_CODE_GRAPH_RESEARCH`.
- Checkpoint canónico: `WFLOOP-CODE-GRAPH-20260911-0019`.
- Nodo de reentrada de SOL_1: `G013_SOURCE_TRUTH_RECONCILIATION`.
- GAP ledger: `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`.
- Evidencia G-001: `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`.
- Evidencia G-002: `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`.
- Evidencia G-003: `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.
- Evidencia G-004: `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.
- Evidencia G-005: `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`.
- Evidencia G-013: `wordflow_loop/evidence/G013_CANONICAL_RECONCILIATION_2026-09-11.json`.
- `G-013` está reclamado por `SOL_1` y no se cierra hasta 8/8 fuentes en `0019` + reconciliador/tests + read-back.
- `G-018` está reclamado por `SOL_2`; SOL_1 no lo toca.

## G-005 RECUPERABLE
`runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`; tests `runtime/tests/test_reuse_selector.py` blob `1bcd0fca22d1238d28add1880e882e7af863ad52`; catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`. Política `REUSE > PATCH > ADAPT > GENERATE`; máximo 10 candidatos; source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios. External candidate => `ADAPT`; riesgo alto o compatibilidad nula => `RESEARCH_MORE`; sin match tras investigación => `GENERATE`. Para `dag`, DAGEngine local es REUSE. Graphiti/Graphology siguen NO integrados salvo evidencia posterior explícita en su nodo.

## G-006 BLOQUEADO
La política de generación existe, pero `G-006` queda `BLOCKED_DEPENDENCY_G018` hasta que Fables/Ficha tenga source proof + registro/ABI + test verificables. No crear bus paralelo.

## G-013 EN RECONCILIACIÓN
Contrato `yaiwes.truth_reconciliation/v1` en `runtime/src/core/source_truth_reconciler.py`. STATE y CHECKPOINT son anchors. El parser histórico acepta un único marcador explícito `Checkpoint canónico:` y rechaza marcadores canónicos contradictorios. El objetivo actual es alinear README/STATE/CHECKPOINT/BITÁCORA/GAPS/HANDOFF/PLAN/RECOVERY al checkpoint `0019`, ejecutar el reconciliador exacto y cerrar solo tras read-back consistente.

## RECONSTRUCCIÓN OBLIGATORIA
Al recuperar: releer README arquitectura → STATE → CHECKPOINT → BITÁCORA → GAP ledger → HANDOFF → PLAN → este RECOVERY. Si existe contradicción, mantener G-013 abierto y no elegir silenciosamente una fuente.

## ORDEN DE CONTINUACIÓN
1. Terminar G-013 1×1: reconciliar las 8 fuentes al checkpoint `0019`, ejecutar reconciliador/tests, persistir evidencia y read-back.
2. No tocar G-018 mientras esté reclamado por SOL_2.
3. Tras cerrar G-013, releer `TASK-NODES.json`; G-019 solo será elegible si sigue PENDING/libre y su dependencia G-013 está PASS.
4. Reutilizar antes de crear; `REUSE > PATCH > ADAPT > GENERATE`.
5. Para descargar/extraer/copiar/mover: motores canónicos inmutables, destino explícito, hash/read-back, no LFS, no force.
6. No crear bus paralelo: módulos nuevos solo mediante Fables/Ficha.
7. LLM no controla gates deterministas ni deployment.
8. G-022 permanece bloqueado hasta aislamiento enforceable; G-017 depende de ese gate.

## FAIL-CLOSED
Sin evidencia reproducible, el estado es GAP/INCONCLUSIVE, nunca PASS.