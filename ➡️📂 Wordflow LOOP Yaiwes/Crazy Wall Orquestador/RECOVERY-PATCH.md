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
- Checkpoint: `WFLOOP-CODE-GRAPH-20260911-0008`.
- Nodo de reentrada: `CG06_NEW_CODE_POLICY_G006`.
- GAP ledger: `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`.
- Evidencia G-001: `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`.
- Evidencia G-002: `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`.
- Evidencia G-003: `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.
- Evidencia G-004: `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.
- Evidencia G-005: `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`.
- Cerrados verificados: `G-001`, `G-002`, `G-003`, `G-004`, `G-005`, `G-010`, `G-020`.

## G-005 RECUPERABLE
`runtime/src/core/reuse_selector.py` blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`; tests `runtime/tests/test_reuse_selector.py` blob `1bcd0fca22d1238d28add1880e882e7af863ad52`; catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`. Política `REUSE > PATCH > ADAPT > GENERATE`; máximo 10 candidatos; source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios. External candidate => `ADAPT`; riesgo alto o compatibilidad nula => `RESEARCH_MORE`; sin match tras investigación => `GENERATE`. Para `dag`, DAGEngine local es REUSE. Graphiti/Graphology siguen NO integrados.

## DRIFT DETECTADO Y CORREGIDO MANUALMENTE
Durante ciclo G-005 se detectó que PLAN y RECOVERY seguían en checkpoint `0005` mientras las fuentes principales ya estaban en `0007`. Se actualizaron manualmente a `0008`. G-013 permanece abierto porque todavía falta reconciliador automático + test de drift/conflict; la corrección manual no equivale a cerrar G-013.

## RECONSTRUCCIÓN OBLIGATORIA
Al recuperar: releer README arquitectura → STATE → CHECKPOINT → BITÁCORA → GAP ledger → HANDOFF → PLAN → este RECOVERY. Si existe contradicción, abrir/reabrir G-013 y no elegir silenciosamente una fuente.

## ORDEN DE CONTINUACIÓN
1. Ejecutar G-006 1×1: política/contrato de generación de código nuevo; solo tras resultado `GENERATE` del selector G-005.
2. Después G-007/G-008/G-009 para code existente, seguridad y `NO_VALUE_GAP`.
3. Reutilizar antes de crear; `REUSE > PATCH > ADAPT > GENERATE`.
4. Para descargar/extraer/copiar/mover: motores canónicos inmutables, destino explícito, hash/read-back, no LFS, no force.
5. Graphiti/Graphology no están integrados todavía; requieren evidencia de copia/adaptador/test/read-back.
6. No crear bus paralelo: módulos nuevos solo mediante Fables/Ficha.
7. LLM no controla gates deterministas ni deployment.
8. G-022 permanece abierto hasta aislamiento enforceable; G-017 hasta checks reales de deployment/health.

## FAIL-CLOSED
Sin evidencia reproducible, el estado es GAP/INCONCLUSIVE, nunca PASS.
