# PLAN DE TRABAJO — COMPONENTES YAIWES

## Alcance fijo
Destino de auditoría: `Core kernel Yaiwes/`.
Integración destino: estructura canónica bajo `Agente Yaiwes principal/`, determinada siempre leyendo `Readme arquitectura Yaiwes/README.md` antes de mover código.

## Lista pendiente de 20 nodos raíz
1. Componentes recuperados A
2. Componentes recuperados B
3. Download code Yaiwes
4. Download code
5. Metodo de trabajo
6. Método de trabajo
7. Refactoria
8. TASK-GAPS
9. agente-yaiwes
10. agents
11. code-programming-engine
12. control-layer
13. extensions
14. groups
15. loop_catalog.json
16. memory
17. scripts
18. tools
19. wordflow
20. workflows archivados 2026-09-04

## Regla de componente real
Un componente es un agente o software open source descargado. Carpetas contenedoras, README, ZIP, `.keep`, documentación y basura auxiliar no cuentan por sí solos. Cada nodo raíz se recorre recursivamente y los componentes reales se deduplican.

## Paso 1 — X-Ray y clasificación
1. Leer INPUT_BLOCK literal sin reinterpretar.
2. GOALS 12/12.
3. Prioridades.
4. Plan y cola 1×1.
5. Auditar código fuente real del componente, no basarse en su README.
6. Identificar función, objetivo y microflujo horizontal.
7. Clasificar A/B/C con evidencia; GAP/NO_DETERMINABLE si no hay prueba suficiente.
8. Verificar/refutar; si falla, LOOP sin escalar.

### Opciones A/B/C
- A: agente/subagente autónomo con objetivo, estado, herramientas y ciclo de vida.
- B: workflow/orquestador/pool con secuencia, routing, ejecución o conjunto intercambiable de ejecutores.
- C: capacidad modular determinista/híbrida del kernel; código primero, LLM solo si está justificado.

## Paso 2 — Integración física
1. Leer siempre `Readme arquitectura Yaiwes/README.md` y validar ubicación exacta.
2. Crear el nuevo Wordflow/capacidad en `Agente Yaiwes principal/`.
3. MOVER, no copiar, únicamente archivos de código útiles desde el componente aprobado.
4. No mover README upstream, ZIP, docs, ejemplos basura ni artefactos auxiliares innecesarios.
5. Crear README nuevo propio del Wordflow Yaiwes.
6. Cablear siempre mediante Universal Plugin Bus v2 + Ficha Contract v2: contrato I/O, adapter, registry, seguridad, evidencia, telemetría, health y failover.
7. Después del movimiento ejecutar 10 pasadas X-Ray: corrección, determinismo, contratos, concurrencia, errores/retries, rendimiento, recursos, seguridad, observabilidad y tests.
8. Aplicar mejoras solo con evidencia; volver al LOOP ante cualquier GAP.

## Paso 3 — Cierre y persistencia
1. Verificar origen→destino y ausencia de duplicación accidental.
2. Verificar cableado, contratos, imports y tests.
3. Repetir checks reales hasta 10× cuando puedan ser inestables.
4. Auditar instrucciones 3 veces.
5. Hacer 3 refutaciones de cumplimiento.
6. Cross-check global.
7. Actualizar bitácora, `state.json` y `CHECKPOINT.json`.
8. Cerrar únicamente con evidencia: `VERIFIED_CLOSED`; sin evidencia = GAP.

## Cadena LOOP obligatoria
`SCHEMA/CONTRATO SYSTEM ➡️ WATCHDOG/SENTINELA ➡️ INPUT literal ➡️ GOALS 12/12 ➡️ prioridades ➡️ plan ➡️ cola 1×1 ➡️ verifica/refuta + soluciones ➡️ analiza ➡️ GAP? RESEARCH ➡️ auditor soluciones ➡️ ejecuta delta ➡️ CODA/PRELUDE persistencia ➡️ goals + council ➡️ investigación intensiva ➡️ refutaciones ➡️ cross-check ➡️ checklist ➡️ salida`.

## Estado inicial
- Nodo raíz activo: `Componentes recuperados A`.
- Componente aprobado para Paso 2: `APScheduler`.
- Estado: `READY_FOR_STEP_2`.

<!-- YAIWES_BATCH5_STATUS_20260906 -->
## Lote activo de 5 — estado verificable
1. Ajv — **VERIFIED_CLOSED** — C — destino `definition-registry/schema-contracts/ajv/` — move `95713304...` — run `34061366845` 10× PASS.
2. Apache-APISIX — **ACTIVE_LOOP** — B — destino `mesh-routing-collaboration/apisix-api-gateway/` — Paso 1 X-Ray cerrado; MOVE/runtime OpenResty pendientes.
3. Apache-Airflow — **PENDING** — B — destino propuesto `execution-orchestration/dag-executor/apache-airflow/`.
4. Argo-Workflows — **PENDING** — B — destino propuesto `execution-orchestration/dag-executor/argo-workflows/`.
5. Azure-Durable-Functions — **PENDING** — B — destino propuesto `execution-orchestration/state-machine-executor/azure-durable-functions/`.

Regla del lote: cada componente mantiene evidencia/estado independiente; el lote solo cierra `5/5 VERIFIED_CLOSED`.
