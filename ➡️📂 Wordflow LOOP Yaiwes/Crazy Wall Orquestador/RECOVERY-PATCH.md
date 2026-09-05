# RECOVERY PATCH — Wordflow LOOP Yaiwes

## Anclas canónicas
- README: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`
- LEDGER PARTES 1–4: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/LEDGER-CANONICO-PARTES-1-4.md`
- ANEXO PLAN: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/ANEXO-01-PLAN-CAPAS-FUENTES-RECOVERY.md`
- AUDITORÍA X-RAY CORRECCIÓN 1:1 — VIGENTE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/AUDITORIA-XRAY-CORRECCION-1A1.md`
- AUDITORÍA X-RAY 5 PASADAS — HISTÓRICA PRE-CORRECCIÓN: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/AUDITORIA-XRAY-PLAN-5-PASADAS.md`
- STATE: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/STATE.json`
- CHECKPOINT: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/CHECKPOINT.json`
- BITÁCORA: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`
- HANDOFF: `➡️📂 Wordflow LOOP Yaiwes/HANDOFF.md`
- AGENTS: `AGENTS.md`

## Norma de reanudación — 3 pasadas antes de ejecutar
1. Pasada 1: leer README + LEDGER PARTES 1–4; usar INPUT literal cuando existe y registro aprobado inmutable cuando el contrato fue aprobado en Git; no reconstruir wording histórico desde memoria.
2. Pasada 2: leer STATE + CHECKPOINT + Crazy Wall + ANEXO + AUDITORÍA X-RAY CORRECCIÓN 1:1 vigente; usar el X-Ray 5 pasadas anterior solo como evidencia histórica. Reconciliar nodo, pendientes, SHAs, evidencia y recovery. Divergencia = GAP.
3. Pasada 3: releer documentos fuente del nodo listados en CHECKPOINT y las autoridades de `AGENTS.md`; cruzar documento↔plan↔código; ausencia de soporte = GAP.

Cadena obligatoria: `goals 12/12 → INPUT literal/registro aprobado → prioridades → plan → cola 1×1 → verifica/refuta + 20 soluciones → analiza/LOOP → auditor instrucciones ×3 → auditor salida 12 → 3 refutaciones → verificación global → checklist/salida`.

## Autoridad de instrucciones Parte 1–4 — corregida
1. Parte 1: INPUT 013 literal, commit `2d1c718f28333ef4b77e9c362f757bb74ff9c5cc`, blob `474af741abe3ac9c816f4406f0fc6e4e4490c2aa`.
2. Parte 2: INPUT 014 literal; mapeo commit `26760e498a59cb65bb2cdab14f1ac7554e0af0a1`; integración reuse commit `4b1c705f891199bb28ec1d0efb14bca223dd440f`.
3. Parte 3: usar exactamente el registro aprobado del commit `6b59f4a1514ba419cbeade7c948e68b65d02fe5d`; el diff contiene el contrato de 12 puntos preservado en README. Estado operativo: `APPROVED_CANONICAL_RECORD`.
4. Parte 4: usar mapa funcional aprobado del README + INPUT 015 literal; commit `a4fcb2c9d1286f7a8f9695ff2e54805744e8f7d9` registra literalmente la aprobación y plan siguiente. Estado operativo: `LITERAL_APPROVAL_VERIFIED + APPROVED_CANONICAL_MAP`.
5. La ausencia de una transcripción histórica adicional no autoriza inventarla ni invalida un contrato ya aprobado y fijado por commit. Para ejecución manda el registro aprobado inmutable.

## AGENTS.md — rutas obligatorias restauradas
- `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md` — commit `8024e57606cedc34592ef18b3565c624b1e6d676` — read-back PASS.
- `PIPELINE/FORENSIC_CODE_AUDIT.md` — commit `2072d535920573550a443cf9a3967ab66b50375c` — read-back PASS.
- `PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md` — commit `7bc798ad4173f39f758abd3d4e6cbc2d909658e6` — read-back PASS.

## Deltas de consistencia X-Ray que deben preservarse
- Director 12/12 prevalece para este Wordflow sobre la sección 10/10 del documento de arquitectura; ambas fuentes siguen trazadas.
- “DSL” = contrato declarativo existente YAML/JSON/schema; `ADDITIONAL_DSL: FORBIDDEN`; no inventar sintaxis nueva.
- Límites simultáneos: UOOS `≤200 líneas/archivo` cuando corresponda; Chat A/B `≤500 LOC/bloque`; `≤2000 LOC/task`.
- Cola del plan actual = `1×1`; paralelismo solo en fase futura autorizada por DAG/contrato/Director.
- Plugins externos autorizados: solo `GitHub` y `Hugging Face`; demás bloqueados.
- Candidate code: análisis estático/AST; ejecución dinámica (`exec()` o equivalente) bloqueada hasta sandbox+security PASS.
- Usage metering: debe persistir en ledger append-only antes de estado INTEGRATED.
- Deploy: `plan.json` + gates + push + verificación remota + `evidence.json`; sin ello no existe PASS.

## Recuperación detallada por fuente
- README: recuperar INPUT BLOCKS literales, Partes 1–4, autorizaciones/prohibiciones, formato `➡️📂 Capa N` + microflujo, destinos, gates, cadena LOOP, política no reinterpretar.
- Ledger Partes 1–4: resolver autoridad exacta por commit para cada parte; no usar resumen de memoria.
- Arquitectura Wordflow: recuperar clasificación WORKFLOW/CORE/KERNEL/RAZONAMIENTO/CONTROL/MEMORIA/EJECUCIÓN/TEST/PERSISTENCIA/OPTIMIZACIÓN, destino estructural, programación modular, contratos, trazabilidad y gaps.
- Chat A/B: recuperar 10 auditorías, INPUT+Sentinel, MissionContract+GoalLock, Council12, Analysis/Architecture/DAG/ROOT_MAP/Dependencies, REUSE>PATCH>ADAPT>GENERATE, límites LOC, task contract, EvidencePacket.
- UOOS1: recuperar B1-B8, L01-L15, DSL, DAG, loops, Tribunal, state events, checkpoint, rollback, evidence, anti-scope-creep y reproducibilidad.
- UOOS2: recuperar E01-E12, RT00-04, RT10-45, RT80, RT90, idempotencia, capabilities, memoria mínima, input validation, Tribunal, auditoría y resume.
- Deploy: recuperar 0% LLM, deploy_config, dry-run, plan.json, SIN_REGLA=FAIL, secret gate, copia idempotente, semver, CHANGELOG, push, verificación remota, evidence.json.
- Pipeline NCT: recuperar fases/fuentes, auditoría viva, 3+3 pasadas, cross-check, mapeo UOOS y separación diseño/ejecución/despliegue.
- Programming Pool: recuperar ProgrammingInstance, InstancePool, classifier, registry, metering, idempotency, watchdog, fallback, queue y schemas.
- Plugin/Ficha/Contrato: recuperar registry, adapter, mount, shadow/hotswap, I/O, invariantes, permisos, sandbox, dependencies, versionado, health, fallback, recovery, governance y `ejecucion.kind`; bloquear ejecución dinámica no validada.
- Extracción→Ficha: recuperar requisito→ID/origen/objetivo/dependencia/destino/contrato/tarea/evidence.
- Skill GitHub Action / deploy-router: recuperar DO_NOT_REWRITE_CODE, COPY_THEN_SURGICAL_EDIT, SHA locks, provenance, descarga/extracción, read-back y seguridad de COPY/MOVE.

## Recuperación por capa — HISTÓRICO, NO AUTORIDAD DE IDs
Este bloque conserva la numeración histórica pre-corrección y NO gobierna IDs de capa. La autoridad canónica de IDs es README 0–24 hasta que Tarea 1/2 aplique el delta quirúrgico de renumeración.
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
1 registrar node_id/mission_id/trace_id/INPUT o approved-record/source_refs/destino/SHA previo/evidence esperado; 2 checkpoint pre-mutation; 3 una tarea; 4 verificar/refutar; 5 FAIL conserva evidencia y genera exactamente 20 alternativas distintas; 6 rank REUSE>COPY/MOVE>PATCH>ADAPTER>GENERATE; 7 aplicar delta nuevo autorizado; 8 retest; 9 rollback por SHA/commit, nunca memoria; 10 actualizar STATE/CHECKPOINT/Crazy Wall; 11 DONE solo con evidence_hash+prueba+trazabilidad; 12 secretos solo secret_ref.

## CONSTITUCIÓN DEL DIRECTOR — MIRROR JSON
```json
{
  "schema": "tel.workflow/v3",
  "mode": "fail-closed",
  "mandatory_read_update": ["HANDOFF", "README", "STATE", "CHECKPOINT", "RECOVERY", "CRAZY_WALL"],
  "governance_goals_14": [
    "G01 INPUT literal+hash sin reinterpretar",
    "G02 reconciliar seis anclas obligatorias",
    "G03 bloquear y trazar 11 objetivos",
    "G04 una instrucción=un nodo",
    "G05 12 goals entrada+12 salida",
    "G06 prioridades antes de ejecutar",
    "G07 plan/destino/evidencia antes del delta",
    "G08 cola 1x1",
    "G09 verificar/refutar y LOOP ante fallo",
    "G10 investigar 10 vías y hasta 20 soluciones por GAP",
    "G11 REUSE>COPY/MOVE>PATCH>ADAPTER>GENERATE",
    "G12 auditor 3x+Council12+auditor salida12+3 refutaciones",
    "G13 actualizar anclas por cada avance real",
    "G14 cross-check global+checks reales antes de cerrar"
  ],
  "project_objectives_11": ["O01 LOOP horario", "O02 investigar código", "O03 COPY/REUSE", "O04 plugins", "O05 cinco pasadas+GAPs", "O06 tareas agentes", "O07 espejo agentes", "O08 HF/3 procesadores", "O09 storage", "O10 APIs secret_ref", "O11 auditoría/tests/cierre"],
  "input_goals_12": ["identificar_objetivo", "congelar_input_y_hash", "enumerar_alcance", "resolver_repo_rama_ruta_version", "capturar_restricciones", "capturar_autorizacion", "inventariar_dependencias", "inventariar_fuentes", "definir_evidencia_admisible", "definir_pre_post_condiciones", "fijar_formato_y_destino_salida", "compilar_cada_paso_como_nodo"],
  "output_goals_12": ["ejecutar_exacto_el_contrato", "preservar_trazabilidad_literal", "producir_artefactos_validos", "demostrar_pruebas_reproducibles", "cruzar_fuentes", "resolver_contradicciones", "cerrar_sin_supuestos", "registrar_url_version_sha_run_id", "mantener_ledger_encadenado", "reparar_y_reverificar_gap", "cumplir_control_de_salida", "cerrar_solo_con_12_12_verify_final_y_zero_gaps"],
  "ask_consilio_12": ["¿Qué afirmo?", "¿Qué evidencia lo demuestra?", "¿Qué podría demostrar que estoy equivocado?", "¿Estoy mirando la fuente correcta?", "¿La ruta/versión coincide?", "¿Existe realmente?", "¿Hay otra explicación?", "¿Qué dependencia falta?", "¿Puedo reproducirlo?", "¿El resultado contradice algo?", "¿Qué GAP permanece?", "¿Qué evidencia permite cerrar?"],
  "pipeline": ["SHERIFF", "VALIDATOR", "SIMULATE", "RESEARCH", "RANK", "EXECUTE", "SENTINEL", "VERIFY", "SUPERVISOR", "JUDGE", "GUARDIAN", "CODA"],
  "repeat_check": {"max_runs": 10, "pure_deterministic_runs": 1, "purpose": "detect_flakiness"},
  "research_funnel": {"steps": ["chat", "codigo", "comunidad", "filtra", "dedup", "rank+URL"], "solution_paths_on_gap": 10, "candidate_target": 20},
  "loop": {"rule": "NO_STOP_WHILE_GAP", "fail_restart": "RESEARCH", "max_recurrences_per_node": 100, "no_scope_escalation": true},
  "final_verification": {"sin_checks": "INCONCLUSIVE", "todos_pasan": "VERIFIED_CLOSED", "alguno_falla": "CLOSED_UNVERIFIED"}
}
```

## Fail-closed
Divergencia entre README/LEDGER/ANEXO/XRAY-CORRECCIÓN/STATE/CHECKPOINT/Recovery/Crazy Wall/HANDOFF/AGENTS, fuente ausente para el nodo activo, instrucción reinterpretada o evidencia inexistente => `GAP`; volver al LOOP, no avanzar. La reconciliación documental Parte 1–4 está PASS; implementación/runtime permanece independiente.