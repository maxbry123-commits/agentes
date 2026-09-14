# ANEXO 01 — PLAN DE CAPAS + FUENTES + CHECKPOINT + RECOVERY

## Autoridad y ancla
- Contrato: `tel.workflow/v3`.
- README canónico: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`.
- Este anexo NO reemplaza INPUT BLOCKS; los consume literalmente.
- STATE: `Crazy Wall Orquestador/STATE.json`.
- CHECKPOINT: `Crazy Wall Orquestador/CHECKPOINT.json`.
- RECOVERY: `Crazy Wall Orquestador/RECOVERY-PATCH.md`.
- BITÁCORA: `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`.
- Regla de IDs: este anexo usa exactamente la numeración canónica `0–24` del README; divergencia futura = GAP.

## Cadena obligatoria por nodo
`goals 12/12 → revisar INPUT BLOCK literal sin interpretar → prioridades → planifica → cola 1×1 → verifica/refuta + 20 soluciones → analiza; si falla LOOP → auditor instrucciones 3x → auditor salida 12 pasos → 3 refutaciones (input/tareas/cumplimiento) → verificación cruzada global → checklist + salida`.

## Checkpoint mínimo antes de cualquier mutación
Cada nodo registra: `node_id`, `mission_id`, `trace_id`, objetivo literal, INPUT BLOCK aplicable, 12 goals entrada, fuentes con ruta/URL/SHA, dependencias, destino exacto, blob/commit previo, evidence esperado, rollback SHA, estado y siguiente nodo permitido.

## Matriz detallada: qué se extrae de cada documento cableado

### SRC-README — README canónico
Extraer literalmente: todos los INPUT BLOCKS; Parte 1, Parte 2, Parte 3, Parte 4; autorizaciones y prohibiciones; formato de presentación `➡️📂 Capa N` + microflujo español; estados pendiente/listo; destinos; regla no reinterpretar; cadena LOOP; obligación de checkpoint/recovery/state/Crazy Wall; política de copiar/reusar antes de reescribir; gates del Director. No sustituir texto literal por resumen operativo.

### SRC-ARCH-WORDFLOW — `📌✅😀Arquitectura para hacer el código Wordflow.md`
Extraer: definición funcional de workflow; core/kernel; razonamiento; control; memoria; ejecución; test/verificación; persistencia; optimización; reglas para decidir dónde vive cada pieza; método de programación; clasificación previa; contratos; trazabilidad; arquitectura modular; gaps entre diseño y código real; reglas para convertir requisito documental en necesidad de código; método para incorporar código sin convertir el kernel en monolito.

### SRC-CHAT-A-B — `PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md`
Extraer: rol Arquitecto Chat A y Ejecutor Chat B; 10 auditorías de entrada; INPUT_BLOCK + Sentinel; MissionContract + GoalLock; Ask Council 12; PROJECT_ANALYSIS; ARCHITECTURE; DAG; ROOT_MAP; Dependency Map; orden REUSE > PATCH > ADAPT > GENERATE; división de tareas ≤2000 LOC; bloques de código ≤500 LOC; contrato por tarea; pruebas; EvidencePacket; formato exacto de entrega del ejecutor; prohibición de que ejecutor rediseñe la arquitectura.

### SRC-UOOS-1 — UOOS Parte 1 v2
Extraer: B1 PROJECT_MANIFEST; B2 state.json; B3 DSL por tarea; B4 DAG; B5 loops L01–L11; B6 Tribunal; B7 plan construcción/despliegue; B8 Recovery; leyes L01–L15; investigación OSS antes de código nuevo; archivo=responsabilidad; no borrar código; flags; no inventar APIs; dependencias versionadas; DAG obligatorio; sandbox; estado solo por eventos; evidencia obligatoria; anti-scope-creep; ambigüedad; reproducibilidad; state machine; checkpoint por subgoal; rollback; telemetry; memory read/write.

### SRC-UOOS-2 — UOOS Parte 2 v3 Runtime
Extraer: E01–E12; prohibición de replanificar durante ejecución; una tarea/nodo activo; RT00 versión; RT01 integridad bidireccional B2/B3/DAG/schema/skills; RT02 preflight; RT03 skills bootstrap solo por necesidad; RT04 resume desde checkpoint; RT10 selección; RT11 idempotencia; RT12 capability/delegación; RT13 memoria mínima; RT14 input schema; RT20 ejecutar dentro de loop; RT30 Tribunal; RT31 Goal Check; RT40 artefactos; RT41 consistencia; RT42 auditoría; RT43 memoria salida; RT44 optimización; RT45 entrega; RT80 Recovery Gate; RT90 cierre; locks de archivos/recursos; no aceptar resultado delegado sin Tribunal.

### SRC-DEPLOY — `DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md`
Extraer: despliegue 0% LLM; destino declarado y no decidido por agente; `deploy_config.yaml`; reglas/protecciones; dry-run; `plan.json`; `SIN_REGLA=FAIL`; secret blocking; aprobación/validación; copia/sincronización idempotente; git add/commit; semver por hashes; CHANGELOG; push; verificación HEAD remoto==local; archivos==plan; tag/version; `evidence.json`; sin evidencia no hay despliegue. Destino del proyecto: `agentes/➡️➡️📂 Agente Yaiwes principal/`.

### SRC-PIPELINE-NCT — `GUIA_MAESTRA_PIPELINE_NCT_v2.html`
Extraer: auditoría viva; fases reales; fuente/archivo que alimenta cada fase; 3 pasadas + 3 revisiones + cross-check; separación diseño/ejecución/despliegue; mapeo Pipeline→UOOS1/UOOS2; formato técnico/simple; criterios de transición y detección de gaps.

### SRC-PROGRAMMING-POOL — `INSTRUCCIONES_GROK_OPCION_A.md`
Extraer: motor compartido de programación; `ProgrammingInstance`; `InstancePool`; mission/tenant/API/engine/idempotency; classifier hook; capability registration; usage metering; concurrencia; heartbeat/watchdog; fallback chain; queue; schemas faltantes; condición de no reemplazar legacy hasta paridad de tests.

### SRC-PLUGIN-BUS — Enchufe Universal parte 1
Extraer: registry; adapter; mount; plugin routing; shadow; hotswap; health; fallback; aislamiento; mecanismo de cableado. Riesgo: cualquier ejecución dinámica queda bloqueada/aislada hasta validación; no convertir el bus en permiso de ejecución arbitraria.

### SRC-FICHA — Ficha contrato parte 2
Extraer: identidad/version/hash; contrato I/O; invariantes; permisos; límites; sandbox; dependencias; compatibilidad; versionado; healthcheck; fallback; recovery; governance; evidencia; criterios de aceptación/rechazo antes de mount.

### SRC-UNIVERSAL-CONTRACT — JSON/DSL Enchufe Universal
Extraer: artifact_id/version/hash; registry metadata; consume/expone; determinismo/idempotencia; permissions/limits/sandbox; `ejecucion.kind`; transport; fallback; schemas de resultado; dependencias; governance ledger. Diferenciar `kind: code` para capacidad determinista y `kind: llm` solo donde razonamiento no determinista sea necesario.

### SRC-EXTRACTION-FICHA — documento→Ficha
Extraer: cada requisito como item con ID; documento/origen; cita/ruta; objetivo; dependencia; destino; criterio de éxito/fallo; contrato; tarea de programación; trazabilidad documento→item→ficha→code→test→evidence.

### SRC-GHA-SKILL — Skill GitHub Acción
Extraer: `DO_NOT_REWRITE_CODE`; `COPY_THEN_SURGICAL_EDIT`; reutilización por blob/SHA; locks; provenance; descarga/extracción; validación; read-back; comparar SHA fuente/destino; cambios quirúrgicos solo en cableado/plugin autorizado.

## Arquitectura por capas/nodos y microflujos — CANÓNICA 0–24

### ➡️📂 Capa 0 — Gobierno, ledger, STATE, CHECKPOINT y Recovery
`INPUT literal → mission/trace/node → STATE → checkpoint pre-mutation → ledger/Crazy Wall → Sheriff → allow/block → evidence → checkpoint post-step`.

### ➡️📂 Capa 1 — Intake, InputBlockReader, objetivo y GOAL_LOCK
`input → InputBlockReader/hash-chain → extracción literal → goal-dual-driver → GOAL_LOCK → 12/12 goals → MissionContract → PASS/GAP`; no fusionar instrucciones ni inventar metas.

### ➡️📂 Capa 2 — Investigación
`consulta literal → chat/historial → repos/código interno → repos Maxbry → OSS/docs/PyPI/Papers With Code → comunidad secundaria → filtrar/dedup/rank → URL/ruta/SHA/licencia/fecha`; REUSE primero.

### ➡️📂 Capa 3 — Auditoría forense X-Ray documental
`índice/documento → lectura real → 12 goals → extracción → clasificación → fusión → auditoría consistencia/cobertura → Council12 → qué código debe existir → localizar → GAP=nuevo objetivo/tarea`.

### ➡️📂 Capa 4 — Auditoría forense X-Ray de código
`requisito documental → ruta esperada → búsqueda global → código/imports/contracts/tests → documento↔código → WIRED|PARTIAL|STUB|GAP → task ID`.

### ➡️📂 Capa 5 — REUSE / copiar / mover
`candidato → SHA origen → procedencia/licencia → compatibilidad → COPY exacto → SHA destino → compare/read-back → evidence`; `REUSE > COPY/MOVE > PATCH PEQUEÑO > ADAPTER > GENERATE DELTA`.

### ➡️📂 Capa 6 — Adquisición GitHub Action / descarga y extracción
`source list → GitHub Action → lock SHA → download/clone → validar archive/LFS/hash → extracción → provenance manifest → scan → staging → evidence`; descarga ≠ integración.

### ➡️📂 Capa 7 — Evolución de capacidades
`GAP → classify target → research reuse → Council12 → proposal → Director gate → acquire → sandbox → mount → verify`.

### ➡️📂 Capa 8 — Clasificador arquitectónico de programación
`task → WORKFLOW|CORE/KERNEL|RAZONAMIENTO|CONTROL|MEMORIA|EJECUCIÓN|TEST|PERSISTENCIA|OPTIMIZACIÓN → destino → blast radius → complexity/profile → capability?`.

### ➡️📂 Capa 9 — Reasoning modules deterministas / catálogo 105
`problema → expert_panel_router → capability match → función Python determinista → output → verify`; solo falta real → `kind: llm`.

### ➡️📂 Capa 10 — Arquitecto Chat A / Council
`10 auditorías → INPUT/Sentinel → MissionContract/GoalLock → Council12 → análisis → arquitectura → DAG YAML/JSON → ROOT_MAP → dependencies → tasks ≤2000 LOC`.

### ➡️📂 Capa 11 — Ejecutor Chat B / motor de programación
`TaskContract único → classifier → ProgrammingInstance → sandbox/worktree → reuse/delta → tests → EvidencePacket → retorno a Chat A`; no rediseñar; ≤500 LOC/bloque.

### ➡️📂 Capa 12 — Espejo y registro de agentes de programación
`capability registry → engine_binding → adapter gateway → agente elegido → mismo contrato → result normalization → EvidencePacket → Tribunal`.

### ➡️📂 Capa 13 — Enchufe Universal + Ficha/Contrato
`candidate → static AST analysis → Ficha → invariants/I-O/permissions → sandbox → Tribunal → adapter/plugin → registry → health/fallback → telemetry → evidence → mount`.

### ➡️📂 Capa 14 — Orquestación / Scheduler / Time-Wheel / cola 1×1
`DAG → topological sort → priority/dependencies → scheduler → timeout/deadline → locks → queue 1×1 → dispatch → heartbeat/watchdog → event`.

### ➡️📂 Capa 15 — Persistencia LOOP / OpenMythos adaptado
`anchor original → intento → verify/refute → FAIL? 20 alternativas distintas → seleccionar delta nuevo → checkpoint/recovery → retry → PASS → Coda`.

### ➡️📂 Capa 16 — Heartbeat, memoria y mecanismos
`heartbeat → snapshot → stale/deadline check → Sentinel/watchdog → retry/circuit-breaker → checkpoint/recovery → resume → memoria validada`; nombres de capacidades no prueban implementación.

### ➡️📂 Capa 17 — Auditoría adversarial + cruzada + Maker-Checker + Tribunal
`maker output → adversarial audit → documento↔código → checker independiente → Judge/VerdictAuthority → Guardian → PASS? evidence_hash : LOOP`.

### ➡️📂 Capa 18 — UOOS Parte 1 / diseño ejecutable
`B1 Manifest → B2 State → B3 nodos DSL → B4 DAG → B5 loops → B6 Tribunal → B7 construcción/despliegue → B8 Recovery`.

### ➡️📂 Capa 19 — UOOS Parte 2 / runtime
`RT00→01→02→03→04 → RT10→11→12→13→14→20→30→31→40→41→42→43→44→45`; fallo→`RT80`; todos DONE→`RT90`.

### ➡️📂 Capa 20 — Despliegue determinista
`deploy_config.yaml → dry-run → plan.json → SIN_REGLA/secret gates → validar → copy/sync → commit → semver/CHANGELOG → push → verify remoto → evidence.json`; 0% LLM en decisiones de despliegue.

### ➡️📂 Capa 21 — Integración repos Maxbry ↔ Hugging Face compute
`inventario repos → capability map → credential refs → verificar 3 procesadores/runtime → resource broker/leases → adapter → test mínimo → telemetry/evidence`; no afirmar conexión sin prueba real.

### ➡️📂 Capa 22 — Almacenamiento y memoria externa
`data class → Graphiti|Grapify|SQL|HF storage disponibles? → schema/ownership → adapter → write/read consistency → backup/checkpoint → test/evidence`.

### ➡️📂 Capa 23 — APIs/modelos y secretos
`capability requerida → secret_ref → adapter/gateway → allowed provider/model → timeout/budget/rate limit → health → fallback/circuit breaker → usage ledger → evidence`; nunca guardar API keys en repo/README/log.

### ➡️📂 Capa 24 — Auditoría final, E2E, SBOM y cierre
`unit → contract → integration → E2E reception→mission→decision→execution→evidence→closure → secret scan → SBOM → placeholder/stub audit → 4 verificaciones → 3 refutaciones → 5 cross-checks → VerdictAuthority → checkpoint final/commit histórico`; cierre solo `VERIFIED_CLOSED` con evidencia real.

## Auditoría previa a presentación
### Verificación 1 — instrucciones
Comprobar que la salida conserva formato por capas, INPUT literal como autoridad, no reinterpretación y no omite Parte 1–4.
### Verificación 2 — documentos
Cada capa debe tener al menos una fuente cableada o quedar GAP; no convertir nombres de componentes en hechos implementados.
### Verificación 3 — ejecución
Separar claramente plan/documentación de implementación real; presencia de archivo ≠ integración.
### Verificación 4 — recuperación
Todo nodo debe poder restaurarse por SHA/commit y tener STATE/CHECKPOINT/Recovery/Crazy Wall.

## Refutaciones obligatorias
1. Refutación INPUT: ¿alguna acción contradice o amplía una instrucción literal? Si sí → GAP.
2. Refutación tareas: ¿alguna capa no tiene objetivo, fuente, destino, contrato o evidencia esperada? Si sí → GAP.
3. Refutación cumplimiento: ¿se afirma PASS sin test/hash/read-back/evidence real? Si sí → degradar a GAP/INCONCLUSIVE.

## Ask Consil 12
1 objetivo; 2 alcance; 3 fuentes; 4 dependencias; 5 destino; 6 REUSE; 7 contrato; 8 riesgo; 9 validación; 10 recovery; 11 evidencia; 12 cierre. Cada respuesta debe ser soportada por INPUT/fuente/estado; ausencia = GAP.

## 12 goals de salida del plan
1 capas separadas; 2 microflujo por capa; 3 fuentes cableadas; 4 trazabilidad; 5 DSL/DAG/schema exigidos; 6 Sheriff/Validator/Verifier; 7 Sentinel/Supervisor/Judge/Guardian; 8 checkpoint/recovery; 9 state/Crazy Wall; 10 gates de evidencia; 11 LOOP/refutación; 12 formato de presentación Director.

## Estado
Numeración de capas reconciliada 1:1 con README canónico: `0–24`, 25 nodos. Este anexo documenta y cablea el PLAN; no convierte por sí mismo implementación/runtime en PASS.