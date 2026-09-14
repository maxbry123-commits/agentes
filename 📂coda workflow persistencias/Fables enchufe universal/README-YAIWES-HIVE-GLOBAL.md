# YAIWES — 24 CODA + Hybrid Hive V9

## Objetivo

YAIWES usa 24 componentes como una cadena CODA durable. El modo normal es determinista y lineal; el paralelismo se usa de dos maneras distintas:

1. **Cola de tareas independientes:** varias tareas completas pueden recorrer su propia cadena de 24 CODA en paralelo.
2. **Colmena de resolución:** si una tarea queda bloqueada, sin progreso, con evidencia contradictoria o incompleta, varias estrategias seguras para el mismo problema pueden ejecutarse en paralelo y el resultado se integra con un árbitro determinista.

El sistema no convierte artificialmente los 24 componentes en agentes. Cada componente conserva su naturaleza original: subagente, planner, memoria, conexión, estado, auditoría, control-plane o finalizador.

## Flujo transversal

`TASK → QUEUE → 01 → 02 → ... → 24 → UNIVERSAL_PLUG`

Cuando aparece un GAP resoluble por colmena:

`NORMAL_CHAIN → STRUCTURED_ESCALATION_GATE → [candidate A ∥ candidate B ∥ candidate C] → DETERMINISTIC_FAN_IN → VERIFIED_WINNER → CHECKPOINT → NORMAL_CHAIN/HANDOFF`

Para tareas independientes:

`DURABLE_QUEUE → [TASK A: 01→...→24 ∥ TASK B: 01→...→24 ∥ TASK C: 01→...→24] → independent results`

## Catálogo de los 24 componentes

| # | Modo V9 | Función operativa |
|---|---|---|
| 01 | subagent | Orquestación autónoma y coordinación dinámica. |
| 02 | state_service | Recuperación del tablero persistente de tareas. |
| 03 | planner_gate | Normalización y validación del contrato del planner. |
| 04 | subagent | Coordinación jerárquica de especialistas. |
| 05 | task_service | Inicialización y composición del gestor de tareas. |
| 06 | persistence_service | Persistencia segura de recursos y hashes. |
| 07 | mcp_connection_service | Supervisión resiliente de sesiones MCP. |
| 08 | coordination_service | Steering/cola de instrucciones entre procesos. |
| 09 | subagent | Ejecución paralela de trabajadores con blackboard. |
| 10 | deterministic_planner | Descomposición determinista en milestones. |
| 11 | memory_service | Memoria incremental, deduplicación y registro de fallos. |
| 12 | subagent | Loop durable Supervisor/Executor con leases y recuperación. |
| 13 | audit_service | Bitácora estructurada y legible. |
| 14 | local_adapter | Adaptador local de preprocesamiento. |
| 15 | memory_learning_service | Memoria SQLite y aprendizaje operacional de patrones. |
| 16 | subagent | Orquestación por máquina de estados/fases. |
| 17 | model_gateway | Gateway resiliente para llamadas de modelo. |
| 18 | control_plane | Dispatcher/lifecycle de sesión y gates. |
| 19 | subagent | Misiones persistentes, memoria y failover de modelo. |
| 20 | subagent | Loop de modelo + herramientas MCP. |
| 21 | dag_planner | Scheduler por dependencias y prioridad. |
| 22 | state_hygiene_service | Higiene de estado, anchors y memoria acotada. |
| 23 | subagent | Loop iterativo Planner → resultado → resumen → siguiente paso. |
| 24 | finalizer | Verificación de continuidad y cierre hacia Universal Plug. |

## Política de selección

La ruta normal siempre intenta primero la cadena durable. La función `escalation_decision()` no consulta un LLM para decidir si hay que abrir colmena. Solo acepta señales estructuradas y auditables. Si no hay señal de GAP, no se crea fan-out.

Los componentes aptos para actuar como subagentes son: **01, 04, 09, 12, 16, 19, 20 y 23**. Los otros 16 componentes permanecen como etapas/servicios porque convertirlos en agentes aumentaría la no-determinación sin aportar una estrategia completa independiente.

## Fan-in determinista

`deterministic_fan_in()` ordena candidatos por un vector de evidencia durable:

1. rama completada;
2. cierre de 24 CODA;
3. Universal Plug validado;
4. 24 componentes presentes;
5. 24 workflows internos completados;
6. 24 workflows internos reales ejecutados;
7. 24 ciclos de investigación;
8. cantidad de investigaciones `EXECUTED`;
9. cantidad de workflows `COMPLETED`;
10. tamaño de evidencia.

Si dos candidatos empatan exactamente, gana el `candidate_id` lexicográficamente menor. Así el replay de la misma evidencia produce la misma decisión.

Una rama parcial nunca se declara ganadora verificada. El estado permanece `UNRESOLVED`.

## Persistencia y cola

V9 reutiliza V8; no crea un segundo motor de estado. Por tanto conserva:

- SQLite durable;
- WAL;
- commits transaccionales por componente;
- idempotencia por workflow/task id;
- recuperación después de interrupción;
- durable queue;
- lease recovery;
- ejecución paralela acotada.

## Investigación y herramientas

La investigación sigue perteneciendo al bus CODA/research gate: cada CODA debe volver a investigar cuando se use el gate de producción. V9 no sustituye ese gate.

Conexiones externas permitidas por el contrato: **MCP o API**. El descubrimiento de plugins es metadata-only y un plugin desconocido no se instala ni ejecuta automáticamente.

## Entrypoints

- Lineal: `yaiwes_coda_bus_v8.run_coda_chain`
- Cola paralela independiente: `yaiwes_coda_hybrid_v9.run_independent_queue`
- Colmena para un mismo problema: `yaiwes_coda_hybrid_v9.run_hive_candidates`
- Gate determinista de escalado: `yaiwes_coda_hybrid_v9.escalation_decision`
- Contrato legible por máquina: `yaiwes_coda_hybrid_v9.activation_contract`

## Reglas fail-closed

- No seleccionar ganador si la mejor rama no completa las condiciones durables mínimas.
- No usar la colmena para mezclar tareas independientes; esas van a `run_independent_queue()`.
- No usar el finalizador 24 como solucionador del problema.
- No reemplazar memoria, planner o estado por agentes LLM cuando su función ya es determinista.
- No ejecutar plugins desconocidos.
- No declarar investigación externa real si no existe una conexión API/MCP configurada y ejecutada.

## Activación por el agente YAIWES

1. Leer `YAIWES-HANDOFF-V9.json`.
2. Validar que existan exactamente los componentes 01..24.
3. Ejecutar la cadena V8 para el camino normal.
4. Evaluar `escalation_decision()` ante un GAP.
5. Si `escalate=false`, continuar cola normal.
6. Si `escalate=true`, crear dos o más estrategias seguras para el mismo problema y llamar `run_hive_candidates()`.
7. Aceptar únicamente `RESOLVED_VERIFIED` como ganador.
8. Persistir el resultado y continuar el handoff.
9. Finalizar en 24 y entregar al Universal Plug.

## Estado de la reparación de YAIWES 15

El GAP de lectura de sesión que consumía la fila SQLite dos veces fue corregido en `agentes/main` antes de V9. La implementación debe conservar la regla: obtener la fila una sola vez y luego convertirla, sin un segundo `fetchone()` sobre el mismo cursor.
