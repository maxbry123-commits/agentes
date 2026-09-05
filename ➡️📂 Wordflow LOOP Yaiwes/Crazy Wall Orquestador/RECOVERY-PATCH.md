# RECOVERY PATCH — Wordflow LOOP Yaiwes

## Anclas canónicas
- README: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`

## Norma de reanudación — 3 pasadas antes de ejecutar
Cada ejecución o reanudación del LOOP debe hacer, en este orden y sin saltos:
1. **Pasada 1 — instrucciones:** leer el INPUT BLOCK activo en el README literal 1:1; identificar únicamente acciones explícitamente autorizadas, prohibiciones, formato y destino.
2. **Pasada 2 — estado:** leer STATE + CHECKPOINT + Crazy Wall; comparar `current_node`, pendientes, último SHA, evidencia y recovery anterior. Si divergen, marcar GAP y reconciliar antes de mutar.
3. **Pasada 3 — fuentes cableadas:** releer los documentos fuente del nodo listados en CHECKPOINT; extraer solo requisitos soportados por cada fuente, comparar documento↔plan↔código y registrar cambios de interpretación como GAP, nunca como hecho.

Después de las 3 pasadas se aplica la cadena obligatoria del Director:
`goals 12/12 → INPUT literal sin interpretar → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 → 3 refutaciones → verificación global → checklist/salida`.

## Cableado de documentos y qué recuperar de cada uno
### README canónico
Recuperar: INPUT BLOCK activo, Partes 1–4, orden literal, destinos, gates, microflujo obligatorio, estado de cada capa y reglas de no reinterpretación.

### `📌✅😀Arquitectura para hacer el código Wordflow.md`
Recuperar: arquitectura de programación; cómo distinguir workflow/core/kernel/razonamiento/control/memoria/ejecución/test/persistencia/optimización; destino estructural; contratos; trazabilidad; criterios para determinar código faltante.

### `PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md`
Recuperar: roles Chat A/Chat B; 10 auditorías; INPUT_BLOCK+Sentinel; MissionContract+GoalLock; Council 12; PROJECT_ANALYSIS; ARCHITECTURE; DAG YAML/JSON; ROOT_MAP; Dependency Map; REUSE>PATCH>ADAPT>GENERATE; tasks ≤2000 LOC; bloques ≤500 LOC; formato de salida y EvidencePacket.

### `UOOS_v2_... PARTE 1 ... AUTORUN-1.md`
Recuperar: B1 Manifest, B2 state, B3 nodos DSL, B4 DAG, B5 loops L01–L11, B6 Tribunal, B7 plan construcción/despliegue, B8 Recovery; leyes L01–L15; state machine por eventos; checkpoint por subgoal; evidencia obligatoria; anti-scope-creep.

### `UOOS_PARTE2_v3_... RUNTIME.md`
Recuperar: E01–E12; boot RT00–RT04; ciclo RT10–RT45; RT80 recovery gate; RT90 cierre; idempotencia; capability selection; memoria mínima; validación input; Tribunal; auditoría; resume desde checkpoint sin reiniciar lo ya DONE.

### `DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md`
Recuperar: 0% LLM; `deploy_config.yaml`; dry-run; `plan.json`; `SIN_REGLA=FAIL`; bloqueo de secretos; copiar/desplegar idempotente; semver por hashes; CHANGELOG; push; verificación post-push; `evidence.json`; regla “sin evidence no está desplegado”.

### `GUIA_MAESTRA_PIPELINE_NCT_v2.html`
Recuperar: Pipeline como auditoría viva; fases reales; archivos/fuentes por fase; 3 pasadas + 3 revisiones + cross-check; formato técnico/simple; mapeo directo a UOOS Parte 1 y Parte 2; separación diseño/ejecución/despliegue.

### `INSTRUCCIONES_GROK_OPCION_A.md`
Recuperar: motor de programación compartido; `ProgrammingInstance`; `InstancePool`; classifier hook; capability registration; usage metering; idempotency; concurrencia; watchdog; fallback/queue; schemas pendientes; no reemplazar legacy hasta paridad de tests.

### Enchufe Universal parte 1 + Ficha parte 2 + contrato universal JSON
Recuperar: Ficha, I/O, invariantes, seguridad, sandbox, permisos, límites, registry, adapter, healthcheck, fallback, versionado, ledger, mount/shadow/hotswap. Cualquier ejecución dinámica de código candidato se trata como riesgo y queda bloqueada/aislada hasta validación.

### Prompt extracción documento→Ficha
Recuperar: convertir cada requisito documental en item/ficha con ID, origen, objetivo, dependencia, destino, contrato y trazabilidad para programación.

### Skill GitHub Acción
Recuperar: `DO_NOT_REWRITE_CODE`, `COPY_THEN_SURGICAL_EDIT`, locks SHA, descarga/extracción, provenance, validación y read-back.

## Contrato de recuperación por nodo
1. Antes de mutar: registrar `node_id`, `mission_id`, `trace_id`, INPUT literal, source_refs, destino, SHA/commit previo y evidencia esperada.
2. Crear checkpoint pre-mutation.
3. Ejecutar una sola tarea/nodo de la cola.
4. Verificar/refutar contra contrato y documentos cableados.
5. Si FAIL: conservar error y evidencia; no avanzar; investigar exactamente 20 alternativas distintas al delta fallido.
6. Rankear alternativas por `REUSE > COPY/MOVE > PATCH PEQUEÑO > ADAPTER > GENERATE DELTA`, riesgo, reversibilidad, tests y compatibilidad.
7. Aplicar únicamente el nuevo delta autorizado; no repetir ciegamente el mismo delta fallido.
8. Reejecutar tests/verificación. Si vuelve a fallar, reinyección del INPUT/objetivo original y otro lote distinto de 20 alternativas.
9. `ROLLBACK`: restaurar blob/SHA/commit previo; nunca reconstruir de memoria.
10. Actualizar STATE + CHECKPOINT + Crazy Wall en cada transición.
11. Ningún nodo pasa a DONE sin `evidence_hash`, prueba funcional y trazabilidad fuente→tarea→archivo→test→resultado.
12. API keys/credenciales nunca se guardan aquí: solo `secret_ref`.

## Recuperación del ledger literal
Fuente histórica verificable: commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc`, blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`. Si un INPUT anterior falta en el README actual, se restaura desde ese blob literalmente y luego se anexan los INPUT posteriores, sin resumir.

## Condición de fail-closed
Si README, STATE, CHECKPOINT, Recovery o Crazy Wall divergen; si falta una fuente obligatoria; si una instrucción fue reinterpretada; o si no existe evidencia real: estado = `GAP`, volver al LOOP y no escalar a siguiente nodo.
