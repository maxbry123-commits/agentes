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

## EVENTO CW-0004 — PLAN DETALLADO CABLEADO Y VALIDADO
- Anexo operativo creado: `ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`.
- Checkpoint actualizado a `WFLOOP-BUILD-0002` y contiene 13 fuentes con qué extraer de cada una, 25 capas/nodos, anclas, pre-mutation fields y siguiente nodo permitido.
- Recovery actualizado con reanudación 3 pasadas, recuperación por cada fuente y por cada capa 0–24, rollback por SHA/commit y prohibición de reconstruir de memoria.
- STATE actualizado a `PLAN_PRESENTATION_READY`.
- Validación registrada: 12 goals entrada, 12 salida, Ask Consil 12/12, auditor de instrucciones 3 pasadas, 4 verificaciones del plan, 3 refutaciones y verificación cruzada global documental.
- Resultado: `PASS_PLAN_DOCUMENTAL`; NO significa implementación física de Parte 1/3/4 ni `VERIFIED_CLOSED`.
- Política de plugins: únicamente GitHub y Hugging Face están autorizados externamente; cualquier otro plugin requiere autorización explícita.
- LOOP horario solicitado: no está activo.

## EVENTO CW-0005 — VALIDACIÓN REAL DE INVENTARIO DE FUENTES
- Pasada 1: README actual leído nuevamente; INPUT BLOCK 017 conserva la norma literal de no reinterpretación y cadena obligatoria.
- Pasada 2: STATE + CHECKPOINT `WFLOOP-BUILD-0002` + RECOVERY + Crazy Wall + ANEXO reconciliados; todos apuntan a las mismas anclas y al nodo `PLAN_LAYERED_ARCHITECTURE`.
- Pasada 3: inventario real de `📂Archivo download 2` leído desde GitHub `main`; se verificaron allí los documentos principales y los archivos de programación/Enchufe/Ficha/contrato/prompt de extracción usados por el plan.
- Fuente adicional `skills/skills Github acción` verificada en el commit `c789e5fe635e220230ffc759d86dc3bbb8e261d4`; existen `SKILL.md`, `README.md`, `ADVERTENCIA-CODE.json`, assets/references/scripts y carpetas de copiar/mover/descargar-extracción.
- Evidencia de SHAs del intake: Arquitectura Wordflow `a08dc64b902465cb1549ed3607cbfe1d737e5d1f`; Chat A/B `a9606ed0154ad5e7a72b6ffbe43d225e2ea448a3`; UOOS1 `0874a14dcad274d4dbf058721b60af5da3d79fe8`; UOOS2 `bf8cf9c24b899cc67dd56a449ee7999ab8f4c0a8`; Deploy `3a0e39b61b30ce244aadc3337e1446afff61917b`; Pipeline NCT `f40b0a4634733891efdb430958dae9ca59ff2427`; Programming Pool doc `c0a97179e55b042ca6356daf3f5b6fae738fbae7`; PluginBus `c017bb2c1a09c8bb738e1774d656d59340ab56d5`; Ficha `a72508027cc2458553ef6a2255a9aa33d9a77a21`; contrato universal `aa023a5c5124eb574bcaa63d0b69607f1d18590c`; extracción→Ficha `c49b693dfad9e8331a4f84fa069c38a61ec2ad60`.
- Resultado de la validación del PLAN: `PASS_PLAN_DOCUMENTAL`.
- GAPs que permanecen explícitos y no se ocultaron: implementación física Parte 1/3/4, agentes programadores definitivos, compute HF real, almacenamiento, bindings de modelos y E2E final.

## SIGUIENTE EVENTO PERMITIDO
Presentar al Director el plan por capas con microflujo; tras aprobación, ejecutar únicamente el siguiente nodo pendiente de la cola 1×1 con checkpoint pre-mutation y evidencia real.