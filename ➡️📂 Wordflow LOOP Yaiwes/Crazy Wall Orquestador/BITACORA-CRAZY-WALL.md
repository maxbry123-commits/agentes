# BITÁCORA CRAZY WALL — Wordflow LOOP Yaiwes

Esta bitácora registra progreso humano-legible; `STATE.json` registra estado estructurado. README, STATE, CHECKPOINT y RECOVERY-PATCH son anclas mutuas; si divergen, el estado efectivo es GAP.

## EVENTO CW-0001 — PLAN MASTER
- Nodo: `PLAN_MASTER`.
- Estado histórico: `PLANNING`.
- Fuente: instrucciones literales del Director registradas en README.
- Partes: Parte 1 PENDING; Parte 2 READY; Parte 3 PENDING_IMPLEMENTATION; Parte 4 PENDING_IMPLEMENTATION.
- Regla de cierre: sin `evidence_hash` verificable = GAP.

## EVENTO CW-0002 — CORRECCIÓN DE CUMPLIMIENTO DE INSTRUCCIONES
- Se registró como norma la cadena literal del Director: goals 12/12 → leer INPUT BLOCK literal sin interpretar → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones → analiza/LOOP → auditor instrucciones 3x → auditor salida 12 → 3 refutaciones → verificación global → checklist/salida.
- Se registró como FAIL histórico haber ejecutado más de lo pedido cuando el INPUT solo pedía confirmar comprensión.
- Regla nueva: ningún nodo puede ejecutar si la auditoría literal previa no confirma autorización explícita.

## EVENTO CW-0003 — ACTIVACIÓN DEL LOOP DE CONSTRUCCIÓN
- Orden activa del Director: `Inicia`.
- Estado: `LOOP_ACTIVE`.
- Nodo actual: `PLAN_AND_SOURCE_RECONCILIATION`.
- Checkpoint activo: `WFLOOP-BUILD-0001`.
- Recovery activo: `RECOVERY-PATCH.md` con protocolo de lectura 3 pasadas.
- Cada iteración debe releer: (1) INPUT BLOCK literal del README; (2) STATE+CHECKPOINT+Crazy Wall; (3) documentos fuente cableados al nodo.
- Toda mutación requiere checkpoint pre-mutation, SHA previo, destino, evidencia esperada y rollback por SHA/commit.
- Si falla: GAP → 20 alternativas distintas → seleccionar delta distinto → reintentar → no avanzar hasta PASS.

## DOCUMENTOS CABLEADOS AL PLAN
1. README canónico → instrucciones literales, Partes 1–4, gates, destinos y cadena LOOP.
2. `📌✅😀Arquitectura para hacer el código Wordflow.md` → arquitectura/clasificación/destinos/gaps de programación.
3. `PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md` → Chat A/B, 10 auditorías, MissionContract, Council 12, DAG, ROOT_MAP, task contracts, EvidencePacket.
4. `UOOS_v2 ... PARTE 1 ... AUTORUN-1.md` → B1–B8, leyes L01–L15, nodos/loops/Tribunal/Recovery.
5. `UOOS_PARTE2_v3 ... RUNTIME.md` → E01–E12, RT00–RT45, RT80, RT90, resume/idempotencia/Tribunal.
6. `DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md` → config, dry-run, plan, secret-block, semver, push, verificar, evidence.json, 0% LLM.
7. `GUIA_MAESTRA_PIPELINE_NCT_v2.html` → auditoría viva, fases, fuentes, 3+3 pasadas, mapeo UOOS.
8. `INSTRUCCIONES_GROK_OPCION_A.md` → ProgrammingInstance, InstancePool, classifier, registry, metering, watchdog/fallback.
9. Enchufe Universal parte 1 → plugin bus/registry/adapter/mount; ejecución dinámica queda bloqueada hasta seguridad.
10. Ficha parte 2 + contrato universal JSON → I/O, invariantes, permisos, sandbox, versionado, ledger, recovery.
11. Prompt extracción documento→Ficha → requisito documental→ID/ficha/tarea trazable.
12. Skill GitHub Acción → DO_NOT_REWRITE_CODE / COPY_THEN_SURGICAL_EDIT / locks SHA / extracción/provenance/read-back.

## SIGUIENTE EVENTO PERMITIDO
Tras tres pasadas de reconciliación de README/STATE/checkpoint/fuentes, ejecutar únicamente el siguiente nodo pendiente de la cola 1×1 y registrar evidencia real. No cerrar por presencia de archivos.
