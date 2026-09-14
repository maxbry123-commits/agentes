# PLAN DE TRABAJO CLAUDE → WORDFLOW LOOP

**Fuente:** `Readme arquitectura Yaiwes/Claude instrucciones Yaiwes/`  
**Estado:** extracción documental; NO significa que el código esté implementado.  
**Regla:** distinguir `REUSE/SEARCH/WIRE/WRITE/TEST` y comprobar el repo antes de generar nada.

## 1. Método de trabajo que Claude indica

1. **Cerrar primero una ruta mínima E2E (Nivel A).** Una tarea simple debe entrar, decidir, ejecutar, guardar evidencia y terminar sin reparación manual. No activar primero Mythos, pool grande, Council o watchdog.
2. **Reutilizar y cablear antes de escribir.** El Bloque 1 dice explícitamente que no se escribe código nuevo salvo cuando la tarea lo ordena; la mayoría del trabajo es comparar, delegar, envolver, importar y conectar código existente.
3. **Trabajar por dependencias.** Bloque 1 → Bloque 2 → Bloque 3 → Bloque 4; la capa 71–90 depende del cierre de los bloques anteriores.
4. **Un fallo real = siguiente delta.** En el cierre simple, ejecutar desde el entrypoint real, registrar exactamente dónde falla, arreglar solo eso y volver a ejecutar.
5. **Checkpoint + auditoría.** Cada tarea tiene checkpoint; Claude agrupa auditorías cada 5 tareas y exige evidencia antes de marcar 100% PASS.
6. **Kernel determinista.** Scheduler, DAG, contratos, Sheriff, estado, recovery, trazabilidad y selección determinista deben vivir fuera del LLM. El LLM queda aislado para razonamiento cuando sea necesario.
7. **Maker ≠ Checker.** El generador no debe aprobar su propio resultado; Claude separa generador/evaluador y propone auditoría adversarial → cruzada → maker-checker.
8. **Contratos antes de montar capacidad.** Schema cerrado, validador, timeout, idempotencia, policy/deny-list, sandbox y evidencia antes de aceptar una capacidad.
9. **Código externo: analizar primero, no tocar original.** Rellenar ficha → validar → `PASSTHROUGH` si ya encaja o `ADAPTER` si hay que traducir interfaz → nuevo slot → shadow test → swap; rechazar si exige reescritura insegura.
10. **Buscar OSS/librerías reales antes de programar.** Claude da librerías concretas para scheduler, router, colas, pool, memoria, observabilidad, recovery, testing y algoritmos; no propone reescribirlas desde cero.
11. **Aislar ejecución paralela.** Workers/agentes externos en worktrees/sandbox; capability matching; normalizar resultados antes del agregador.
12. **Cierre por evidencia.** Unit/integration/E2E, contratos, hashes/ledger, secret scan/SBOM y X-Ray final; si falla una condición, sigue `FAIL-CLOSED/PARCIAL`.

## 2. Ruta inmediata que Claude prioriza — NIVEL A

| Paso | Acción documental de Claude | Tipo |
|---|---|---|
| A1 | Verificar/arreglar los 5 imports señalados por su auditoría | VERIFY/PATCH |
| A2 | Resolver `mission.py` | SEARCH → REUSE o WRITE delta |
| A3 | Resolver `goal_lock.py` | SEARCH primero; no asumir que falta |
| A4 | Resolver bootstrap de `execution-orchestration/` | SEARCH → REUSE/WIRE o WRITE delta |
| A5 | Resolver `recovery.py`, reutilizando checkpoint si existe | REUSE/WIRE |
| A6 | Elegir una tarea mínima y ejecutarla desde entrypoint real | TEST E2E |
| A7 | Si cae, corregir solo el primer fallo demostrado y repetir | LOOP DELTA |
| A8 | Parar cuando una ejecución completa deje resultado + evidencia | CIERRE NIVEL A |

**Nota forense:** el documento 08 enumera archivos concretos según una auditoría previa. Antes de escribir cualquiera hay que revalidar su existencia/ruta en `main`; el documento no sustituye el X-Ray actual.

## 3. Elementos de código / búsqueda por documento

### Documento 01 — Fundamentos y limpieza, tareas 1–15
- Comparar duplicados `workflow.py/runtime.py`; delegar/importar en vez de duplicar.
- SBOM con CycloneDX o Syft.
- CLI canónico con Typer.
- `mypy --strict`/Pyright.
- Contratos de 8 primitivas: Event Loop, DSL, Scheduler, Runtime, Registry, Router, Policy, State.
- Wrappers delegantes sobre Wordflow/Wordflow Kernel existente.
- Manifest de migración.
- Regresión sobre tests existentes.
- **Método dominante:** `REUSE + WIRE + WRAPPER + TEST`, no generación masiva.

### Documento 02 — Razonamiento y gobernanza, tareas 16–35
- goal dual driver, decision-on-demand, prompts versionados, score de complejidad, selección de plantilla.
- expert-panel-router, consensus-trigger, workflow-capacity.
- schema cerrado + validator.
- timeout, idempotencia y concurrencia de estado.
- sheriff/sentinel/council, Judge, forensic log, LLM deny-list.
- tests de reasoning/extension kernel y cierre de gaps.
- OSS sugerido: Pydantic/PydanticAI, DSPy, semantic-router, Mixture-of-Agents, OPA, TruLens, OpenTelemetry, Guardrails AI.
- **Método dominante:** buscar librería/patrón → adaptar mínimo → contrato → test.

### Documento 03 — Workflow, pool y memoria, tareas 36–55
- primer DAG YAML real + step template + registry.
- DAG/FSM executor, task generation y guard determinista.
- extraer worktrees/subagentes de Grok Build, sin copiar su cerebro decisor.
- pool paralelo Ray o Celery, capability matching, result normalization, agregador.
- mount-guard con sandbox/secret scan.
- memoria Letta/Mem0 y wiring MEMORY_WRITE.
- agentes auxiliares y test workflow→pool→agregador.
- **Método dominante:** workflow real pequeño primero; workers aislados; adaptar piezas OSS concretas.

### Documento 04 — Observabilidad y cierre, tareas 56–70
- OpenTelemetry, IDs obligatorios y ledger.
- ejecución durable con Temporal o LangGraph checkpointer.
- retry/backoff + circuit breaker + resource leases + watchdog.
- contract testing, Merkle, E2E sin mocks críticos.
- SBOM/secret scan, manifest final, cero placeholders, X-Ray final y veredicto.
- OSS sugerido: OTel, Temporal/LangGraph, Tenacity/pybreaker, Schemathesis/Pact, pymerkle.
- **Método dominante:** endurecer solo después de tener workflow/pool E2E.

### Documento 05 — Arquitectura Fables
- separa sesión append-only del harness.
- kernel 0% LLM; LLM aislado.
- InputBlock → GoalLock → DSL/DAG/Contract/Sheriff → Scheduler → Multi-API/Fleet → auditoría → reasoning → recovery → evidence.
- Maker/Checker separados.
- Claude reconoce que varias piezas estaban completas solo en papel y debían escribirse o fusionarse desde librerías.
- **Método dominante:** arquitectura por capas + fail-closed + evidencia; no confundir diseño con implementación.

### Documento 06 — Investigación OSS
Buscar/reutilizar antes de escribir:
- sesión/durabilidad: Temporal o LangGraph.
- multi-API: LiteLLM + `asyncio.wait/gather` + Mixture-of-Agents.
- scheduler: APScheduler/Celery Beat/croniter.
- input queue: NATS JetStream o Redis Streams.
- fleet: Ray + piezas de Grok Build.
- memoria: Letta/Mem0/Graphiti/LlamaIndex/DVC.
- gateway: OpenClaw/Hermes/n8n.
- elicitation: JSON Schema/PydanticAI o Rasa.
- contexto: CLAUDE.md/AGENTS.md + compactación del Claude Agent SDK como referencia.
- **Método dominante:** `SEARCH OFFICIAL CODE → EXTRACT PATTERN/CAPABILITY → ADAPT`, nunca copiar un sistema completo sin necesidad.

### Documento 07 — Loops, Multi-API, memoria y chat, tareas 71–90
- APScheduler time-wheel práctico.
- LiteLLM SINGLE/RACE/QUORUM/SPLIT.
- NATS/Redis input block.
- Ray Fleet Manager + Hermes fleet rail.
- memoria niveles 1–5.
- separación session/harness y generator/evaluator.
- context reset, Pydantic enums, gateway OpenClaw, MCP Hermes.
- tests reales multi-provider e input concurrente.
- **Dependencia literal:** ejecutar esta capa después del cierre de los bloques 1–4.

### Documento 08 — Cierre simple
- Prioridad absoluta: una tarea aburrida E2E.
- no escribir todavía `sentinel.py`, `council.py`, `supervisor.py`, `watchdog.py` para cerrar Nivel A.
- no activar Mythos 40 pasos.
- no seguir produciendo diseño si no corre el camino real.
- **Método dominante:** ejecución → fallo exacto → delta pequeño → repetición.

### Documento 09 — Intake de código al kernel
- analizar exports/deps/riesgos antes de ejecutar.
- ficha con datos determinables; `[NO_DETERMINABLE]` si faltan datos.
- validar identidad + ejecución + sandbox/timeout.
- Opción 1 passthrough si encaja; Opción 2 adapter si necesita traducción; REJECT si exige reescritura insegura.
- original intacto; ficha + adapter separados; nuevo slot; shadow test/swap.
- **Método dominante:** preservar original + adapter, no modificar lógica de terceros.

### Documento 10 — Módulos de razonamiento
Antes de incorporar uno exige 4 pruebas:
1. independencia de dominio en 3 dominios;
2. no redundancia con módulos existentes;
3. instrucción accionable;
4. costo declarado.
- SELECT por expert-panel-router → ADAPT por decision-on-demand → ejecución paralela → Judge.
- **Método dominante:** calificar antes de integrar; rechazar duplicados.

### Documento 11 — 105 algoritmos deterministas
- catálogo de capacidades sin LLM: grafos, búsqueda, lógica formal, consenso, MCDA, optimización, persistencia, testing, etc.
- Claude indica usar implementaciones/librerías probadas (`networkx`, `jsonschema`, `pysat`, `scipy`, `OR-Tools`, Hypothesis, Pact/Schemathesis, etc.) en lugar de reescribirlas.
- cada algoritmo es candidato, no obligación de instalar los 105.
- **Método dominante:** seleccionar por gap real → buscar implementación madura → ficha `kind: code` → test → enchufe.

## 4. Código que Claude ya dejó junto a los documentos

### `expert_panel_router.py`
Código candidato real de SELECT determinista: carga YAML, rankea módulos y permite inyectar otro ranker. **No recrearlo sin X-Ray.** Debe probarse/cablearse en su destino real antes de llamarlo integrado.

### `decision_on_demand.py`
Código candidato real para SELECT→ADAPT→IMPLEMENT→RANK, pero trae `_llm_caller_dummy` y ejecución secuencial. **No es producción todavía:** requiere proveedor real/Multi-API, tests y cableado.

## 5. Orden práctico extraído de Claude para empezar Wordflow

```text
1. X-RAY runtime actual
2. demostrar qué existe y qué falta
3. cerrar NIVEL A con una tarea mínima
4. REUSE interno antes de descargar/generar
5. buscar OSS solo para gaps reales
6. copiar/adaptar por contrato
7. cablear
8. test unitario/contrato/integración/E2E
9. evidencia
10. recién después activar pool/Multi-API/memoria/watchdog avanzados
```

## 6. Estados que debe usar esta construcción

`EXISTS_UNVERIFIED | REUSE | SEARCH | WIRE | WRITE_DELTA | TEST | GAP | VERIFIED_CLOSED`

Un nombre en Claude o un archivo descargado nunca equivale a `VERIFIED_CLOSED`.