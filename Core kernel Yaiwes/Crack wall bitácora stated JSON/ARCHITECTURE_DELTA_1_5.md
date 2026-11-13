## 26. Integraciones VERIFIED_CLOSED — componentes 1–5 · 2026-09-07

Esta sección es un delta aditivo; preserva íntegramente la arquitectura anterior. Los cinco componentes fueron revalidados contra código real, integrados en destinos modulares de `Agente Yaiwes principal/`, conectados mediante Fables / Ficha Contract v2 / Universal Plugin Bus y verificados después del MOVE físico desde `Core kernel Yaiwes/Componentes recuperados A/`.

| Componente | A/B/C | Destino canónico | Función dentro de YAIWES | Integración |
|---|---|---|---|---|
| APScheduler | B | `execution-orchestration/task-classifier-scheduler/` | scheduling sync/async, jobs, ejecutores y control temporal | adapter + Ficha v2 + WIRING + `UniversalPluginBus.enchufar()` |
| AWS-Step-Functions-DS-SDK | B | `execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk/` | composición de State/Chain/Graph y definiciones ASL | adapter + Ficha v2 + WIRING + `UniversalPluginBus.enchufar()` |
| Ajv | C | `definition-registry/schema-contracts/ajv/` | validación determinista JSON Schema/JTD | bridge/adapter + Ficha v2 + WIRING + `UniversalPluginBus.enchufar()` |
| Apache APISIX | C | `mesh-routing-collaboration/apisix-api-gateway/` | API gateway, routing, plugins y upstreams | adapter fail-closed + Ficha v2 + WIRING + `UniversalPluginBus.enchufar()` |
| Apache Airflow | B | `execution-orchestration/dag-executor/apache-airflow/` | DAG runtime, scheduling y ejecución/orquestación de tareas | adapter + Ficha v2 + WIRING + `UniversalPluginBus.enchufar()` |

### Evidencia de cierre del lote 1

- MOVE/deduplicación física: commit `fe25fc78e38f24c14d64fd5b51ce0feab668a102`; los cinco directorios de código recuperado fueron retirados después de verificar sus destinos. Los ZIP de recuperación no se integraron ni movieron.
- Licencias/NOTICE upstream fueron preservados en cada destino cuando correspondía.
- Verificación conjunta post-MOVE: workflow `YAIWES First Five Plugin Bus Verify`, run `34090968435`, `SUCCESS`.
- El gate conjunto ejecuta el montaje de los cinco mediante `UniversalPluginBus.enchufar()` diez veces y exige registro `ACTIVE`, evidencia L2, heartbeat/health, activación y telemetría.
- Las pruebas runtime específicas previas de APScheduler, AWS Step Functions, Ajv, APISIX y Airflow se conservan como evidencia complementaria; presencia de carpeta o Ficha por sí sola no cuenta como cierre.

**Estado arquitectónico del lote:** `VERIFIED_CLOSED` para componentes 1–5. Cualquier regresión posterior reabre el nodo correspondiente en modo fail-closed.
