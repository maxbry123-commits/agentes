# Instrucciones — Opción A + Instance Pool (code-programming-engine)

## Objetivo
Sacar el motor de programación de code del kernel, ponerlo como pieza única
compartida (`code-programming-engine/`), y agregar `instance_pool.py` para
que múltiples tenants/workflows lo usen en paralelo sin pisarse.

## Archivos entregados en este paquete
- `programming_instance.py` — contrato de datos de una ejecución aislada
- `instance_pool.py` — aislamiento por tenant + tope de concurrencia + dedup
- `capability_registration.py` — entradas para tus catálogos reales
- `classifier_hook.py` — decide cuándo abrir una instancia y con qué perfil
- `usage_metering.py` — medición de uso para facturación SaaS

## Dónde conecta con el repo real (`maxbry123-commits/agentes`)

| Pieza nueva | Se conecta a (archivo real ya auditado) | Qué hacer |
|---|---|---|
| `code-programming-engine/` | `extensions/wordflow/engine/code_path_runner.py` + `programming_pipeline.py` | Mover estos módulos aquí como base del motor. **No reescribir su lógica interna**, solo reubicar. |
| `capability_registration.append_entries()` | `extensions/wordflow/component_catalog.json` + `connect_catalog.json` | Ejecutar una sola vez para añadir las 2 entradas de componente + 2 de conexión. Es idempotente: correrlo dos veces no duplica. |
| `classifier_hook.dispatch_to_engine()` | módulo `task_*` dentro de `extensions/wordflow/engine/` (task_classifier) | Integrar como el punto donde el classifier existente decide "esto es code, abro instancia" en vez de llamar directo al runner. |
| `instance_pool.InstancePoolManager` | `extensions/wordflow_kernel/gateway/intelligence.py` + `router_http.py` | **Este es el punto de enchufe real de los motores externos.** Hoy solo tiene adapters `Mock` y `RouterHTTP` (marcado `stub` en el catálogo). Cada `engine_binding` de una instancia debe resolver aquí a un adapter concreto: Claude Code, Codex, OpenHands, OpenCode, Aider, Cline. |
| Nivel 3 (agentes auxiliares) | `extensions/wordflow_kernel/engines/openclaw_stub.py` y `hermes_stub.py` | Llenar estos dos stubs con la lógica real de paralelismo de apoyo/supervisión — ya existen como archivo, solo faltan implementados. |
| `usage_metering.UsageMeter` | `extensions/wordflow/state/ledger.py` | Integrar contra ese ledger (`append_only_events`) en vez de la lista en memoria del ejemplo — así el consumo queda persistido igual que el resto del estado del sistema. |

## Regla que no se toca
El monolito en `main` (`code_path_runner.py` tal cual funciona hoy) sigue
siendo la única fuente operativa real. La rama `programming-modular-v1`
(p01–p12) es el prototipo de cómo debería quedar dividido, pero hoy
`runner.py` solo bridgea al legacy — no lo reemplaces hasta que la versión
modular pase los mismos tests (`test_code_path_runner.py`,
`test_unified_programming.py`, etc.) con el mismo resultado exacto.

## Extras recomendados para reforzar esta opción

1. **Idempotency key** (ya incluido en `programming_instance.py` y
   `classifier_hook.py`): usa `task_id` como clave. Evita que un reintento
   de red abra una segunda instancia para la misma tarea — mismo patrón que
   usa Trigger.dev para runs durables.
2. **Heartbeat/watchdog**: el repo ya tiene `watchdog.py` en
   `extensions/wordflow/engine/`. Engánchalo a cada `ProgrammingInstance`
   activa para detectar instancias colgadas y transicionarlas a `FAILED`
   automáticamente, liberando su slot de concurrencia.
3. **Fallback chain**: si `dispatch_to_engine` devuelve `None` por
   `ConcurrencyCapExceeded`, no falles la tarea — reintenta con otro
   `engine_binding` disponible o encola en `task_queue` del workflow. El
   sistema no debe detenerse por un solo motor ocupado.
4. **Schemas pendientes** (gap ya confirmado por auditoría): crear
   `pre_gate.schema.json`, `forensic_state.schema.json`,
   `run_code_path_return.schema.json` dentro de
   `code-programming-engine/schemas/` — hoy ese contrato vive solo
   implícito en el código.

## Estándar de código a seguir (ya usado en T-001 de este proyecto)
Máximo 30 líneas por función · máximo 500 líneas por archivo · docstring
obligatorio en cada función/clase · sin números mágicos (usar constantes
nombradas) · sin `except: pass` · orden de ejecución determinista.

## Qué NO hacer todavía
- No apagar ni reemplazar `code_path_runner.py` en `main`.
- No mezclar el `tenant_id` de instancias con el `project-isolation` de
  workflows — son dos aislamientos distintos, no sustituyen uno al otro.
- No exponer `credential_ref` de `ApiSlot` en logs ni en `wire_trace`.
