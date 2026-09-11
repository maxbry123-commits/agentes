# GAPS — INVESTIGACIÓN + CODE GRAPH — WORDFLOW LOOP YAIWES

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.
Fecha de apertura: 2026-09-10.
Regla: **todo punto inicia como GAP hasta existir evidencia de investigación + decisión arquitectónica + implementación cuando corresponda + test/read-back + actualización de STATE/CHECKPOINT/BITÁCORA/HANDOFF/README**.

## G-001 — Raíz anclada de CODE GRAPH
Estado: `GAP_OPEN`.
Crear dentro del Wordflow una raíz de trabajo para recibir archivos/componentes y construir un grafo cableado del proceso completo. Debe representar archivos, requisitos, capacidades, tareas, dependencias, destinos arquitectónicos, agentes, sandbox, validaciones, evidencias, deployment y estados del LOOP. No puede crear un segundo orquestador aislado; debe integrarse al contrato y a la persistencia existentes.
Cierre: raíz canónica + contrato de nodos/aristas + serialización determinista + test.

## G-002 — Ask Council + auditoría del archivo de entrada
Estado: `GAP_OPEN`.
Cada archivo recibido debe pasar por análisis de formato, contenido, arquitectura, dependencias, riesgos, capacidades, intención y trazabilidad. El Council aporta razonamiento, pero la salida debe normalizarse a un contrato determinista. Se debe extraer la arquitectura del archivo y convertirla en requisitos programables.
Cierre: contrato de auditoría + salida estructurada + simulaciones + evidencia.

## G-003 — Generador determinista de lista de tareas de código
Estado: `CLOSED_VERIFIED_LOCAL`.
Transforma requisitos/arquitectura en tareas atómicas con `task_id`, dependencia, prioridad, capability, owner/rol, inputs, outputs, destino propuesto, riesgo, sandbox requerido, test, evidence y estado, manteniendo separadas tareas del Director y tareas generadas. Implementación: `runtime/src/core/code_task_graph.py`; evidence `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`.

## G-004 — Clasificador de destino arquitectónico
Estado: `CLOSED_VERIFIED_LOCAL`.
Analiza dónde debe vivir el código usando función, privilegio, lifecycle, estado, tipo de ejecución, seguridad, latencia, acoplamiento y dependencias. Opciones: A Kernel; B Extension Kernel; C Reasoning Layer; D Wordflow; E Pool; F Tools; G otras ubicaciones justificadas. Implementación: `runtime/src/core/placement_classifier.py`, blob `69698ad30ba1903e0780efcea1952a3737aeb23e`; tests `runtime/tests/test_placement_classifier.py`, blob `bf1c26f49edf668ee05584b2a357324af0fc4d8d`; evidence `wordflow_loop/evidence/G004_PLACEMENT_CLASSIFIER_2026-09-10.json`; simulación local equivalente `PASS_10_OF_10_ASSERTIONS`. Señales débiles/conflictivas o G sin ubicación+justificación => `PLACEMENT_REVIEW_REQUIRED`. No se reclama runtime externo.

## G-005 — Investigación previa a creación/adaptación de código
Estado: `GAP_OPEN`.
Antes de generar código, buscar reutilización real: librerías Python, YAML/schema, parsers, RAG, grafos, validación, seguridad, workers, colas, sandbox y despliegue. Mantener hasta 10 opciones pertinentes cuando exista decisión de biblioteca y registrar fuente, licencia, mantenimiento, compatibilidad y riesgo. Política `REUSE > PATCH > ADAPT > GENERATE`.
Cierre: catálogo de opciones + selector documentado + evidence URLs.

## G-006 — Creación de código nuevo
Estado: `GAP_OPEN`.
Cuando no exista pieza reutilizable adecuada, generar código mínimo y modular, con contrato estable, typing/schema, idempotencia, fail-closed, logs estructurados, pruebas y conexión exclusiva por el Enchufe Universal Fables. Ningún LLM puede saltarse gates deterministas.
Cierre: ABI/Protocol + módulo + tests + registro/cableado.

## G-007 — Ingesta de código ejecutable ya existente
Estado: `GAP_OPEN`.
Si el archivo recibido ya es código, evaluar REUSE/PATCH/ADAPT; cuando corresponda usar motores canónicos de copiar/mover, conservar trazabilidad y adaptar a `.py`, YAML o mixto solo cuando la arquitectura lo requiera. No reescribir upstream sin necesidad.
Cierre: source proof + decisión + destino + read-back + test.

## G-008 — Neutralización de comportamiento malicioso/inseguro
Estado: `GAP_OPEN`.
Analizar componentes antes de ejecución. Si existe conducta maliciosa o incompatible con políticas del sistema, bloquearla; solo sustituir por una acción benigna funcionalmente equivalente cuando sea técnicamente justificable. Nunca ejecutar primero para descubrir si era malicioso.
Cierre: scanner/gates + reason codes + sandbox tests + evidencia.

## G-009 — Componente sin valor / GAP de rechazo
Estado: `GAP_OPEN`.
Si una pieza no mejora capacidades, duplica funcionalidad sin beneficio, degrada seguridad/mantenibilidad o no puede cablearse de forma útil, marcarla `NO_VALUE_GAP` y producir `.md` con justificación, alternativas y decisión pendiente del Director.
Cierre: plantilla GAP + reviewer independiente.

## G-010 — Watchdog horario supervisor del Wordflow
Estado: `CLOSED_VERIFIED`.
Cada hora revisar tareas, GAPs, bloqueos, estado de grafos/DAG, integridad de contratos, evidencia, colas, agentes, router, sandbox y persistencia. Resolver automáticamente solo lo autorizado y determinista; no inventar PASS. Informar al Director de cambios materiales.

## G-011 — Pipeline de recepción de componentes + motor de copiar/mover
Estado: `GAP_OPEN`.
Recibir `source + destination` explícitos. Estudiar el motor canónico, mantenerlo inmutable, ejecutar la operación de copia/movimiento y después analizar/cablear el componente dentro del Wordflow. La raíz `Core kernel Yaiwes/` y otros repos son fuentes de lectura, no destinos de escritura de esta fase.
Cierre: motor canónico disponible dentro del LOOP + blob SHA preservado + prueba read-back.

## G-012 — Pipeline de lista de componentes para descargar/extract
Estado: `GAP_OPEN`.
Cuando el Director entregue lista de componentes y destinos, el LOOP debe encolar descargas/extracciones de forma determinista usando motores canónicos: destino explícito, allowlist, sin LFS, sin force, CRC/hash/read-back y fail-closed.
Cierre: intake schema + queue + adapter a motores + simulación segura.

## G-013 — Fuentes de verdad operativas
Estado: `GAP_OPEN`.
Mantener sincronizados: 1) mapa/diagrama de trabajo; 2) HANDOFF; 3) tareas generadas; 4) tareas entregadas por el Director; 5) Crazy Wall/STATE/CHECKPOINT/PLAN; 6) contrato Schema/DSL/DAG/Pipeline; 7) evidencias. Evitar estados contradictorios.
Cierre: source-of-truth policy + reconciliación automática.

## G-014 — `agente-readme-memoria.md` por agente
Estado: `GAP_OPEN`.
Cada uno de los 18 agentes debe tener memoria de operación versionada: rol, capacidades, prohibiciones, contratos, fuentes, gates, estilo de evidencia, errores aprendidos y mejoras aprobadas. Debe cargarse antes de ejecutar trabajo y actualizarse solo con aprendizaje verificado.
Cierre: 18 memorias + loader determinista + test de pre-injection.

## G-015 — 12 GOALS de entrada/salida + Council + simulaciones
Estado: `GAP_OPEN`.
Cada capacidad nueva debe evaluarse con 12 checks de entrada y 12 de salida, Council/Ask Council, simulaciones, refutaciones y cross-check. El razonamiento puede usar LLM; gates, estados y aceptación son deterministas.
Cierre: schema de goals + runner + evidencia por punto.

## G-016 — Conversión de arquitectura Chat A ↔ Chat B
Estado: `GAP_IN_RESEARCH`.
Buscar en documentos existentes el proceso indicado por el Director para conversión/transferencia de arquitectura entre Chat A y Chat B. Si existe, reutilizar y adaptar; si no se localiza tras búsquedas por nombre, contenido y documentos, registrar `NOT_FOUND` con evidencia y crear solo el mínimo equivalente autorizado.
Cierre: artefacto localizado/adaptado o NOT_FOUND probado.

## G-017 — Despliegue determinista
Estado: `GAP_OPEN`.
Revisar el mecanismo existente de despliegue: inputs validados → build/prepare → sandbox → tests → reviewer → promotion → checkpoint → rollback/compensación. Sin deployment directo desde salida LLM.
Cierre: pipeline/gates reales + rollback + prueba.

## G-018 — Enchufe Universal Fables obligatorio
Estado: `GAP_IN_RESEARCH`.
Confirmar físicamente la versión canónica del Enchufe Universal Fables y Ficha/Contract. Todo módulo nuevo se conecta solo por ese contrato/ABI; prohibido crear buses paralelos o integraciones ad hoc.
Cierre: source proof + adapter contract + test de registro.

## G-019 — Auditoría global de archivos del Wordflow
Estado: `GAP_OPEN`.
Revisar lo existente para detectar capacidades ya construidas, duplicados, piezas huérfanas, rutas rotas, documentación obsoleta y GAPs. No rehacer trabajo verificado.
Cierre: inventario/capability map + GAP ledger reconciliado.

## G-020 — 12 fuentes web/comunidad para arquitectura
Estado: `CLOSED_VERIFIED`.
Catálogo: `wordflow_loop/research/community_sources.json`; 12 fuentes verificadas con tema/autoridad/uso.

## G-021 — Cola + paralelismo controlado
Estado: `GAP_OPEN`.
Diseñar cola con prioridades, dependencias, fan-out/fan-in, deduplicación, idempotency keys, límites por proveedor y workers/pools por concern. Ejecutar en paralelo solo tareas independientes; dependencias del DAG siguen bloqueantes. Inspiración de los documentos Mavis: persistent pools, priority queue, batching, backpressure, async pipeline y dedup; sus multiplicadores de rendimiento quedan como hipótesis hasta benchmark local.
Cierre: scheduler/queue determinista + tests de dependencias, prioridad, dedup y backpressure.

## G-022 — Sandbox → reviewer → deploy
Estado: `GAP_OPEN`.
Todo código se ejecuta primero en sandbox aislado, con límites de filesystem/network/time/memory. Un segundo agente/reviewer valida evidencia antes de promover. Deployment final usa pipeline determinista.
Cierre: sandbox adapter + reviewer gate + promotion gate + prueba de rechazo.

## G-023 — Hugging Face: acceso, dataset y skills bridge
Estado: `GAP_IN_RESEARCH`.
Comprobar mediante el conector/recursos autorizados qué datasets, modelos, Spaces o bibliotecas de skills existen realmente. No asumir secretos. Crear puente determinista para inyectar contexto/skills aprobados antes de tareas, sin exponer tokens.
Cierre: inventario verificado + bridge + source refs + test sin secretos.

## G-024 — Separación determinismo / LLM
Estado: `GAP_OPEN`.
Scheduler, contracts, DAG, routing, state machine, gates, sandbox, hashing, deployment y evidence deben funcionar sin decisión LLM. LLM solo para análisis, síntesis, generación, Council o clasificación no resoluble por reglas; sus salidas se validan contra schema/gates.
Cierre: matriz `DETERMINISTIC|LLM_ALLOWED` + enforcement tests.

## G-025 — Patrones paralelos de los archivos aportados por el Director
Estado: `GAP_OPEN`.
Evaluar 1×1: persistent worker pool, priority queue, LRU/mmap cache, smart batching, streaming/backpressure, asyncio.Queue pipeline, dedup, Job ABI, registry/factory/DI/event bus/middleware/FSM/checkpoints/audit/tests/versioning/sandbox/capability routing; además fan-out/fan-in, sharding, DLQ, outbox/CDC, multi-pool, durable execution y recovery. Integrar solo lo que aporte al Wordflow y validar benchmarks en vez de asumir cifras 100x.
Cierre: matriz ADOPT/ADAPT/REJECT + pruebas.

## G-026 — UI/visual para operar el LOOP
Estado: `GAP_OPEN`.
Investigar una capa visual para mapa de DAG/grafos, cola, estado de tareas, GAPs, agentes, evidencia y checkpoints. Priorizar componentes ya presentes en repositorios del usuario y evitar un frontend monolítico.
Cierre: selección de stack visual + esquema de datos + prototipo/adapter cuando sea autorizado por gates.

## G-027 — Graphiti
Estado: `GAP_IN_RESEARCH`.
Componente localizado en `maxbry123-commits/osquestador-auditor/graphiti`. Investigar su uso como grafo temporal/contextual de arquitectura, historial de tareas, provenance y memoria operacional. Evaluar backend, dependencia LLM/embedding, MCP/FastAPI, licencia y costo operacional. No usar Graphiti como scheduler del DAG; su función candidata es contexto/provenance/memoria de grafo.
Cierre: investigación + copy exacta mediante motor + adapter opcional + sandbox test.

## G-028 — Graphology
Estado: `GAP_IN_RESEARCH`.
Componente localizado en `maxbry123-commits/osquestador-auditor/graphology`. Investigar como estructura de grafo JS/TS, algoritmos/traversals/layouts y backend de Sigma.js. Candidato principal para representación/visualización interactiva del mapa de tareas, no para durable execution.
Cierre: investigación + copy exacta mediante motor + integración visual/serializer si aporta valor.

## G-029 — Motor de planificación organizada de tareas
Estado: `GAP_IN_RESEARCH`.
Evaluar componentes existentes en el repo auditor: Dagster, Prefect, Argo Workflows, Inngest, Trigger.dev, Restate, Airflow, orquestador existente y alternativas ligeras. Elegir por compatibilidad con el LOOP actual, durable state, dependencies, parallelism, idempotency, deployment footprint y no duplicación de la fundación ya existente.
Cierre: matriz comparativa + decisión REUSE existente antes de añadir otro framework.

## G-030 — Crazy Wall compartido por agentes
Estado: `GAP_OPEN`.
Todos los agentes deben leer/escribir el mismo estado lógico sin pisarse. Implementar update protocol con version/checkpoint/idempotency y ownership por task/node. Cerrar grupo de tareas/GAPs con evidencia y abrir nuevo grupo conservando historial. El operador/supervisor audita coherencia cada hora.
Cierre: state update protocol + optimistic concurrency/merge rules + tests de conflicto.

## Evidencia inicial de investigación
- `osquestador-auditor/graphiti` localizado; README lo define como framework de grafos temporales/contextuales para agentes, con provenance, actualizaciones incrementales, búsqueda híbrida, MCP server y FastAPI.
- `osquestador-auditor/graphology` localizado; README lo define como Graph object JS/TS multipropósito, con algoritmos/utilidades/eventos y uso como backend de Sigma.js.
- Skill canónico de motores leído: motores inmutables, COPY_ONLY, blobs fijos, destino explícito, sin LFS/force, read-back obligatorio.
- El skill identifica el origen canónico de motores en `maxbry123-commits/frontend/main` y la allowlist de 7 archivos.

## Regla de cierre global
Ningún GAP pasa a `CLOSED` por presencia de archivo o por afirmación de un agente. Se requiere evidencia reproducible: source/provenance + decisión + implementación si aplica + test/simulación + read-back/commit + actualización de fuentes de verdad.
