# Source Evolution Workflow — guía operativa

Este directorio es el espacio de trabajo controlado para evolucionar YAIWES. Se carga antes de ejecutar una tarea de evolución y complementa `YAIWES_EVOLUTION.md`; no sustituye los contratos, el DAG ni la autorización del Director.

## Secuencia de arranque

1. Leer este `README.md`, `YAIWES_EVOLUTION.md` y `EXTENSION_KERNEL_WIRING.json`.
2. Leer `../../../extensions/source-evolution-module/EVOLUTION_GOALS_50.yaml` y `evolution_dag.yaml`.
3. Consultar `CAPABILITY_INDEX.json` y el checkpoint más reciente; si faltan, ejecutar auditoría X-Ray sin mutar componentes.
4. Fijar una sola tarea, repositorio, rama, raíz destino, prohibiciones y evidencia de cierre.
5. Ejecutar investigación, Consilio, tres simulaciones y tres refutaciones.
6. Detenerse en `AWAITING_DIRECTOR`. La LLM no autoriza.
7. Tras autorización verificable, adquirir con `skills/research-download-chain/SKILL.md`.
8. Ejecutar cada carril mediante `microkernel/parallel_kernel.py` con límites independientes.
9. Cablear únicamente por Registry → Adapter → BUS → Schema.
10. Verificar pruebas individuales, E2E, hot-swap, rollback, SHA y lectura posterior.

## Reglas inmutables

- No borrar ni sobrescribir documentos o componentes.
- No reactivar workflows antiguos fallidos; una reparación usa un workflow nuevo y aislado.
- Código externo mayor de 100 líneas se copia desde fuente fijada; no se reescribe.
- Una URL repetida no es por sí sola un duplicado: comparar URL normalizada, commit, contenido y destino.
- Ningún carril puede ampliar el alcance de otro ni escribir su ledger.
- Un fallo se registra; no cancela carriles independientes. El cierre global permanece FAIL hasta resolverlo.
- El microkernel no concede sandbox de sistema: cada comando debe ejecutarse dentro del sandbox definido por el Guardian.
- No declarar `VERIFIED_CLOSED` con jobs activos, GAPS, colisiones, pruebas omitidas o evidencia incompleta.

## Carriles paralelos

El microkernel activa carriles independientes para `inventory`, `research`, `security-license`, `simulation`, `refutation`, `adapter`, `tests` y `rollback`. La concurrencia es limitada, no se usa shell y cada carril tiene timeout, directorio de trabajo y salida propios. Los resultados se ordenan de forma determinista antes de escribir un ledger nuevo.

## Documentos de contexto

El patrón combina dos ideas verificadas: instrucciones de proyecto cargadas al inicio como `CLAUDE.md`, y un workspace explícito como el de OpenClaw. Aquí la guía es informativa; Sheriff, Sentinel y Guardian deben hacer cumplir las reglas en código y CI, porque un documento no es una frontera de seguridad.

## Cierre

El resultado mínimo incluye `run_id`, huella de propuesta, autorización, estado de cada carril, hashes, pruebas, rollback y veredicto. Solo Judge y Guardian pueden emitir `VERIFIED_CLOSED`.
