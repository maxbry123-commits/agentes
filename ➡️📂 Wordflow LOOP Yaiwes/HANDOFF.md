# HANDOFF — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4`  
Modo: `FAIL_CLOSED_EXECUTION_LOOP`  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`

## Histórico conservado
El cierre local anterior permanece válido: fleet=18, Council12=12, routing/fail-closed local y router MVP fueron probados localmente. Evidencia: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/FINAL_3STEP_CLOSURE_TEST_2026-09-10.json` · commit `6c4b10a49fa8de3bd85348f15bd5f5fa461d128c`.

Estado externo histórico y actual: `AUTH_PROVIDER_TEST_PENDING`. No se afirma PASS_REAL de proveedores/APIs o agentes remotos sin ejecución autenticada real.

# Fase activa — CODE_GRAPH_ARCHITECTURE_PROGRAMMING_LOOP
Estado: `ACTIVE_LOOP_CODE_GRAPH_RESEARCH`  
Checkpoint: `WFLOOP-CODE-GRAPH-20260911-0008`  
Nodo: `CG06_NEW_CODE_POLICY_G006`.

Pipeline objetivo:
`archivo/componente → Ask Council/auditoría → arquitectura → requisitos → director_tasks + generated_tasks → DAG/cola → placement A|B|C|D|E|F|G → REUSE>PATCH>ADAPT>GENERATE → sandbox → reviewer independiente → deployment determinista → evidencia → STATE/CHECKPOINT`.

## GAP status verificado
- `G-001 CLOSED_VERIFIED_LOCAL`: workspace `wordflow_loop/code_graph/`; serialización determinista + SHA-256 + proyección al DAG existente. Evidence `wordflow_loop/evidence/G001_CODE_GRAPH_WORKSPACE_2026-09-10.json`.
- `G-002 CLOSED_VERIFIED_LOCAL`: contrato `yaiwes.file_audit/v1` en `runtime/src/core/file_audit_contract.py`, blob `e6624c0b39421a01d54cf0615920073c5dd1ee0f`; tests `runtime/tests/test_file_audit_contract.py`, blob `d490a7e15205c37a0f476e6e4c0de7f9429f36c6`; evidence `wordflow_loop/evidence/G002_FILE_AUDIT_COUNCIL_2026-09-10.json`; simulación local equivalente `PASS_5_OF_5_ASSERTIONS`. Council es asesor: `executable_action_authorized=false` siempre.
- `G-003 CLOSED_VERIFIED_LOCAL`: task graph determinista; mantiene `director_tasks` y `generated_tasks` separados. Evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.
- `G-004 CLOSED_VERIFIED_LOCAL`: clasificador A–G + `PLACEMENT_REVIEW_REQUIRED`. Evidence `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`.
- `G-005 CLOSED_VERIFIED_LOCAL`: selector `runtime/src/core/reuse_selector.py`, blob `bc7f4805fc7f13e6de0341b84c533d4b7fb6b044`, catálogo `wordflow_loop/research/reuse_catalog_g005.json` blob `2367f7ed8c7e1ece1d724f15f6494d5ff56543f8`, tests blob `1bcd0fca22d1238d28add1880e882e7af863ad52`, evidence `wordflow_loop/evidence/G005_REUSE_SELECTOR_2026-09-11.json`. Política `REUSE > PATCH > ADAPT > GENERATE`, máximo 10 candidatos, source/licencia/mantenimiento/compatibilidad/riesgo/footprint obligatorios, read-back PASS, `repo_pytest_execution=NOT_CLAIMED`. No se instaló/copió código externo.
- `G-010 CLOSED_VERIFIED`: Watchdog CODE GRAPH activo y limitado a la raíz autorizada.
- `G-020 CLOSED_VERIFIED`: 12 fuentes de investigación en `wordflow_loop/research/community_sources.json`.
- En investigación: `G-016`, `G-018`, `G-023`, `G-027`, `G-028`, `G-029`.

## Reutilización clave
`runtime/src/core/dag_engine.py` sigue siendo el DAG topológico determinista y gana como `REUSE` para capability `dag`; NetworkX queda referencia externa, no reemplazo. Graphiti queda `ADAPT` únicamente para contexto temporal/provenance/memoria; Graphology `ADAPT` únicamente para grafo/visualización cuando exista GAP concreto. No se añade scheduler paralelo.

## GAPs críticos abiertos
- `G-006`: siguiente nodo 1×1; creación de code nuevo solo tras resultado `GENERATE` de G-005 y gates deterministas.
- `G-013`: durante este ciclo se detectó drift en PLAN/RECOVERY (checkpoint 0005); documentación reconciliada manualmente a 0008, pero falta reconciliador automático + test.
- `G-018`: Fables requiere source proof exacto; no crear bus paralelo.
- `G-022`: sandbox actual no demuestra aislamiento físico de filesystem/network/time/memory.
- `G-017`: installation/deployment contiene PASS/health estáticos no aceptados como prueba real.
- `G-016`: Chat-B localizado; Chat-A todavía no localizado.
- `G-011/G-014`: motores canónicos y memorias exactas de 18 agentes siguen abiertos hasta read-back.

## Reglas de continuación
1. No escribir fuera de `➡️📂 Wordflow LOOP Yaiwes/`.
2. No cerrar GAP por presencia de archivo.
3. Motores de descargar/extraer/copiar/mover: únicamente canónicos, inmutables, destino explícito, hash/read-back, no LFS, no force.
4. Todo módulo nuevo entra por Enchufe Universal Fables/Ficha; no buses paralelos.
5. LLM solo en análisis/generación/Council; DAG/routing/gates/state/sandbox/hash/deploy permanecen deterministas.
6. Graphiti y Graphology siguen en investigación; no se declara integración hasta copia exacta/adaptador/test/read-back.
7. Próximo nodo 1×1: `G-006` — política y contrato de generación de code nuevo posterior al gate G-005.
