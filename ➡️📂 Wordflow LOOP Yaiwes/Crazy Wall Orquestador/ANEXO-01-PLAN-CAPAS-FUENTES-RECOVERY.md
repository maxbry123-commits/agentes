# ANEXO 01 — PLAN DE CAPAS + FUENTES + CHECKPOINT + RECOVERY

## Autoridad y ancla
- Contrato: `tel.workflow/v3`.
- README canónico: `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme wordflow loop Yaiwes.md`.
- Este anexo NO reemplaza INPUT BLOCKS; los consume literalmente.
- STATE: `Crazy Wall Orquestador/STATE.json`.
- CHECKPOINT: `Crazy Wall Orquestador/CHECKPOINT.json`.
- RECOVERY: `Crazy Wall Orquestador/RECOVERY-PATCH.md`.
- BITÁCORA: `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`.

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

## Arquitectura por capas/nodos y microflujos

### ➡️📂 Capa 0 — Gobierno, INPUT literal y ledger
`INPUT BLOCK literal → hash/trace/mission → 12 goals entrada → autorización explícita → STATE/CHECKPOINT/RECOVERY/Crazy Wall → gate`; sin autorización o divergencia = GAP.

### ➡️📂 Capa 1 — Investigación
`objetivo bloqueado → fuentes internas/chat → repos código → comunidad secundaria → filtrar/dedup → rank → URL/SHA/fecha → conclusión`; REUSE primero.

### ➡️📂 Capa 2 — Auditoría forense X-Ray documental
`documento → 12 goals entrada → 12 Ask Consil → extracción de requisitos → comparación con arquitectura → comparación con código → buscar información relacionada/mejor versión → requisito inexistente = nuevo objetivo → IDs/tareas trazables → 12 goals salida`.

### ➡️📂 Capa 3 — Auditoría X-Ray de código
`objetivo documental → ruta esperada → buscar en raíz proyecto → repos Maxbry → agentes motores Wordflow YAIWES → router → orquestador/auditor/memoria → clasificar existente/parcial/ausente → evidence`.

### ➡️📂 Capa 4 — Adquisición/copia/movimiento
`pieza elegida → licencia/provenance/SHA → checkpoint pre-mutation → COPY por blob/SHA → destino → read-back → hash fuente==destino → evidence`; no reescribir.

### ➡️📂 Capa 5 — GitHub Action descarga/extracción
`repo fuente → skill GHA → lock SHA → descarga/clonado → validación LFS/ZIP/manifiesto → extracción → provenance → read-back → evidence`; aplicar mejoras canónicas del skill.

### ➡️📂 Capa 6 — Evolución de capacidades
`gap → calificar necesidad → investigar capacidad existente → propuesta → autorización → adquisición → sandbox → mount → verificación → registro`; reutilizar workflow evolución ya existente.

### ➡️📂 Capa 7 — Clasificador de programación
`requisito → WORKFLOW|CORE/KERNEL|RAZONAMIENTO|CONTROL|MEMORIA|EJECUCIÓN|TEST|PERSISTENCIA|OPTIMIZACIÓN → ruta destino → contrato → skill requerido`; no programar antes de clasificar.

### ➡️📂 Capa 8 — Catálogo determinista 105
`necesidad → catálogo → PyPI/repo referencia → madurez/licencia/tests → Ficha `kind: code` → registry → llamada Python directa`; LLM no reemplaza algoritmo determinista.

### ➡️📂 Capa 9 — Arquitecto Chat A
`10 auditorías → INPUT+Sentinel → MissionContract+GoalLock → Council12 → análisis → arquitectura → DAG → ROOT_MAP → Dependency Map → REUSE/PATCH/ADAPT/GENERATE → task contracts → entrega a ejecutor`.

### ➡️📂 Capa 10 — Ejecutor Chat B / programación
`task contract único → preflight → skill/capability → sandbox → implementar delta limitado → tests → EvidencePacket → devolver`; no replanifica, no cambia alcance.

### ➡️📂 Capa 11 — Espejo/pool de agentes
`task_classifier → ProgrammingInstance → InstancePool → capacidad → agente primario → 2 fallos/no PASS → agente espejo → mismo contrato → Tribunal`; agentes concretos quedan pendientes de decisión del Director salvo OpenClaw/Hermes para auditoría documental.

### ➡️📂 Capa 12 — Enchufe Universal/Ficha
`artefacto → Ficha → invariantes → I/O → permisos/sandbox → adapter/plugin → registry → health/fallback → mount/shadow/hotswap → evidence`.

### ➡️📂 Capa 13 — Scheduler/cola
`DAG topológico → prioridad → dependencias → cola 1×1 por instrucción actual → timeout/deadline → locks → idempotencia → siguiente elegible`; concurrencia solo cuando contrato futuro lo autorice.

### ➡️📂 Capa 14 — Persistencia/LOOP
`checkpoint → ejecutar nodo → evidencia fresca? NO→GAP→20 alternativas distintas→nuevo delta→retry; SÍ→CODA→verify_final`; resume desde último checkpoint, no desde cero.

### ➡️📂 Capa 15 — Heartbeat/watchdog/memoria
`heartbeat → snapshot → deadline/watchdog → detectar colgado → recovery → memoria jerárquica/graph/vector/cache según capacidad validada → consolidación`; niveles de memoria se tratan como capacidades a demostrar, no nombres suficientes.

### ➡️📂 Capa 16 — Maker-Checker/Tribunal
`maker output → checker documental → checker código → verificación cruzada → Judge/Guardian → score/criterios objetivos → PASS/GAP`; nada cerrado por autodeclaración del ejecutor.

### ➡️📂 Capa 17 — UOOS Parte 1 documental
`B1 Manifest → B2 State → B3 DSL nodos → B4 DAG → B5 L01-L11 → B6 Tribunal → B7 construcción/despliegue → B8 Recovery`.

### ➡️📂 Capa 18 — UOOS Parte 2 runtime
`RT00→01→02→03→04→RT10→11→12→13→14→20→30→31→40→41→42→43→44→45`; fallo→RT80; todos DONE→RT90.

### ➡️📂 Capa 19 — Despliegue determinista
`deploy_config → dry-run → plan.json → regla/secret gates → validar → copiar/sincronizar → commit → semver/CHANGELOG → push → verificar remoto → evidence.json`; destino `Agente Yaiwes principal`; 0% LLM.

### ➡️📂 Capa 20 — Compute Hugging Face
`inventario real conectores → verificar 3 procesadores/recursos → contrato de conexión → health → scheduler/resource broker → prueba mínima → evidence`; no declarar conectado sin prueba real.

### ➡️📂 Capa 21 — Almacenamiento/memoria externa
`requisito → auditar Graphiti/Grapify/SQL/HF disponibles → schema/ownership → adapter → persistencia → consistencia → recovery → test → evidence`; cada backend se valida por separado.

### ➡️📂 Capa 22 — Multi-API/modelos/secretos
`capacidad requerida → router → secret_ref → proveedor/modelo → health/rate limit → fallback → usage ledger → circuit breaker → evidence`; nunca guardar API keys en repo/README/log.

### ➡️📂 Capa 23 — Auditoría E2E y cierre
`reception → mission → decision → execution → evidence → deployment cuando aplique → closure → X-Ray final → SBOM/secret scan → tests → evidence_hash → 12 goals salida → CLOSED solo con 100% PASS`.

### ➡️📂 Capa 24 — Archivo/continuidad
`estado final → checkpoint final → Merkle/hash/commit → archivar históricos → Crazy Wall → próximo objetivo`; permite recuperación exacta y evita reconstrucción de memoria.

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
Este anexo documenta y cablea el PLAN. No convierte por sí mismo capas pendientes en implementación PASS. Parte 2 permanece READY; Parte 1/3/4 requieren construcción/verificación según STATE.