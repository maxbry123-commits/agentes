# ➡️📂 README arquitectura Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · modo `FAIL_CLOSED_EXECUTION_LOOP`.  
Raíz única autorizada de escritura: `maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.  
Arquitectura: modular, determinista por defecto, no monolítica.

## Flujo base previamente verificado
`documentos → requisitos → Task Contract/Ficha → agent_fleet_plugin_registration → AgentFleetAdapter → registry → binding ID/slot/rol → router disponibilidad/prioridad → transporte API/MCP/command → agente → evidencia → STATE/CHECKPOINT`.

## Fleet + router previamente verificados localmente
18 agentes · Council12=12. Routing determinista por ID/rol. Sin runtime configurado, `fail_closed`.
Router: `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.
Prioridad: Kimi → MiniMax → DeepSeek V4 Pro → DeepSeek V4 Flash → GLM 5 → Muse/Glimmer → Qwen 3.8 → GPT-OSS. El GAP externo `AUTH_PROVIDER_TEST_PENDING` continúa abierto hasta prueba autenticada real.

# FASE ACTIVA APROBADA — CODE GRAPH / ARQUITECTURA / PROGRAMACIÓN AUTÓNOMA
Apertura: 2026-09-10. Esta fase no invalida el cierre local anterior; añade capacidades nuevas autorizadas exclusivamente dentro del Wordflow. Ledger detallado: `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`.

## 1 — Raíz anclada de CODE GRAPH
Se debe crear dentro del Wordflow un workspace canónico para recibir archivos y componentes. El grafo debe representar por nodos/aristas: archivo fuente, requisitos extraídos, capacidades, tareas, dependencias, destino arquitectónico, agente owner/reviewer, sandbox, tests, evidencia, deployment, GAPs, checkpoint y estado. No será un orquestador paralelo: debe consumir el contrato `tel.workflow/v4`, usar el fleet existente y persistir en Crazy Wall.
Estado: `G-001 GAP_OPEN`.

## 2 — Ask Council + auditoría de cada archivo
Todo archivo recibido se audita antes de programar: tipo/formato, contenido, arquitectura, interfaces, dependencias, capacidades, riesgos, posibles comportamientos inseguros, intención, procedencia y compatibilidad. Ask Council puede razonar sobre alternativas; el resultado se normaliza a schema determinista antes de producir acciones.
Estado: `G-002 GAP_OPEN`.

## 3 — Generación de tareas de code
La arquitectura extraída se descompone en tareas atómicas. Cada tarea tendrá `task_id`, dependencia, prioridad, capability, rol/owner, entradas, salidas, destino candidato, sandbox requerido, tests, evidencia, retry/idempotency y estado. Deben distinguirse explícitamente las tareas entregadas por el Director de las generadas automáticamente.
Estado: `G-003 CLOSED_VERIFIED_LOCAL`.
Implementación: `runtime/src/core/code_task_graph.py` blob `91fd7779b2e8c27e3dd7f282847df1e2e4ab4f62`; tests `runtime/tests/test_code_task_graph.py` blob `882eb17b4289c747adf3850407e8a6a13b80ae65`; reutiliza `runtime/src/core/dag_engine.py` blob `ed4361e9e2ca93e6744f9946d2334bf55b3ef63a`. Evidence: `wordflow_loop/evidence/G003_TASK_GRAPH_2026-09-10.json`. Verificación local equivalente: `PASS_5_OF_5_ASSERTIONS`; no se reclama ejecución externa/GitHub Actions.

## 4 — Decisión de ubicación en la arquitectura YAIWES
El sistema estudiará función y límites del código para elegir entre: A Kernel; B Extension Kernel; C Reasoning Layer; D Wordflow en la cadena del agente; E Pool; F Tools; G otra ubicación justificable. La decisión usa privilegio, lifecycle, estado, latencia, acoplamiento, seguridad, dependencias y capacidad; nunca solo nombre de archivo.
Estado: `G-004 GAP_OPEN` — siguiente nodo 1×1.

## 5 — Investigación técnica antes de crear code
Política obligatoria `REUSE > PATCH > ADAPT > GENERATE`. Antes de crear se investigan librerías Python/YAML/schema/RAG/grafo/seguridad/colas/sandbox/deploy pertinentes. Cuando haya selección de biblioteca, comparar hasta 10 opciones útiles registrando fuente, licencia, compatibilidad, mantenimiento, riesgo e integración.
Estado: `G-005 GAP_OPEN`.

## 6 — Creación de code nuevo
Solo cuando no exista pieza reutilizable adecuada. El code nuevo debe ser mínimo, modular, tipado, idempotente, fail-closed, observable, testeable y conectado exclusivamente por el Enchufe Universal Fables/Ficha. Ninguna salida LLM puede ejecutar o desplegar sin gates.
Estado: `G-006 GAP_OPEN`.

## 7 — Archivo recibido que ya contiene code ejecutable
Analizar antes de reescribir. Puede reutilizarse, parchearse o adaptarse. Si debe copiarse/moverse se usan motores canónicos inmutables. Cambio a `.py`, YAML o lenguaje mixto solo cuando el contrato de destino lo requiera y preservando source/provenance.
Estado: `G-007 GAP_OPEN`.

## 8 — Seguridad y neutralización
Antes de ejecutar, inspeccionar código y dependencias. Conducta maliciosa o insegura se bloquea. Si se puede conservar funcionalidad mediante sustitución benigna explícita, se documenta y valida; nunca se ejecuta primero una acción peligrosa para después corregirla.
Estado: `G-008 GAP_OPEN`.

## 9 — Componente sin valor
Si no mejora capacidades, duplica sin beneficio, empeora seguridad/mantenibilidad o no puede cablearse con valor, se marca `NO_VALUE_GAP`. Debe producir justificación `.md`, evidencia, posibles alternativas y quedar para revisión del Director.
Estado: `G-009 GAP_OPEN`.

## 10 — Watchdog horario del Wordflow
Cada hora auditar tareas, GAPs, bloqueos, DAG/grafo, agentes, router, sandbox, evidencias y coherencia de STATE/CHECKPOINT/HANDOFF/README. Resolver únicamente lo autorizado y verificable. Nunca convertir ausencia de evidencia en PASS.
Estado: `G-010 CLOSED_VERIFIED`.

## 11 — Recepción de componentes y motores de copiar/mover
Entrada obligatoria `source + destination`. El motor canónico se conserva byte-a-byte, ejecuta copia/movimiento con destino explícito, hash/read-back y fail-closed. Después se analiza el componente y se cablea en el destino que determine la arquitectura. `Core kernel Yaiwes/` y otros repos se usan como fuentes de lectura/adquisición; no son destinos de escritura de esta fase.
Estado: `G-011 GAP_OPEN`.

## 12 — Listas de descarga/extracción
El LOOP debe aceptar una lista de componentes con URL/fuente y destino explícito, convertirla en cola y usar motores de descarga/extracción. Reglas: no LFS, no force, CRC/hash, bloqueo de rutas inseguras, persistencia de estado y read-back antes de PASS.
Estado: `G-012 GAP_OPEN`.

## 13 — Fuentes de verdad del LOOP
Debe mantener y reconciliar: mapa/diagrama; HANDOFF; tareas generadas; tareas del Director; Crazy Wall BITÁCORA/STATE/CHECKPOINT/PLAN; Schema/DSL/DAG/Pipeline; evidencias y GAP ledger. Una discrepancia de estado abre GAP en vez de elegir silenciosamente una versión.
Estado: `G-013 GAP_OPEN`.

## 14 — `agente-readme-memoria.md` de cada agente
Los 18 agentes tendrán memoria operativa versionada: rol, capacidades, restricciones, contratos, fuentes autorizadas, gates, evidence format, errores aprendidos y mejoras aprobadas. Se carga antes del trabajo y solo se perfecciona con aprendizaje verificado.
Estado: `G-014 GAP_OPEN`.

## 15 — 12 GOALS entrada/salida + Council + simulaciones
Cada capacidad nueva tendrá 12 gates/checks de entrada y 12 de salida, más Council/Ask Council, simulaciones, refutación y cross-check. LLM puede contribuir al razonamiento; estado, gates y aceptación final deben ser deterministas.
Estado: `G-015 GAP_OPEN`.

## 16 — Conversión de arquitectura Chat A ↔ Chat B
Buscar en documentos del proyecto el proceso existente señalado por el Director. Reutilizar/adaptar si existe. Si las búsquedas por nombre, contenido y documentos no lo localizan, registrar `NOT_FOUND` con evidencia antes de diseñar un equivalente nuevo.
Estado: `G-016 GAP_IN_RESEARCH`.

## 17 — Despliegue determinista
Revisar y adaptar pipeline existente. Cadena requerida: `validate → prepare/build → sandbox → tests → reviewer independiente → promote → checkpoint → rollback/compensation`. Ninguna salida generativa se despliega directamente.
Estado: `G-017 GAP_OPEN`.

## 18 — Enchufe Universal Fables único
Confirmar físicamente código canónico + Ficha/Contract. Todo módulo nuevo se integra a través de ese ABI/plug; prohibido crear buses o rutas de integración paralelas.
Estado: `G-018 GAP_IN_RESEARCH` — búsquedas actuales dentro del LOOP no han producido source proof exacto; no se crea sustituto.

## 19 — Auditoría global del Wordflow
Inventariar capacidades existentes y encontrar duplicados, piezas huérfanas, rutas rotas, documentación obsoleta, code no utilizado y GAPs reales. Regla: no rehacer trabajo ya verificado.
Estado: `G-019 GAP_OPEN`.

## 20 — 12 direcciones de comunidad/desarrollo
Crear catálogo de al menos 12 fuentes verificadas para investigación de arquitectura/programación. Debe indicar URL, tema, autoridad/uso y cuándo un agente debe consultar la fuente antes de decidir.
Estado: `G-020 CLOSED_VERIFIED` — `wordflow_loop/research/community_sources.json` blob `5c03a6a13b5df868f21eb6f744fcc20489c4d183`.

## 21 — Cola + ejecución paralela
Implementar/usar prioridades, dependencias DAG, fan-out/fan-in, pools por concern, dedup, idempotency keys, límites de concurrencia y backpressure. Solo nodos sin dependencia entre sí corren en paralelo; tareas bloqueadas esperan evidencia de sus dependencias.
Estado: `G-021 GAP_OPEN`.

## 22 — Sandbox → segundo agente → deploy
Antes de ejecutar code candidato: sandbox con límites de filesystem/network/time/memory. Después un agente distinto valida tests/evidence. Solo entonces gate determinista de promoción/deployment.
Estado: `G-022 GAP_OPEN`; el descriptor actual no prueba aislamiento físico.

## 23 — Hugging Face: dataset + skills bridge
Verificar con acceso/conector real los datasets, modelos, Spaces y skills disponibles. No asumir acceso a secretos por existir referencias. Crear bridge determinista que inyecte recursos/skills aprobados antes de la tarea sin exponer tokens.
Estado: `G-023 GAP_IN_RESEARCH`.

## 24 — LLM solo para razonamiento
Contracts, scheduler, DAG, routing, FSM, estado, gates, hash, sandbox y deployment serán deterministas. LLM se permite en análisis, síntesis, generación, Council o decisiones semánticas, pero su salida siempre se valida y no posee permiso implícito de ejecución.
Estado: `G-024 GAP_OPEN`.

## 25 — Patrones del documento MAVIS-PARALLEL-100X
Evaluar 1×1: pool persistente, priority queue, LRU/mmap, smart batching, streaming/backpressure, asyncio.Queue pipeline, dedup, Job ABI, registry/factory/DI/event bus/middleware/FSM/checkpoints/audit/tests/version/sandbox/capability routing. Sus multiplicadores de rendimiento quedan como hipótesis hasta benchmark local.
Estado: `G-025 GAP_OPEN`.

## 26 — Patrones del documento MAX-SYSTEM-100X-FINAL-1
Evaluar 1×1: fan-out/fan-in, batching, sharding, idempotency+DLQ, outbox+CDC, multi-pool, durable execution, recovery, multi-sandbox y memoria persistente. Se debe preferir la fundación LOOP existente antes de incorporar infraestructura nueva.
Estado: `G-026 GAP_OPEN`.

## 27 — Graphiti
Localizado en `maxbry123-commits/osquestador-auditor/graphiti`. Investigación inicial: grafo temporal/contextual para agentes con provenance por episodios, actualizaciones incrementales, retrieval híbrido, tipos Pydantic, MCP y FastAPI. Candidato para memoria/provenance/contexto de arquitectura y tareas; no reemplaza el scheduler DAG.
Estado: `G-027 GAP_IN_RESEARCH`.

## 28 — Graphology
Localizado en `maxbry123-commits/osquestador-auditor/graphology`. Investigación inicial: Graph object JS/TS, algoritmos/layout/traversal/eventos, usado por Sigma.js. Candidato para estructura/visualización interactiva del mapa de tareas; no durable execution.
Estado: `G-028 GAP_IN_RESEARCH`.

## 29 — Planificación organizada de tareas
Investigar piezas existentes en el repo auditor (Dagster, Prefect, Argo Workflows, Inngest, Trigger.dev, Restate, Airflow, `orchestrator`) y compararlas con la fundación Wordflow ya existente (LangGraph/Temporal/Prefect/Hatchet/redun históricos). Prohibido añadir otro orquestador si no cierra una capacidad no cubierta.
Estado: `G-029 GAP_IN_RESEARCH`; para G-003 se decidió REUSE del DAG local, no añadir orquestador.

## 30 — Crazy Wall compartido por agentes
Los agentes deben compartir un estado lógico sin pisarse: task ownership, node ownership, versión/checkpoint, idempotency y reglas de merge/conflict. Al cerrar un grupo de GAPs/tareas se conserva evidencia/historial y se abre el siguiente grupo. El operador/supervisor reconcilia cada hora.
Estado: `G-030 GAP_OPEN`.

# Investigación inicial registrada
- `osquestador-auditor` contiene Graphiti y Graphology, además de candidatos GraphRAG/FalkorDB/Neo4j y motores de planificación/visualización. Presencia ≠ selección.
- Skill canónico de motores leído: `COPY_ONLY / IMMUTABLE_MOTORS`, allowlist exacta de 7 archivos, blobs fijos, destino explícito, no LFS, no force y read-back obligatorio.
- Fuente canónica indicada por el skill: `maxbry123-commits/frontend/main/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`.
- `runtime/src/core/dag_engine.py` ya cubre DAG topológico determinista, ciclos y batches paralelos; G-003 lo reutiliza.

# Persistencia y reglas de esta fase
- GAP ledger: `Crazy Wall Orquestador/GAPS-INVESTIGACION-CODE-GRAPH-20260910.md`.
- STATE: `Crazy Wall Orquestador/STATE.json`.
- BITÁCORA: `Crazy Wall Orquestador/BITACORA-CRAZY-WALL.md`.
- CHECKPOINT/HANDOFF/PLAN se actualizan cuando cambie el nodo o cierre un grupo.
- Ningún GAP se cierra por presencia de archivo; requiere investigación + decisión + implementación cuando aplique + test/simulación + evidencia/read-back.
- No escribir ni modificar nada fuera de `➡️📂 Wordflow LOOP Yaiwes/`.
