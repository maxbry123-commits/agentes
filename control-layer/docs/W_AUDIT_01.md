# Auditoría W01–W06 · mejoras 10x

## Pasada 1 — Cobertura
Goals, Failure, Budget, Hot-input, ChangeEngine: OK.

## Pasada 2 — Literalidad
- NEW_TASK no debe atar mission_id → gateway OK
- Change nunca rebuild_workflow → OK
- Budget es de cadena, no solo agente → OK

## Pasada 3 — Gaps detectados y cerrados en esta salida
1. Gateway: forzar mission_id=None en NEW_TASK siempre (refuerzo)
2. Goals: export helpers en contracts/__init__ si falta
3. Budget: método snapshot para Event Store

## Pasada 4 — Riesgo
No introducir Temporal/Graphiti en núcleo. Adapters solo.
