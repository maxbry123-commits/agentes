# YAIWES — 24 CODA global

## Objetivo
Integrar 24 métodos internos distintos como una capacidad del agente YAIWES para resolver tareas difíciles con cola durable y paralelismo controlado. No todos los componentes deben convertirse en agentes: se conserva cada workflow determinista cuando aporta memoria, planificación, validación, persistencia o control; los orquestadores se pueden usar como especialistas/subagentes.

## Arquitectura canónica

`TASK → durable queue → branch claim → CODA-01 → ... → CODA-24 → universal plug → verified result`

Cada CODA mantiene este contrato transversal:

`input previo → research API/MCP → contexto aprendido → workflow interno propio → evidencia → checkpoint SQLite/WAL → handoff`

Para tareas independientes:

`QUEUE → [branch A: 24 CODA] ∥ [branch B: 24 CODA] ∥ [branch C: 24 CODA] → resultados verificados`

La unidad paralela es una rama independiente; dentro de cada rama se conserva el orden 01→24 para no romper la continuidad causal.

Cuando una tarea queda bloqueada o produce evidencia conflictiva, Hybrid V9 permite otra forma de paralelo:

`NORMAL CHAIN → structured escalation gate → [candidate A ∥ candidate B ∥ candidate C] → deterministic fan-in → verified winner → checkpoint/handoff`

La colmena se usa solamente para varias estrategias del **mismo problema**. Tareas independientes nunca compiten por un ganador.

## Roles de los 24 componentes
- 01 orquestación dinámica — subagente
- 02 recuperación de tablero/estado — servicio de estado
- 03 normalización de decisiones — planner gate
- 04 coordinación de especialistas — subagente
- 05 inicialización de task manager — servicio de tareas
- 06 persistencia verificada de artefactos — servicio de persistencia
- 07 supervisión resiliente MCP — servicio de conexión
- 08 steering/cola de directivas — servicio de coordinación
- 09 fan-out de subagentes — subagente
- 10 descomposición determinista de objetivos — planner
- 11 memoria incremental y fallos previos — memoria
- 12 loop supervisor/executor durable — subagente
- 13 auditoría JSON + Markdown — auditoría
- 14 preprocesamiento local hacia MCP — adapter local
- 15 memoria persistente y aprendizaje de patrones — memoria/aprendizaje
- 16 máquina de estados/orquestación por fases — subagente
- 17 llamada LLM resiliente — model gateway
- 18 dispatcher/control-plane MCP — control-plane
- 19 misiones persistentes — subagente
- 20 agente iterativo con herramientas MCP — subagente
- 21 scheduler DAG por dependencias/prioridad — planner DAG
- 22 higiene de memoria/anchors — higiene de estado
- 23 ciclo planificar→observar→resumir→evaluar — subagente
- 24 atestación final y universal plug — finalizador

## Decisión workflow vs subagente
Mantener como workflows/servicios deterministas las capacidades 02,03,05,06,07,08,10,11,13,14,15,17,18,21,22,24. Exponer como especialistas cuando la tarea lo requiera 01,04,09,12,16,19,20,23. Esta separación reduce competencia innecesaria y conserva determinismo.

## Política de escalado de problema — V9

La decisión de abrir colmena no depende de un voto del LLM. `yaiwes_coda_hybrid_v9.escalation_decision()` solo usa estado estructurado. Puede escalar ante `BLOCKED`, `FAILED`, `UNRESOLVED`, `LOW_CONFIDENCE`, `NO_PROGRESS`, `CONFLICT`, una cadena incompleta, investigación incompleta, Universal Plug ausente, falta de progreso o evidencia conflictiva.

1. Ejecutar la ruta determinista normal.
2. Evaluar el gate estructurado.
3. Si no existe GAP, seguir la cola normal.
4. Si existe GAP verificable, preparar al menos dos estrategias seguras para el mismo problema.
5. Ejecutarlas en paralelo con `run_hive_candidates()`.
6. Comparar resultados por evidencia durable, nunca por voto simple del LLM.
7. Persistir solo un resultado `RESOLVED_VERIFIED` como ganador y continuar el handoff.

## Fan-in determinista

`deterministic_fan_in()` usa, en orden, evidencia de rama completada, cierre 24-CODA, Universal Plug, 24 componentes, workflows completados/reales, 24 ciclos de research y cantidad de evidencias ejecutadas. Un resultado parcial no puede superar uno completamente verificado.

En empate exacto se usa `candidate_id` ascendente como desempate estable. La misma evidencia debe producir el mismo ganador al repetirse.

## Research y conexiones
Research es obligatorio en cada CODA de producción. Solo se admite un endpoint explícitamente configurado mediante `YAIWES_RESEARCH_MCP_URL` o `YAIWES_RESEARCH_API_URL`. El discovery de plugins es metadata-only: no instala ni ejecuta herramientas desconocidas automáticamente.

## Persistencia
V8 usa SQLite/WAL, workflow idempotente, checkpoints transaccionales, recuperación desde el último componente confirmado, cola durable y leases. V9 reutiliza V8; no crea un segundo motor de estado. Un reinicio no debe repetir enlaces ya comprometidos.

## Handoff de activación
Contrato legible por máquina: `YAIWES-HANDOFF-V9.json`.

Entrypoints:
- lineal: `yaiwes_coda_bus_v8.run_coda_chain`
- cola de tareas independientes: `yaiwes_coda_hybrid_v9.run_independent_queue`
- colmena del mismo problema: `yaiwes_coda_hybrid_v9.run_hive_candidates`
- gate de escalado: `yaiwes_coda_hybrid_v9.escalation_decision`
- contrato runtime: `yaiwes_coda_hybrid_v9.activation_contract`

El entrypoint de producción con research debe conservar el gate V8.1/V7.1 autorizado por API/MCP. El cierre exige 24 workflows internos, 24 research cycles `EXECUTED`, estados liberados y Universal Plug después del componente 24.

## Fail closed
No declarar cierre si falta un componente, research no ejecutó, un workflow no terminó, un estado no fue liberado, se rompe continuidad o el Universal Plug no valida. Sin endpoint real API/MCP configurado, producción debe fallar cerrado en lugar de simular research. No ejecutar plugins desconocidos. No utilizar el componente 24 como solucionador.

## Reparación YAIWES 15
El GAP de `_load_session` que podía consumir la fila SQLite dos veces fue reparado quirúrgicamente antes de esta V9. La lectura debe ejecutar un único `fetchone()` y convertir esa misma fila.

## Componentes seleccionados para integración UI YAIWES
Se deben copiar con procedencia y verificación hash los componentes 08, 11, 12, 15, 16, 21, 22 y 23 al repo `frontend`, raíz `UI YAIWES/`. La copia no implica activación automática; frontend debe consumirlos mediante adapters seguros y contratos explícitos.
