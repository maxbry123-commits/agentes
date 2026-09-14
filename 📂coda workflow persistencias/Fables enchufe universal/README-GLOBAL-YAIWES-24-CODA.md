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

## Roles de los 24 componentes
- 01 orquestación dinámica
- 02 recuperación de tablero/estado
- 03 normalización de decisiones
- 04 coordinación de especialistas
- 05 inicialización de task manager
- 06 persistencia verificada de artefactos
- 07 supervisión resiliente MCP
- 08 steering/cola de directivas
- 09 fan-out de subagentes
- 10 descomposición determinista de objetivos
- 11 memoria incremental y fallos previos
- 12 loop supervisor/executor durable
- 13 auditoría JSON + Markdown
- 14 preprocesamiento local hacia MCP
- 15 memoria persistente y aprendizaje de patrones
- 16 máquina de estados/orquestación por fases
- 17 llamada LLM resiliente
- 18 dispatcher/control-plane MCP
- 19 misiones persistentes
- 20 agente iterativo con herramientas MCP
- 21 scheduler DAG por dependencias/prioridad
- 22 higiene de memoria/anchors
- 23 ciclo planificar→observar→resumir→evaluar
- 24 atestación final y universal plug

## Decisión workflow vs subagente
Mantener como workflows deterministas las capacidades 02,03,05,06,07,08,10,11,13,14,15,17,18,21,22,24. Exponer como especialistas cuando la tarea lo requiera 01,04,09,12,16,19,20,23. Esta separación reduce competencia innecesaria y conserva determinismo.

## Política de escalado de problema
1. Ejecutar la ruta determinista normal.
2. Si existe GAP verificable, clasificar el problema.
3. Seleccionar solo especialistas compatibles.
4. Ejecutar ramas independientes en paralelo, nunca dos writers sobre el mismo estado/path.
5. Comparar resultados por evidencia, continuidad, tests y estado terminal; no por voto simple del LLM.
6. Persistir la decisión ganadora y continuar la cola.

## Research y conexiones
Research es obligatorio en cada CODA de producción. Solo se admite un endpoint explícitamente configurado mediante `YAIWES_RESEARCH_MCP_URL` o `YAIWES_RESEARCH_API_URL`. El discovery de plugins es metadata-only: no instala ni ejecuta herramientas desconocidas automáticamente.

## Persistencia
V8 usa SQLite/WAL, workflow idempotente, checkpoints transaccionales, recuperación desde el último componente confirmado, cola durable y leases. Un reinicio no debe repetir enlaces ya comprometidos.

## Handoff de activación
Entrada mínima: `task_id` único + payload JSON + registry canónico de 24 componentes + endpoint de research API/MCP autorizado.

Activación canónica: `yaiwes_internal_swarm_chain_v5.run_swarm(...)`.

Ese entrypoint debe pasar por `yaiwes_coda_research_gate_v81`, que reutiliza el broker auditado V7.1 y ejecuta el bus durable V8. El cierre exige 24 workflows internos, 24 research cycles `EXECUTED`, 24 estados `RELEASED` y universal plug después del componente 24.

Para múltiples tareas independientes usar `yaiwes_coda_research_gate_v81.run_parallel_tasks(...)`; cada worker reclama una tarea de la cola durable y ejecuta su propia cadena completa.

## Fail closed
No declarar cierre si falta un componente, research no ejecutó, un workflow no terminó, un estado no fue RELEASED, se rompe continuidad o el universal plug no valida. Sin endpoint real API/MCP configurado, producción debe fallar cerrado en lugar de simular research.

## Componentes seleccionados para integración UI YAIWES
Se deben copiar con procedencia y verificación hash los componentes 08, 11, 12, 15, 16, 21, 22 y 23 al repo `frontend`, raíz `UI YAIWES/`. La copia no implica activación automática; frontend debe consumirlos mediante adapters seguros y contratos explícitos.
