# A09 COMPLETA · Durable runtime

## Entregable

`runtime/durable.py`

## API

- create_mission / checkpoint / resume / complete
- enqueue_signal (CORRECTION|UPDATE|HEARTBEAT|CANCEL)
- apply_next_signal FIFO
- NEW_TASK rechazado en mission ajena

## Persistencia

`state_dir/<mission_id>.json` (contrato listo para SQL/Temporal)

## Checks

- [x] resume tras "caída" restaura phase+cursor
- [x] signals ordenados
- [x] NEW_TASK no mezcla missions

## Siguiente

**A10** — CorrectionSet → rebuild same mission
