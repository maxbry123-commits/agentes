# HANDOFF — YAIWES 24 COMPONENTES / WORKFLOW TRANSVERSAL V9

## Objetivo
Documento único de handoff para los 24 componentes CODA de YAIWES. Conserva el orden causal 01→24, la función de cada eslabón, su microflujo transversal y el cierre por Universal Plug.

## Workflow global

`TASK → durable queue → claim → YAIWES-01 → YAIWES-02 → YAIWES-03 → YAIWES-04 → YAIWES-05 → YAIWES-06 → YAIWES-07 → YAIWES-08 → YAIWES-09 → YAIWES-10 → YAIWES-11 → YAIWES-12 → YAIWES-13 → YAIWES-14 → YAIWES-15 → YAIWES-16 → YAIWES-17 → YAIWES-18 → YAIWES-19 → YAIWES-20 → YAIWES-21 → YAIWES-22 → YAIWES-23 → YAIWES-24 → UNIVERSAL PLUG → VERIFIED RESULT`

Contrato transversal obligatorio en cada eslabón:

`input previo → research API/MCP → contexto aprendido → workflow interno propio → evidencia → checkpoint SQLite/WAL → handoff al siguiente`

## Los 24 componentes

1. **YAIWES-01 — Orquestación dinámica / subagente.** Función: recibe el objetivo global, organiza la ejecución y decide qué capacidad necesita continuar. Microflujo: `objetivo → leer contexto/estado → research → seleccionar estrategia → ejecutar orquestación → verificar salida → checkpoint → 02`.
2. **YAIWES-02 — Recuperación de tablero/estado.** Función: reconstruye el estado persistido de la tarea y sus pasos. Microflujo: `handoff 01 → cargar estado → ordenar tareas/estado previo → detectar continuidad → devolver snapshot consistente → checkpoint → 03`.
3. **YAIWES-03 — Normalización de decisiones / planner gate.** Función: convierte decisiones del planner a una forma determinista y comparable. Microflujo: `snapshot → recibir decisión → normalizar → validar campos/estado → aceptar o fail-closed → checkpoint → 04`.
4. **YAIWES-04 — Coordinación de especialistas / subagente.** Función: coordina capacidades especializadas sin romper el estado común. Microflujo: `decisión normalizada → seleccionar especialista → entregar contexto acotado → recibir resultado → validar evidencia → checkpoint → 05`.
5. **YAIWES-05 — Inicialización de task manager.** Función: crea y mantiene la estructura operativa de tareas. Microflujo: `resultado 04 → inicializar/recuperar task manager → registrar tareas → asignar estados → emitir siguiente unidad → checkpoint → 06`.
6. **YAIWES-06 — Persistencia verificada de artefactos.** Función: conserva resultados y artefactos con verificación antes/después. Microflujo: `artefacto → validar origen → persistir temporal → verificar integridad → commit atómico → evidencia → checkpoint → 07`.
7. **YAIWES-07 — Supervisión resiliente MCP.** Función: mantiene una sesión MCP autorizada y recuperable. Microflujo: `necesidad de conexión → validar MCP autorizado → abrir/reanudar sesión → health/retry acotado → registrar estado → checkpoint → 08`.
8. **YAIWES-08 — Steering / cola de directivas.** Función: recibe y drena directivas de coordinación asociadas al trabajo activo. Microflujo: `estado 07 → leer cola/directivas → ordenar/aplicar señales permitidas → acumular steering → vaciar cola procesada → checkpoint → 09`.
9. **YAIWES-09 — Fan-out de subagentes.** Función: delega subtareas independientes a especialistas cuando procede. Microflujo: `directivas → dividir trabajo independiente → lanzar especialistas → recoger resultados → aislar ramas → validar → checkpoint → 10`.
10. **YAIWES-10 — Descomposición determinista de objetivos.** Función: transforma el objetivo en unidades ordenadas y verificables. Microflujo: `objetivo/contexto → descomponer → definir dependencias → ordenar pasos → validar plan → checkpoint → 11`.
11. **YAIWES-11 — Memoria incremental y fallos previos.** Función: registra progreso, deduplica pasos y conserva intentos fallidos relevantes. Microflujo: `paso ejecutado → deduplicar → guardar historial → analizar progreso/error → actualizar failed-attempts → checkpoint → 12`.
12. **YAIWES-12 — Loop supervisor/executor durable.** Función: mantiene un ciclo de supervisión, ejecución segura, recuperación e idempotencia. Microflujo: `snapshot → recuperar lease/estado → plan supervisor → validar → ejecutar unidad acotada → validar delta → commit/retry → checkpoint → 13`.
13. **YAIWES-13 — Auditoría JSON + Markdown.** Función: genera registro legible por máquina y por humano de cada transición. Microflujo: `estado/resultados → estructurar evento → escribir JSON → escribir resumen Markdown → comprobar consistencia → checkpoint → 14`.
14. **YAIWES-14 — Adapter local hacia MCP.** Función: prepara entradas locales antes de entregarlas a herramientas MCP autorizadas. Microflujo: `entrada → sanitizar/estructurar → mapear a contrato MCP → validar schema → enviar o fail-closed → registrar respuesta → checkpoint → 15`.
15. **YAIWES-15 — Memoria persistente y aprendizaje de patrones.** Función: guarda sesiones, resultados, conocimiento y patrones operativos reutilizables. Microflujo: `resultado previo → seleccionar save/load/pattern → SQLite → recuperar una sola fila válida cuando corresponda → actualizar conocimiento/patrón → checkpoint → 16`.
16. **YAIWES-16 — Máquina de estados / orquestación por fases.** Función: conduce el trabajo por fases con presupuesto y condiciones de salida. Microflujo: `estado → identificar fase → validar presupuesto → ejecutar agente/fase → medir resultado → avanzar/terminar → checkpoint → 17`.
17. **YAIWES-17 — Gateway LLM resiliente.** Función: encapsula llamadas de modelo con validación y manejo de fallos. Microflujo: `prompt/contexto → validar modelo/ruta → llamada autorizada → validar respuesta → retry acotado/fail-closed → checkpoint → 18`.
18. **YAIWES-18 — Dispatcher / control-plane MCP.** Función: enruta acciones permitidas al endpoint MCP correcto. Microflujo: `acción estructurada → validar política → resolver herramienta MCP → despachar → recoger respuesta → validar estado → checkpoint → 19`.
19. **YAIWES-19 — Misiones persistentes / subagente.** Función: sostiene una misión compleja a través de varios pasos sin perder estado. Microflujo: `misión → cargar estado persistente → ejecutar siguiente objetivo → evaluar progreso → persistir → repetir hasta condición terminal → checkpoint → 20`.
20. **YAIWES-20 — Agente iterativo con herramientas MCP.** Función: resuelve iterativamente usando únicamente conexiones permitidas. Microflujo: `objetivo → observar estado → decidir siguiente acción → herramienta MCP autorizada → observar resultado → actualizar contexto → checkpoint → 21`.
21. **YAIWES-21 — Scheduler DAG por dependencias/prioridad.** Función: elige de forma determinista la siguiente tarea ejecutable. Microflujo: `plan DAG → priorizar in-progress → filtrar pending con dependencias completas → ordenar por prioridad → elegir siguiente → checkpoint → 22`.
22. **YAIWES-22 — Higiene de memoria/anchors.** Función: elimina referencias inválidas, supersedidas o inconsistentes y conserva estado útil. Microflujo: `memoria actual → validar anchors → eliminar inválidos/supersedidos → deduplicar/archivar → emitir estado limpio → checkpoint → 23`.
23. **YAIWES-23 — Ciclo planificar→observar→resumir→evaluar.** Función: ejecuta un bucle de evaluación iterativa y recoge métricas/evidencia. Microflujo: `tarea → preparar contexto → planner → ejecución acotada → resumir → evaluar criterio → registrar métricas → checkpoint → 24`.
24. **YAIWES-24 — Atestación final / finalizador.** Función: comprueba que la cadena completa está cerrada y entrega al Universal Plug; no actúa como solucionador. Microflujo: `estado 23 → verificar 24/24 componentes → verificar 24 research cycles → verificar estados/evidencia/checkpoints → fail-closed si falta algo → atestar cierre → UNIVERSAL PLUG`.

## Paralelismo controlado

Tareas independientes:

`QUEUE → [rama A: 01→24] ∥ [rama B: 01→24] ∥ [rama C: 01→24] → resultados verificados`

Problema único bloqueado o con evidencia conflictiva:

`cadena normal → escalation gate estructurado → [candidato A ∥ candidato B ∥ candidato C] → deterministic fan-in → ganador RESOLVED_VERIFIED → checkpoint → reanudar cadena`

La decisión de escalar usa estado estructurado, no voto libre del LLM. En empate exacto, el desempate es estable por `candidate_id` ascendente.

## Research y aprendizaje operacional

Cada CODA de producción debe ejecutar research mediante API o MCP autorizado antes de su workflow interno. El aprendizaje se conserva fuera de los pesos del modelo mediante memoria, patrones, artefactos, checkpoints y estado persistente. El discovery de plugins es metadata-only; herramientas desconocidas no se ejecutan automáticamente.

## Persistencia y recuperación

V8 aporta SQLite/WAL, commits transaccionales por componente, idempotencia, cola durable y recuperación de leases. V9 reutiliza ese motor y añade escalado híbrido determinista; no crea un segundo motor de estado.

## Entrypoints canónicos

- Lineal: `yaiwes_coda_bus_v8.run_coda_chain`
- Cola paralela de tareas independientes: `yaiwes_coda_hybrid_v9.run_independent_queue`
- Colmena para el mismo problema: `yaiwes_coda_hybrid_v9.run_hive_candidates`
- Gate de escalado: `yaiwes_coda_hybrid_v9.escalation_decision`
- Contrato runtime: `yaiwes_coda_hybrid_v9.activation_contract`

## Condición de cierre

No declarar PASS final si falta un componente, si research no ejecutó en uno de los 24, si un estado no fue liberado, si falla continuidad, si falta evidencia/checkpoint o si el Universal Plug no valida.

## Referencias canónicas

- `README-GLOBAL-YAIWES-24-CODA.md`
- `YAIWES-HANDOFF-V9.json`
- `yaiwes_coda_bus_v8.py`
- `yaiwes_coda_persistence_v8.py`
- `yaiwes_coda_research_gate_v71.py`
- `yaiwes_coda_hybrid_v9.py`
