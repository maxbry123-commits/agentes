# BITÁCORA CRAZY WALL — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · `FAIL_CLOSED_EXECUTION_LOOP`.
Raíz única autorizada: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

## HISTÓRICO CONSERVADO
Migración de alcance principal `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`. Cierre local previo: `LOCAL_TESTS_PASS_AUTH_PROVIDER_TEST_PENDING`; evidence `FINAL_3STEP_CLOSURE_TEST_2026-09-10.json`, commit `6c4b10a49fa8de3bd85348f15bd5f5fa461d128c`. Sobrevive `AUTH_PROVIDER_TEST_PENDING`; no se convierte ausencia de ejecución autenticada en PASS.

# NUEVO GRUPO ACTIVO — CODE GRAPH / PROGRAMACIÓN — 2026-09-10

## CG-0001 — INPUT autorizado
Se abre fase para `archivo/componente → auditoría → arquitectura → tareas → DAG → code → sandbox → reviewer → deployment → evidencia`, con grafo de trabajo, memorias de agentes, cola dependiente/paralela, motores de adquisición y supervisión horaria. Escritura prohibida fuera de `➡️📂 Wordflow LOOP Yaiwes/`.

## CG-0002 — Inventario inicial
Confirmados dentro del LOOP: README arquitectura, HANDOFF, GUIA MAESTRA, PLAN programación, `runtime/`, `wordflow_loop/`, índice de agentes y Crazy Wall con STATE/CHECKPOINT/PLAN/RECOVERY/evidencia. STATE fue abierto en nodo `CG00_REQUIREMENTS_AND_GAP_LEDGER_OPEN` sin borrar el cierre previo.

## CG-0003 — Componentes de grafo localizados
Fuente solo lectura: `maxbry123-commits/osquestador-auditor`.
- `graphiti/`: framework de temporal/context graphs para agentes; entities/facts/episodes/provenance, actualización incremental, hybrid retrieval, tipos Pydantic, MCP y REST/FastAPI. Candidato a contexto/provenance/memoria temporal; no scheduler DAG.
- `graphology/`: Graph object JS/TS; grafos directed/undirected/mixed, algoritmos/layouts/traversals/eventos; backend usado por Sigma.js. Candidato a mapa/visualización; no durable runtime.

## CG-0004 — Skill canónico de motores leído
Origen corroborado: `maxbry123-commits/frontend/main/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`. Motores inmutables, blobs preservados, destino explícito, no LFS/force, read-back obligatorio.

## CG-0005 — GAP ledger publicado
30 GAPs con criterio de cierre reproducible.

## CG-0006 — Documentos del Director incorporados
Mavis/Max System quedan como fuente de patrones; cualquier afirmación de aceleración queda hipótesis hasta benchmark.

# CICLO CG-CYCLE-0002 — SUPERVISIÓN + RECONCILIACIÓN

## CG-0007 — Drift detectado
README/STATE estaban en fase CODE GRAPH mientras CHECKPOINT/HANDOFF/PLAN/RECOVERY seguían en cierre anterior.

## CG-0008 — G-010 CLOSED_VERIFIED
Watchdog CODE GRAPH activo y limitado a la raíz autorizada.

## CG-0009 — G-020 CLOSED_VERIFIED
`wordflow_loop/research/community_sources.json` contiene 12 fuentes; blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## CG-0010 — Reconciliación persistida
STATE/CHECKPOINT/HANDOFF/PLAN/RECOVERY alineados con fase activa. Evidence `CODE_GRAPH_CYCLE_0002_2026-09-10.json`.

# CG01_REUSE_AUDIT — HALLAZGOS

## CG-0011 — Chat A↔B
Localizados tres contratos Chat-B en `runtime/docs/`: T001, T007, T011. Definen ejecución determinista, REUSE>PATCH>ADAPT>GENERATE, sandbox, evidence, Tribunal y traceability. No se localizó artefacto Chat-A en el árbol runtime auditado; G-016 permanece `GAP_IN_RESEARCH` hasta búsqueda completa o NOT_FOUND probado.

## CG-0012 — Sandbox no demostrado
`runtime/src/uek/sandbox_manager.py` blob `e26d955331d5a9df8c7408377bab9924d308abef` retorna un descriptor con status `READY`, policy/memory y un ID; no crea aislamiento de process/filesystem/network/time/memory y `release_sandbox()` retorna `True`. G-022 permanece abierto; `READY` no es evidencia de aislamiento.

## CG-0013 — Deployment/installation con PASS estático
`runtime/src/install/installation_engine.py` blob `af525da2cf3409a30fe2633c934d8ccb45cbda50` avanza su FSM pero emite `valid=true`, `invariants_passed=36`, `health_check=PASS` y hash fijo sin ejecutar checks reales. G-017 permanece abierto y esos PASS no se aceptan como evidencia.

## CG-0014 — Motores y memorias
No se localizaron motores canónicos en top-level del LOOP/wordflow_loop auditado ni archivos exactos `agente-readme-memoria`; G-011 y G-014 permanecen abiertos hasta read-back exacto.

## CG-0015 — Evidence + checkpoint
Evidence `wordflow_loop/evidence/CG01_REUSE_AUDIT_2026-09-10.json`. Checkpoint `WFLOOP-CODE-GRAPH-20260910-0003`. Próximo nodo: localizar Fables/Ficha y completar source map.

# CICLO CG-CYCLE-0004 — G-003 TASK GRAPH

## CG-0016 — Reutilización del DAG existente
Auditado `runtime/src/core/dag_engine.py` blob `ed4361e9e2ca93e6744f9946d2334bf55b3ef63a`: usa `graphlib.TopologicalSorter`, valida dependencias, detecta ciclos y genera batches deterministas. Decisión: REUSE; prohibido introducir otro orquestador para G-003.

## CG-0017 — Implementación G-003
Creado `runtime/src/core/code_task_graph.py`, blob `91fd7779b2e8c27e3dd7f282847df1e2e4ab4f62`. Normaliza tareas con task_id/source/capability/owner/dependencies/priority/destination/sandbox/tests/evidence/idempotency/retry/status y mantiene `director_tasks` y `generated_tasks` separados.

## CG-0018 — Tests + fail-closed
Creado `runtime/tests/test_code_task_graph.py`, blob `882eb17b4289c747adf3850407e8a6a13b80ae65`. Cubre separación Director/generadas, orden topológico, dependencia inexistente fail-closed y ciclo fail-closed. Microtest equivalente ejecutado: `PASS_5_OF_5_ASSERTIONS`. No se reclama GitHub Actions ni runtime externo.

## CG-0019 — Evidence + cierre
Evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`. `G-003 CLOSED_VERIFIED_LOCAL`. Checkpoint `WFLOOP-CODE-GRAPH-20260910-0004`. Próximo nodo 1×1: `G-004` clasificador determinista de ubicación arquitectónica.

# CICLO CG-CYCLE-0005 — G-004 PLACEMENT

## CG-0020 — Matriz determinista A–G
Creado `runtime/src/core/placement_classifier.py`, blob `69698ad30ba1903e0780efcea1952a3737aeb23e`. Usa señales explícitas de privilegio, lifecycle, tipo de ejecución, estado, latencia, invariantes kernel, razonamiento, cadena de agente, fan-out, tool reuse, I/O y justificación de otras capas. No usa nombre de archivo ni LLM.

## CG-0021 — Fail-closed de ambigüedad
Se implementó `PLACEMENT_REVIEW_REQUIRED` cuando faltan señales suficientes, existe empate/conflicto o una ubicación G no trae `other_location + other_justification`.

## CG-0022 — Tests y evidencia
Tests: `runtime/tests/test_placement_classifier.py`, blob `bf1c26f49edf668ee05584b2a357324af0fc4d8d`. Simulación local equivalente: `PASS_10_OF_10_ASSERTIONS`, cubriendo A/B/C/D/E/F/G, conflicto, señal débil y G sin justificación. Evidence: `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`. No se reclama GitHub Actions ni runtime externo.

## CG-0023 — Cierre y siguiente nodo
`G-004 CLOSED_VERIFIED_LOCAL`. Checkpoint `WFLOOP-CODE-GRAPH-20260910-0005`. Siguiente nodo 1×1: `G-001` raíz anclada/contrato/serialización CODE GRAPH. `AUTH_PROVIDER_TEST_PENDING` continúa abierto.

## Estado del grupo
30 GAPs · 4 CLOSED (`G-003`, `G-004`, `G-010`, `G-020`) · externos `AUTH_PROVIDER_TEST_PENDING` · Graphiti/Graphology todavía NO integrados · Fables G-018 sigue en investigación y no se crea bus paralelo.
