# RECOVERY PATCH — Wordflow LOOP Yaiwes

## Anclas canónicas
- README: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- ANEXO PLAN: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`

## Norma de reanudación — 3 pasadas antes de ejecutar
1. Pasada 1: leer INPUT BLOCK activo en README literal 1:1; extraer solo acciones autorizadas, prohibiciones, formato y destino; no reinterpretar.
2. Pasada 2: leer STATE + CHECKPOINT + Crazy Wall + ANEXO; reconciliar nodo, pendientes, SHAs, evidencia y recovery. Divergencia = GAP.
3. Pasada 3: releer documentos fuente del nodo listados en CHECKPOINT; cruzar documento↔plan↔código; ausencia de soporte = GAP.

Cadena obligatoria: `goals 12/12 → INPUT literal → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 → 3 refutaciones → verificación global → checklist/salida`.

## Recuperación detallada por fuente
- README: recuperar INPUT BLOCKS literales, Partes 1–4, autorización, prohibiciones, formato `➡️📂 Capa N` + microflujo, destinos, gates, cadena LOOP, política no reinterpretar.
- Arquitectura Wordflow: recuperar clasificación WORKFLOW/CORE/KERNEL/RAZONAMIENTO/CONTROL/MEMORIA/EJECUCIÓN/TEST/PERSISTENCIA/OPTIMIZACIÓN, destino estructural, programación modular, contratos, trazabilidad y gaps.
- Chat A/B: recuperar 10 auditorías, INPUT+Sentinel, MissionContract+GoalLock, Council12, Analysis/Architecture/DAG/ROOT_MAP/Dependencies, REUSE>PATCH>ADAPT>GENERATE, límites LOC, task contract, EvidencePacket.
- UOOS1: recuperar B1-B8, L01-L15, DSL, DAG, loops, Tribunal, state events, checkpoint, rollback, evidence, anti-scope-creep y reproducibilidad.
- UOOS2: recuperar E01-E12, RT00-04, RT10-45, RT80, RT90, idempotencia, capabilities, memoria mínima, input validation, Tribunal, auditoría y resume.
- Deploy: recuperar 0% LLM, deploy_config, dry-run, plan.json, SIN_REGLA=FAIL, secret gate, copia idempotente, semver, CHANGELOG, push, verificación remota, evidence.json.
- Pipeline NCT: recuperar fases/fuentes, auditoría viva, 3+3 pasadas, cross-check, mapeo UOOS y separación diseño/ejecución/despliegue.
- Programming Pool: recuperar ProgrammingInstance, InstancePool, classifier, registry, metering, idempotency, watchdog, fallback, queue y schemas.
- Plugin/Ficha/Contrato: recuperar registry, adapter, mount, shadow/hotswap, I/O, invariantes, permisos, sandbox, dependencies, versionado, health, fallback, recovery, governance y `ejecucion.kind`; bloquear ejecución dinámica no validada.
- Extracción→Ficha: recuperar requisito→ID/origen/objetivo/dependencia/destino/contrato/tarea/evidence.
- Skill GitHub Action: recuperar DO_NOT_REWRITE_CODE, COPY_THEN_SURGICAL_EDIT, SHA locks, provenance, descarga/extracción, read-back.

## Recuperación por capa
0 Gobierno: restaurar INPUT/mission/trace/goals/state antes de todo.
1 Investigación: restaurar consulta, fuentes, dedup/ranking y URLs/SHA.
2 X-Ray documental: restaurar documento, requisitos, Council12, gaps e IDs.
3 X-Ray código: restaurar objetivo, rutas buscadas y evidencia de existente/parcial/ausente.
4 Copia/move: restaurar SHA fuente/destino y blob previo.
5 GitHub Action: restaurar repo/ref/lock/manifiesto/provenance.
6 Evolución: restaurar gap/capacidad/propuesta/autorización/sandbox.
7 Clasificador: restaurar tipo y ruta destino antes de programar.
8 Catálogo105: restaurar algoritmo/fuente/licencia/tests/Ficha kind:code.
9 Arquitecto A: restaurar MissionContract/GoalLock/DAG/ROOT_MAP/task contract.
10 Ejecutor B: restaurar nodo único, sandbox, delta, tests/EvidencePacket.
11 Espejo agentes: restaurar primario/intentos/causa fallo/contrato idéntico.
12 Enchufe/Ficha: restaurar ficha/adapter/registry/mount/health/evidence.
13 Scheduler: restaurar DAG/cola/locks/idempotencia/deadline.
14 Persistencia LOOP: restaurar último checkpoint y estrategia fallida; siguiente retry usa delta distinto.
15 Heartbeat: restaurar snapshot/deadline/watchdog/memoria validada.
16 Tribunal: restaurar maker output, checker results, score y evidencia.
17 UOOS1: restaurar B1-B8 coherentes.
18 UOOS2: restaurar último RT/checkpoint; no reiniciar DONE.
19 Deploy: restaurar plan/dry-run/commit previo; rollback por Git.
20 HF compute: restaurar inventario/conector/health/resources; no afirmar conexión sin prueba.
21 Storage: restaurar backend/schema/adapter/consistencia/checkpoint.
22 Multi-API: restaurar secret_ref/router/health/fallback/metering; nunca valor secreto.
23 E2E: restaurar caso de prueba, etapa fallida y evidence chain.
24 Archivo: restaurar commit/hash final y puntero histórico.

## Contrato de recuperación por nodo
1 registrar node_id/mission_id/trace_id/INPUT/source_refs/destino/SHA previo/evidence esperado; 2 checkpoint pre-mutation; 3 una tarea; 4 verificar/refutar; 5 FAIL conserva evidencia y genera exactamente 20 alternativas distintas; 6 rank REUSE>COPY/MOVE>PATCH>ADAPTER>GENERATE; 7 aplicar delta nuevo autorizado; 8 retest; 9 rollback por SHA/commit, nunca memoria; 10 actualizar STATE/CHECKPOINT/Crazy Wall; 11 DONE solo con evidence_hash+prueba+trazabilidad; 12 secretos solo secret_ref.

## Ledger literal
Ancla histórica: commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc`, blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`. Si falta un INPUT, restaurarlo literalmente desde Git y anexar posteriores sin resumir.

## Fail-closed
Divergencia entre README/ANEXO/STATE/CHECKPOINT/Recovery/Crazy Wall, fuente ausente, instrucción reinterpretada o evidencia inexistente => `GAP`; volver al LOOP, no avanzar.