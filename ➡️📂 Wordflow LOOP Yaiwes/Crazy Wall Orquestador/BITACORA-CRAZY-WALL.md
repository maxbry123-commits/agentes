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

## EVENTO CW-0004 — PLAN DETALLADO CABLEADO Y VALIDADO
- Anexo operativo creado: `ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`.
- Checkpoint actualizado y contiene 13 fuentes con qué extraer de cada una, 25 capas/nodos, anclas, pre-mutation fields y siguiente nodo permitido.
- Recovery actualizado con reanudación 3 pasadas, recuperación por cada fuente y por cada capa 0–24, rollback por SHA/commit y prohibición de reconstruir de memoria.
- STATE actualizado a `PLAN_PRESENTATION_READY`.
- Validación registrada: 12 goals entrada, 12 salida, Ask Consil 12/12, auditor de instrucciones 3 pasadas, 4 verificaciones del plan, 3 refutaciones y verificación cruzada global documental.
- Resultado: `PASS_PLAN_DOCUMENTAL`; NO significa implementación física de Parte 1/3/4 ni `VERIFIED_CLOSED`.
- Política de plugins: únicamente GitHub y Hugging Face están autorizados externamente; cualquier otro plugin requiere autorización explícita.
- LOOP horario solicitado: no está activo.

## EVENTO CW-0005 — VALIDACIÓN REAL DE INVENTARIO DE FUENTES
- Pasada 1: README actual leído nuevamente; INPUT BLOCK 017 conserva la norma literal de no reinterpretación y cadena obligatoria.
- Pasada 2: STATE + CHECKPOINT + RECOVERY + Crazy Wall + ANEXO reconciliados; todos apuntan a las mismas anclas y al nodo `PLAN_LAYERED_ARCHITECTURE`.
- Pasada 3: inventario real de `📂Archivo download 2` leído desde GitHub `main`; se verificaron allí los documentos principales y los archivos de programación/Enchufe/Ficha/contrato/prompt de extracción usados por el plan.
- Fuente adicional `skills/skills Github acción` verificada en el commit `c789e5fe635e220230ffc759d86dc3bbb8e261d4`; existen `SKILL.md`, `README.md`, `ADVERTENCIA-CODE.json`, assets/references/scripts y carpetas de copiar/mover/descargar-extracción.
- Evidencia de SHAs del intake: Arquitectura Wordflow `a08dc64b902465cb1549ed3607cbfe1d737e5d1f`; Chat A/B `a9606ed0154ad5e7a72b6ffbe43d225e2ea448a3`; UOOS1 `0874a14dcad274d4dbf058721b60af5da3d79fe8`; UOOS2 `bf8cf9c24b899cc67dd56a449ee7999ab8f4c0a8`; Deploy `3a0e39b61b30ce244aadc3337e1446afff61917b`; Pipeline NCT `f40b0a4634733891efdb430958dae9ca59ff2427`; Programming Pool doc `c0a97179e55b042ca6356daf3f5b6fae738fbae7`; PluginBus `c017bb2c1a09c8bb738e1774d656d59340ab56d5`; Ficha `a72508027cc2458553ef6a2255a9aa33d9a77a21`; contrato universal `aa023a5c5124eb574bcaa63d0b69607f1d18590c`; extracción→Ficha `c49b693dfad9e8331a4f84fa069c38a61ec2ad60`.
- Checkpoint histórico en ese momento: `WFLOOP-BUILD-0003`; source_refs principales fijados con SHA/ref.
- Resultado de la validación del PLAN: `PASS_PLAN_DOCUMENTAL`.
- GAPs que permanecían explícitos: implementación física Parte 1/3/4, agentes programadores definitivos, compute HF real, almacenamiento, bindings de modelos y E2E final.

## EVENTO CW-0006 — AUDITORÍA FORENSE X-RAY 5 PASADAS + RESTAURACIÓN LITERAL
- Orden del Director: auditar plan/chat/documentos en 5 pasadas, refutar cada pasada y editar solo faltantes sin reescribir fuentes.
- Se creó `AUDITORIA-XRAY-PLAN-5-PASADAS.md` con 5 pasadas y 5 refutaciones.
- PASADA 1 encontró que README main no contenía físicamente INPUT 010–013; se restauraron literalmente desde blob histórico `474af741abe3ac9c816f4406f0fc6e4e4490c2aa` sin reinterpretación.
- PASADA 2 detectó diferencia documental 10/10 goals vs instrucción Director 12/12; se registró precedencia Director 12/12 sin alterar la fuente.
- PASADA 3 detectó ambigüedad DSL y límites; quedó fijado: DSL = YAML/JSON/schema existente, sin sintaxis nueva; 200 líneas/archivo, 500 LOC/bloque, 2000 LOC/task; cola actual 1×1.
- PASADA 4 confirmó deploy 0% LLM y añadió fail-closed: solo GitHub/Hugging Face autorizados, ejecución dinámica de candidato bloqueada hasta static-AST+sandbox+security PASS, usage metering requiere ledger persistente, deploy sin `evidence.json` no es PASS.
- PASADA 5 reconcilió README + CHECKPOINT + RECOVERY + STATE + Crazy Wall + HANDOFF.
- README de esa pasada: blob `fed000b54a80fd6dd9b7cea21097043e289d73f6`, commit `3d49c55e5d3af050a979ac4de65283587089ad17`.
- Checkpoint de esa pasada: `WFLOOP-XRAY-0004`.
- Resultado histórico de esa pasada: `PASS_WITH_LITERAL_GAPS`.

## EVENTO CW-0007 — CORRECCIÓN 1:1 + CIERRE DE GAP OPERATIVO DE INSTRUCCIONES
- Orden actual del Director: corregir la contradicción entre “anotado 1:1” y el posterior `GAP_LITERAL_SOURCE`.
- Se creó `LEDGER-CANONICO-PARTES-1-4.md`, fijando la autoridad exacta de cada Parte por INPUT/commit.
- Parte 1: INPUT 013 literal, commit `2d1c718...`, blob `474af741...`.
- Parte 2: INPUT 014 literal + mapping `26760e4...` + integración reuse `4b1c705...`.
- Parte 3: registro aprobado inmutable `6b59f4a1514ba419cbeade7c948e68b65d02fe5d`; su diff contiene exactamente el contrato de 12 puntos conservado en README. Estado operativo: `APPROVED_CANONICAL_RECORD`.
- Parte 4: mapa funcional aprobado + INPUT 015 literal; commit `a4fcb2c9d1286f7a8f9695ff2e54805744e8f7d9` registra literalmente aprobación y plan. Estado: `LITERAL_APPROVAL_VERIFIED + APPROVED_CANONICAL_MAP`.
- README corregido: commit `85e04e5ae3875be209a377ff913e7399de029fea`, blob `1a38ec24570e7298e36b6ad20ee6caa5578f2239`; incluye INPUT BLOCK 018 literal y resolución de evidencia.
- Se restauraron las 3 rutas obligatorias antes 404 de `AGENTS.md`: `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md` (`8024e576...`), `PIPELINE/FORENSIC_CODE_AUDIT.md` (`2072d535...`) y `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md` (`7bc798ad...`); read-back 3/3 PASS.
- STATE actualizado a `INSTRUCTION_RECORD_PARTS_1_4_RECONCILED`.
- CHECKPOINT actualizado a `WFLOOP-INSTRUCTION-0005`.
- RECOVERY actualizado para usar literal cuando existe y approved canonical record cuando ese registro aprobado es la evidencia Git disponible.
- Resultado documental de instrucciones/aprobaciones Parte 1–4: `PASS_CANONICAL_EVIDENCE`.
- Regla de verdad: esto NO convierte implementación física, HF compute, storage, bindings, E2E o deploy en `VERIFIED_CLOSED`.

## EVENTO CW-0008 — TAREA 1 / SALIDA 1 — MAPA 25 CAPAS PRESENTADO
- Orden: `Ok inicia tarea 1`.
- Se releen HANDOFF, AGENTS.md, método/forense/estándar PIPELINE, Arquitectura YAIWES, README Wordflow, ledger Partes 1–4, STATE/CHECKPOINT/Recovery/Crazy Wall y fuentes principales de Arquitectura Wordflow, Chat A/B, UOOS1, UOOS2 y Deploy v2.
- Se detecta una discrepancia de numeración: el README canónico usa 25 capas `0–24` con Capa 1 = Intake/GoalLock, mientras `ANEXO-01` conserva una numeración histórica desplazada. Para Tarea 1, el README queda fijado como única autoridad de IDs de capa; el anexo no gobierna numeración.
- Se crea `TAREA-1-SALIDA-1-ARQUITECTURA-CAPAS.md`, commit `84e6b661d4f2efe9c35fdc2facc6ec148054a41d`, con las 25 capas canónicas, microflujos, fuentes, 12 goals entrada/salida, auditor instrucciones ×3, 3 refutaciones y cross-check.
- STATE actualizado a `TASK1_PRESENTED_AWAITING_DIRECTOR_APPROVAL`.
- CHECKPOINT actualizado a `WFLOOP-TASK1-0006`.
- No se ejecutó Tarea 2, no se copió/movió código y no se modificó runtime/arquitectura física.
- Veredicto Tarea 1: `PASS_DOCUMENTAL_PRESENTATION_READY / AWAITING_DIRECTOR_APPROVAL`.

## SIGUIENTE EVENTO PERMITIDO
Solo después de aprobación explícita del Director: Tarea 2 — verificación cruzada de 5 pasadas. Sin aprobación, no iniciar Tarea 2 ni construcción física.