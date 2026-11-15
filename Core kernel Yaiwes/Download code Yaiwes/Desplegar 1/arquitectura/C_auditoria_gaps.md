# Auditoría de Gaps — Objective Engine v2

> **Auditor:** Kimi K3 (Auto-auditoría crítica)  
> **Fecha:** 2026-08-16  
> **Clasificación:** CRÍTICO — Hallazgos de gaps antes de producción  
> **Estado:** 23 hallazgos identificados (7 críticos, 9 altos, 7 medios)

---

## ⚠️ ADVERTENCIA INICIAL

> Esta auditoría es **intencionalmente destructiva**. Busco refutar mi propio trabajo para encontrar todo lo que falta. Un sistema que no puede sobrevivir a su propia auditoría no merece llamarse "kernel de agente".

---

## HALLAZGO 1 [CRÍTICO] — Sin Sistema de Señales Implementado

**Descripción:** En la arquitectura propuse un sistema signal-driven (PAUSE, RESUME, CANCEL, APPROVE, REVERT), pero en el código de `objective_runtime.py` solo implementé `pause()`, `resume()` y `cancel()` como flags booleanos simples. No hay un `SignalBus`, no hay manejo de señales externas, no hay aprobación humana en el loop, no hay REVERT.

**Impacto:** Sin esto, el sistema no puede integrarse en workflows empresariales donde un humano debe aprobar ciertos pasos.

**Evidencia:**
```python
# Lo que hay (inadecuado):
self._paused = False
self._cancelled = False

# Lo que se necesita:
class SignalBus:
    async def emit(self, signal: Signal, execution_id: str): ...
    async def subscribe(self, execution_id: str) -> AsyncIterator[Signal]: ...
```

**Mitigación:** Implementar `signals.py` con patrón pub/sub asíncrono.

---

## HALLAZGO 2 [CRÍTICO] — Sin Sandbox de Ejecución

**Descripción:** Los workers ejecutan código arbitrario sin sandbox. Un plan malicioso o un plan con un bug podría ejecutar `rm -rf /` o exfiltrar datos.

**Impacto:** Riesgo de seguridad catastrófico. El sistema no puede ejecutar código de usuarios no confiables.

**Evidencia:** El `default_executor` en `objective_runtime.py` es un stub vacío que no implementa ninguna sandbox.

**Mitigación:** Implementar `kernel/security/sandbox.py` con:
- Contenedores Docker para cada worker
- Límites de CPU/memoria/tiempo
- Network policies restrictivas
- Audit de syscalls

---

## HALLAZGO 3 [CRÍTICO] — Sin Guardrails Éticos Implementados

**Descripción:** Propuse guardrails en la arquitectura pero no los implementé en código. No hay validación de que los objetivos no sean dañinos, ilegales o antiéticos.

**Impacto:** El agente podría generar y ejecutar objetivos peligrosos (ej: "hackear servidor X", "generar malware").

**Evidencia:** Ningún módulo valida el contenido ético del objetivo antes de ejecutar.

**Mitigación:** Implementar `kernel/security/ethics.py` con:
- Clasificador de riesgo de objetivos
- Lista de objetivos prohibidos
- Aprobación humana obligatoria para riesgo alto
- Logging de intentos de objetivos prohibidos

---

## HALLAZGO 4 [CRÍTICO] — Plan Compiler No Genera Código Real

**Descripción:** El `PlanCompiler` compila a un `ExecutionDAG`, pero los nodos del DAG no contienen código ejecutable real. El `action` es solo un string como `"task"` o `"jwt + rbac"`. No hay generación de código, no hay despacho a herramientas reales.

**Impacto:** El DAG es un plano arquitectónico, no un programa ejecutable. El sistema no puede "hacer" nada solo.

**Evidencia:**
```python
# En ExecutionNode:
action: Optional[str] = None  # Solo un string identificador
action_config: Dict[str, Any] = field(default_factory=dict)  # Config vacía
```

**Mitigación:** Implementar un `CodeGenerator` que transforme nodos del DAG en:
- Código Python ejecutable
- Llamadas a API
- Comandos shell sandboxeados
- Prompts estructurados para LLM workers

---

## HALLAZGO 5 [CRÍTICO] — Sin Sistema de Permisos/ACL

**Descripción:** No hay control de acceso. Cualquier componente puede modificar cualquier otro componente. No hay autenticación entre workers.

**Impacto:** Si un worker está comprometido, puede manipular el grafo completo.

**Mitigación:** Implementar ACLs por nodo: qué worker puede ejecutar qué tipo de acción, qué contexto puede ver.

---

## HALLAZGO 6 [CRÍTICO] — Memory Sin Embeddings Reales

**Descripción:** `ObjectiveMemory` tiene un campo `embedding` y una función `_cosine_similarity`, pero no hay generación real de embeddings. El `embedding_fn` es opcional y si no se pasa, la búsqueda por similitud cae a keywords.

**Impacto:** La recuperación de estrategias similares es superficial (keywords) en lugar de semántica (embeddings).

**Evidencia:**
```python
if self.embedding_fn and record.embedding is None:
    record.embedding = self.embedding_fn(record.objective_description)
# Si embedding_fn es None, nunca se generan embeddings
```

**Mitigación:** Integrar con `sentence-transformers` o API de embeddings (OpenAI, Cohere) por defecto.

---

## HALLAZGO 7 [CRÍTICO] — Sin Tests Implementados

**Descripción:** Propuse una batería de tests pero no implementé NINGUNO. No hay tests unitarios, no hay tests de integración, no hay tests de los 12 GOALS.

**Impacto:** El código es inusable en producción. No hay forma de verificar que funciona.

**Evidencia:** Cero archivos de test generados.

**Mitigación:** Generar mínimo 50 tests unitarios + 10 tests de integración + tests para cada uno de los 12 GOALS.

---

## HALLAZGO 8 [ALTO] — Sin Observabilidad Real (OpenTelemetry)

**Descripción:** Mencioné OpenTelemetry en la arquitectura pero no implementé trazas, métricas ni spans. El `audit_log` es solo una lista de diccionarios en memoria.

**Impacto:** En producción no se puede debuggear el sistema. No hay distributed tracing.

**Mitigación:** Integrar `opentelemetry-api` y `opentelemetry-sdk` con spans para cada fase del pipeline.

---

## HALLAZGO 9 [ALTO] — Sin Manejo de Concurrencia en el Grafo

**Descripción:** `ObjectiveGraph` no es thread-safe. Si múltiples workers intentan modificar el estado de nodos simultáneamente, hay condiciones de carrera.

**Impacto:** Corrupción de estado del grafo en ejecución paralela.

**Mitigación:** Añadir locks por nodo o usar estructuras inmutables para el grafo durante ejecución.

---

## HALLAZGO 10 [ALTO] — Sin Límites de Recursos en Workers

**Descripción:** `WorkerPool` usa un `asyncio.Semaphore` pero no limita tiempo de ejecución, memoria, ni CPU por tarea.

**Impacto:** Una tarea bloqueada puede bloquear todo el worker pool indefinidamente.

**Mitigación:** Implementar timeouts por nodo, cancelación forzada, y límites de recursos.

---

## HALLAZGO 11 [ALTO] — Sin Persistencia de Checkpoints a Disco

**Descripción:** El `checkpoint_callback` recibe datos pero no hay implementación de `CheckpointStore` que persista a disco de forma atómica.

**Impacto:** Si el proceso principal muere, los checkpoints en memoria se pierden.

**Mitigación:** Implementar `kernel/persistence/checkpoint_store.py` con escritura atómica (write-then-rename) y compresión.

---

## HALLAZGO 12 [ALTO] — Sin Manejo de Timeouts en Ejecución

**Descripción:** `ExecutionRuntime.execute()` no tiene timeout global. Una ejecución podría correr para siempre.

**Impacto:** Recursos bloqueados indefinidamente. Posible ataque DoS.

**Mitigación:** Añadir `max_execution_time` y cancelar automáticamente.

---

## HALLAZGO 13 [ALTO] — Plan Validator No Ejecuta Precondiciones Reales

**Descripción:** `_validate_preconditions()` solo verifica que la precondición no sea `"false"` o `"impossible"`. No evalúa precondiciones contra el estado real del mundo.

**Impacto:** Un plan puede pasar validación pero fallar en ejecución porque una precondición real no se cumple.

**Mitigación:** Implementar un `StateManager` que mantenga el estado del mundo y permita evaluar precondiciones contra él.

---

## HALLAZGO 14 [ALTO] — Sin Compensaciones (Saga Pattern)

**Descripción:** Mencioné el patrón Saga de Conductor pero no implementé compensaciones. Si un nodo falla después de que otros completaron, no hay rollback de los efectos secundarios.

**Impacto:** Estado inconsistente. Un pago procesado no se puede revertir si el envío falla.

**Mitigación:** Cada nodo debe definir una función `compensate()` que revierte sus efectos.

---

## HALLAZGO 15 [ALTO] — Recovery Engine Es Un Stub

**Descripción:** `local_replan()` y `rebuild_subgraph()` son stubs que retornan el mismo DAG sin modificar. No hay lógica real de replanificación.

**Impacto:** Cuando falla, el sistema no puede recuperarse realmente. Solo reintenta lo mismo.

**Evidencia:**
```python
def local_replan(self, exec_dag, classification):
    # Stub: retornar el mismo DAG
    return exec_dag
```

**Mitigación:** Implementar replanificación que consulte al LLM para regenerar el subgrafo afectado.

---

## HALLAZGO 16 [ALTO] — Sin Manejo de Deadlocks

**Descripción:** Si dos nodos se bloquean mutuamente esperando recursos, el sistema no detecta ni resuelve el deadlock.

**Impacto:** Ejecución congelada indefinidamente.

**Mitigación:** Implementar detección de deadlock con wait-for graph y resolución por aborto de nodos.

---

## HALLAZGO 17 [MEDIO] — Sin Compresión de Memoria

**Descripción:** `ObjectiveMemory` almacena todo en JSONL sin compresión. A escala, esto consume disco excesivamente.

**Mitigación:** Añadir compresión gzip y rotación de archivos.

---

## HALLAZGO 18 [MEDIO] — Sin Deduplicación de Estrategias

**Descripción:** Si el mismo objetivo se ejecuta 100 veces con la misma estrategia, se almacenan 100 registros idénticos.

**Mitigación:** Implementar deduplicación por hash de estrategia + resultado.

---

## HALLAZGO 19 [MEDIO] — Sin Métricas de Performance

**Descripción:** No hay recopilación de métricas: tiempo por nodo, tasa de éxito por tipo de objetivo, utilización de workers, etc.

**Mitigación:** Integrar Prometheus metrics o similar.

---

## HALLAZGO 20 [MEDIO] — Sin Versionado del Schema

**Descripción:** Los datos persistidos (checkpoints, memoria, audit logs) no tienen versión de schema. Si cambia el formato, los datos antiguos no se pueden leer.

**Mitigación:** Añadir `schema_version` a todos los documentos persistidos.

---

## HALLAZGO 21 [MEDIO] — Sin Manejo de Secrets

**Descripción:** Las credenciales de LLM, APIs externas, y tokens de autenticación no tienen un manejo seguro. Probablemente se pasarían como strings planos.

**Mitigación:** Integrar con un secret manager (HashiCorp Vault, AWS Secrets Manager, etc.).

---

## HALLAZGO 22 [MEDIO] — Sin Documentación de Prompts

**Descripción:** Los prompts que el LLM usaría para descubrir, descomponer, clasificar fallos, etc., no están documentados ni versionados.

**Mitigación:** Crear `kernel/llm/prompts/` con prompts versionados y testeados.

---

## HALLAZGO 23 [MEDIO] — Sin Exportación a Conductor

**Descripción:** Propuse que OE v2 podría exportar a Conductor para escalabilidad de cluster, pero no implementé el exportador.

**Mitigación:** Implementar `kernel/exporters/conductor_exporter.py` que transforme `ExecutionDAG` a formato Conductor JSON.

---

## RESUMEN EJECUTIVO DE LA AUDITORÍA

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| 🔴 CRÍTICO | 7 | Bloqueantes para producción |
| 🟠 ALTO | 9 | Degradan severamente la utilidad |
| 🟡 MEDIO | 7 | Deben resolverse antes de v1.0 |
| **TOTAL** | **23** | |

### Los 7 Críticos Resumidos

1. **Sin sistema de señales** — No hay control operativo real
2. **Sin sandbox** — Ejecución insegura de código arbitrario
3. **Sin guardrails éticos** — Riesgo de objetivos dañinos
4. **Sin generación de código** — El DAG no es ejecutable realmente
5. **Sin ACLs** — Sin control de acceso entre componentes
6. **Sin embeddings reales** — Búsqueda de memoria es solo por keywords
7. **Sin tests** — Código no verificable

### Veredicto Final

> **El Objective Engine v2 es una ARQUITECTURA sólida y bien fundamentada, pero una IMPLEMENTACIÓN incompleta.**
>
> Los 8 módulos de código entregados son **esqueletos funcionales** que demuestran la arquitectura, pero **NO son código de producción**.
>
> Para llevar esto a producción se necesita:
> - **+2,000 líneas de código adicionales** (tests, sandbox, señales, seguridad)
> - **+5 módulos nuevos** (signals, sandbox, ethics, state_manager, code_generator)
> - **Integración con 3+ servicios externos** (embeddings, secret manager, observability)
>
> **Recomendación:** Usar estos 8 módulos como **especificación ejecutable** y **prototipo de arquitectura**. Iterar en sprints enfocados en los 7 hallazgos críticos antes de cualquier despliegue.

---

## PLAN DE REMEDIACIÓN PROPUESTO

### Sprint 1 (Seguridad Crítica)
- [ ] Implementar sandbox de ejecución
- [ ] Implementar guardrails éticos
- [ ] Implementar ACLs y autenticación de workers

### Sprint 2 (Funcionalidad Crítica)
- [ ] Implementar sistema de señales (SignalBus)
- [ ] Implementar generación de código ejecutable
- [ ] Integrar embeddings reales

### Sprint 3 (Calidad)
- [ ] Escribir batería completa de tests (unit + integration)
- [ ] Implementar observabilidad (OpenTelemetry)
- [ ] Implementar persistencia atómica de checkpoints

### Sprint 4 (Resiliencia)
- [ ] Implementar compensaciones (Saga pattern)
- [ ] Implementar replanificación real (no stubs)
- [ ] Implementar manejo de deadlocks y timeouts

---

*Auditoría generada por Kimi K3 — Auto-refutación crítica con 23 hallazgos*
