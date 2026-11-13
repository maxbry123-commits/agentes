# Wordflow — Task Classifier Scheduler / APScheduler

## Capacidad incorporada
APScheduler se integra como backend determinista de scheduling y cola de jobs para `execution-orchestration/task-classifier-scheduler`.

## Clasificación
**B — workflow/orquestador + pool de ejecución.** No es un agente autónomo. Su responsabilidad es transformar definiciones de tareas/schedules en jobs ejecutables mediante scheduler sync/async, data stores, event brokers, triggers y job executors.

## Microflujo
`Task definition ➡️ trigger/schedule ➡️ scheduler ➡️ data store ➡️ job adquirido ➡️ executor ➡️ resultado/evento ➡️ estado/evidencia YAIWES`.

## Código movido
- `apscheduler/`: paquete runtime upstream proveniente de `Core kernel Yaiwes/Componentes recuperados A/APScheduler/APScheduler/src/apscheduler/`.
- `tests/`: suite de código de pruebas upstream para verificación del backend.
- No se trasladan README upstream, docs, examples, ZIP ni artefactos de publicación.

## Enchufe universal
`WIRING.json` conecta este Wordflow con el bus central `kernel-principal/extension-kernel/plugin-bus/universal_plugin_bus_v2_integrated.py` y su `ficha_contract_v2.py`.
`ficha.apscheduler.v2.json` permanece en estado `testing` y exige `director_gate`; no se declara activo hasta completar validación, seguridad y evidencia runtime.

## API YAIWES
- `adapter.py:build_scheduler(async_mode=False|True, **kwargs)`
- `adapter.py:build_task_defaults(**kwargs)`
- `adapter.py:capability()`

## Regla de mejora 10× posterior al movimiento
1. Corrección funcional.
2. Determinismo y side effects.
3. Contratos I/O y ficha.
4. Concurrencia sync/async.
5. Errores, retries, deadlines y leases.
6. Rendimiento y latencia.
7. CPU/memoria/almacenamiento.
8. Seguridad/sandbox/mount guard.
9. Observabilidad, eventos, métricas y evidencia.
10. Tests, integración y cierre E2E.

Cualquier GAP vuelve al LOOP. Cierre permitido solo con `VERIFIED_CLOSED` y evidencia de ruta/SHA/test/log.
