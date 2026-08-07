# Salida C/6 — persist + metrics DEFAULT

## Hecho
- `persist_dir="loop_data"` por defecto
- PersistenceStore: registry · state · events · dlq
- LoopMetrics.record_run en cada run_once
- try_otel_counter hook
- metrics_snapshot()

## Siguiente D/6
MHYTOS strategy dentro del engine
