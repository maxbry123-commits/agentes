# code-programming-engine/

**Despliegue 1 — Opción A** (instrucciones: `despliegue/INSTRUCCIONES_GROK_OPCION_A.md`)

Motor de programación de code **fuera del kernel**. Definición única compartida.
Instancias paralelas = `instance_pool.py` (no duplicar el motor).

## Runtime canónico (NO apagar)

| Pieza | Path real |
|-------|-----------|
| Hot path C-19 | `extensions/wordflow/engine/code_path_runner.py` |
| Pipeline | `extensions/wordflow/engine/programming_pipeline.py` |
| Gateway | `extensions/wordflow_kernel/gateway/` |

Este árbol **añade** pool + registro + hooks. No reemplaza el monolito hasta paridad de tests.

## Contenido de este lote

| Archivo | Rol |
|---------|-----|
| `programming_instance.py` | Contrato de una ejecución aislada |
| `instance_pool.py` | Tenant isolation + concurrency + idempotency |
| `capability_registration.py` | Entradas de catálogo (idempotente) |
| `classifier_hook.py` | Cuándo abrir instancia |
| `usage_metering.py` | Medición de uso |
| `SOURCE.md` | Punteros al code real |
