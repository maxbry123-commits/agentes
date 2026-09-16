# ✅ NOTA X-RAY — Claude 03

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/03_hoja_de_ruta_workflows_pool_memoria.md`
**Blob SHA fuente:** `a4c094a210d2aa96db9dd7caaf82e5147b717e62`
**Estado:** AUDITADO / PROPUESTA, no integrado.

## 4 pasadas
1. **Literal/método:** primero un workflow real; luego DAG/FSM, task-generation, guard determinista, worktrees, pool, capability matching, normalización, agregador, memoria y tests.
2. **Código que falta / cómo conseguirlo:** extraer/adaptar solo piezas concretas de código existente o librerías señaladas; no importar bucles decisores completos ni reconstruir todo.
3. **Integración:** toda pieza externa requiere destino, capability passport, mount-guard/sandbox y test de integración workflow→pool→agregador.
4. **Cruce YAIWES:** encaja con `multi-workflow-engine`, `execution-orchestration`, `execution-engine-pool`, `agent-fleet-parallelism` y memoria; Claude 08 lo coloca después del Nivel A.

## 6 lentes
Literal PASS · Arquitectura ALINEADO · Código PARCIAL/PENDIENTE INVENTARIO · Integración POR CAPACIDAD · Seguridad SANDBOX/PASSPORT · Cierre E2E requerido.

**Conclusión:** el Wordflow no debe desplegar pool/memoria para compensar un E2E roto; primero cerrar la ruta mínima y después añadir paralelismo por necesidad demostrada.
