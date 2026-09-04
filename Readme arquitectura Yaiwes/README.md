# README — Arquitectura fusionada YAIWES · X-Ray

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Base original:** arquitectura fusionada X-Ray 2026-09-01  
**Actualización forense:** 2026-09-03  
**Regla:** GitHub y el código ejecutable son la verdad. Una carpeta o documento no demuestra que una capacidad esté operativa.

> Este `README.md` es la arquitectura canónica única de `Readme arquitectura Yaiwes/`. Las tareas, checkpoints, instrucciones del Director, instrucciones literales de Claude, notas de agentes y estado operativo se mantienen fuera de la arquitectura, dentro de `Crazy Wall Orquestador/`.

## 1. Fuentes fusionadas y trazabilidad

### Fuentes originales preservadas
1. [Índice raíz de arquitectura YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20estructura%20ra%C3%ADz%20de%20agente%20Yaiwes%20wordflow.md)
2. [PLAN_100 — árbol definitivo](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md)
3. [STRUCTURE — estructura materializada](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/STRUCTURE.md)
4. [README canónico de agente-yaiwes](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/README.md)
5. [Foto de producción y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md)
6. [Mapa de organización del código real](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md)
7. [Arquitectura Wordflow consolidada](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md)
8. [Pasada 1 — Structure](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_01_STRUCTURE.md)
9. [Pasada 2 — Connectivity](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_02_CONNECTIVITY.md)
10. [Pasada 3 — Behavior](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_03_BEHAVIOR.md)
11. [Pasada 4 — Cierre](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_04_CIERRE.md)

### Lote 1 — documentos de arquitectura YAIWES
La revisión incorpora el inventario completo de `Documentos arquitectura Yaiwes lote 1/`, incluyendo Mythos/Fables, Muse, Ruflo, PLAN YAIWES, core kernel de razonamiento, diagramas v0–v3.1, Ley Principal TEAM, MAVIS/MAX-SYSTEM, orquestador, memoria Wordflow y el documento de faltantes de kernel/extensión-kernel.

El documento `PLAN_YAIWES_AGENTE_WORDFLOW.md` reafirma como reglas: no inventar planes paralelos; no reescribir el hot path sin paridad; aplicar regla lego; reutilizar `goal_lock.py`, `cognitive_loop.py` y `evidence_packet.py` por referencia; usar `gateway/intelligence.py` + `router_http.py` como punto de enchufe; y terminar/cablear p01→p12 en vez de rehacerlos.

### Instrucciones Claude
Se cruzan literalmente los documentos 01–09 de `Documentos proyectos Yaiwes instrucciones de Claude/`: bloques 1–4, arquitectura Fables, investigación OSS, Loops/Multi-API/Memoria/Chat, protocolo de cierre simple y guía de integración de código.

La lista operativa Claude 1–90 fue retirada de este README y se mantiene en Crazy Wall. El README conserva arquitectura, reglas, mapas, criterios y evidencia; no contiene el backlog operativo/checkpoints.

## 2. Leyenda X-Ray

- **REAL:** código ejecutable localizado en fuente y con cuerpo funcional demostrable.
- **PARCIAL:** capacidad o ruta existente, pero cableado/pruebas/cierre incompletos.
- **ESQ:** scaffold, fake, stub o placeholder.
- **REF:** referencia a implementación canónica que vive en otra ruta.
- **DECLARADO_NO_VERIFICADO:** afirmado por documento pero aún no localizado con evidencia suficiente.
- **FALTANTE:** requerido por arquitectura y no demostrado en código real.
- **VERIFIED_CLOSED:** implementación + cableado + test relevante + evidencia + auditoría destino.

## 3. Arquitectura rectora fusionada

La arquitectura resultante conserva el microkernel TEAM/YAIWES y separa control determinista, razonamiento probabilístico, ejecución, extensiones, memoria, evidencia y agentes externos.

```text
INPUT / SESSION
  ↓
Input Layer / InputBlockReader
  ↓
Mission + GOAL_LOCK
  ↓
DSL → DAG → Contract / Schema
  ↓
Sheriff / Policy / Mount Guard
  ↓
Kernel TEAM 0% LLM
  ├─ Event Loop
  ├─ DSL Engine
  ├─ Scheduler
  ├─ Runtime
  ├─ Registry
  ├─ Router
  ├─ Policy Engine
  └─ State Manager
  ↓
Execution Orchestration
  ├─ deterministic execution
  ├─ state-machine / DAG executor
  ├─ classifier-scheduler
  ├─ task generation
  └─ mission planning
  ↓
Extension Kernel / ABI / Capability Registry
  ↓
Execution Engine Pool / Fleet / Worktree Isolation
  ↓
Reasoning on demand — only when justified
  ├─ DRE
  ├─ EURS
  ├─ MYTHOS
  ├─ expert panel
  └─ consensus / judge
  ↓
Recovery + State + Memory
  ↓
Evidence / Witness / Audit / Closure
  ↓
OUTPUT
```

### Principio 90/10
- Núcleo de coordinación: **0% LLM**.
- Operaciones repetibles, contratos, DAG, scheduler, sheriff, estado, recovery y evidencia: deterministas.
- LLM: cápsula aislada para decisión bajo ambigüedad, investigación compleja, generación no cubierta y consenso.

## 4. Árbol objetivo YAIWES

```text
main/
└── agente-yaiwes/
    ├── code-programming-engine/
    │   ├── engine-modules/
    │   ├── code-path-execution/
    │   ├── standards-forensic/
    │   ├── schema-contracts-io/
    │   ├── external-motor-bridge/
    │   └── module-tests/
    ├── kernel-principal/
    │   ├── extension-kernel/
    │   │   ├── abi-mount/
    │   │   ├── capability-registry/
    │   │   ├── capability-passport/
    │   │   ├── native-learning/
    │   │   └── mount-guard/
    │   ├── reasoning-kernel/
    │   │   ├── decision-on-demand/
    │   │   ├── expert-panel-router/
    │   │   ├── consensus-trigger/
    │   │   ├── goal-dual-driver/
    │   │   └── workflow-capacity/
    │   ├── resource-governance/
    │   │   ├── resource-broker-gate/
    │   │   ├── lease-management/
    │   │   ├── watchdog/
    │   │   ├── circuit-breaker/
    │   │   └── retry-policy/
    │   ├── internal-bus/
    │   └── execution-manifest/
    ├── input-layer/
    │   ├── cli-entry/
    │   ├── route-entry/
    │   ├── cross-tool-session-import/
    │   └── reception/
    ├── definition-registry/
    │   ├── workflow-definition/
    │   ├── agent-definition/
    │   ├── task-definition/
    │   ├── tool-definition/
    │   ├── skill-definition/
    │   ├── schema-contracts/
    │   ├── domain-specific-contracts/
    │   ├── declared-dependency-catalog/
    │   └── authorization-model/
    ├── control-governance/
    │   ├── contracts-and-gates/
    │   ├── sheriff-sentinel-council/
    │   ├── forensic-verdict/
    │   ├── verdict-authority/
    │   ├── forensic-core/
    │   ├── symbol-test-requirement-index/
    │   ├── policy-guardrails-permissions/
    │   ├── llm-control-deny/
    │   ├── refute-repair/
    │   ├── pre-post-closure-gates/
    │   └── gap-registry-and-tasks/
    ├── multi-workflow-engine/
    │   ├── shared-services/
    │   └── instances/workflow-N/
    ├── execution-orchestration/
    │   ├── state-machine-executor/
    │   ├── dag-executor/
    │   ├── sequential-parallel-loop-route/
    │   ├── container-pod-isolation/
    │   ├── task-generation/
    │   ├── deterministic-execution/
    │   ├── mission-planning-goal-lock/
    │   ├── classifier-scheduler/
    │   ├── dependency-injection-context/
    │   └── programming-pipeline/
    ├── agent-fleet-parallelism/
    ├── execution-engine-pool/
    │   ├── adapter-layer/
    │   ├── capability-matching/
    │   ├── parallel-dispatch/
    │   ├── worktree-isolation/
    │   ├── result-normalization/
    │   └── auxiliary-role-agents/
    ├── mesh-routing-collaboration/
    ├── pipeline-runtime/
    ├── codebase-intelligence/
    ├── session-resilience/
    ├── identity-config/
    ├── human-in-the-loop/
    ├── communication-notifications/
    ├── control-plane-ui/
    ├── state-events-durability/
    ├── tools-models-memory-knowledge/
    ├── research-evidence/
    ├── security-auth/
    ├── observability/
    ├── multi-project-orchestration/
    ├── artifact-output-storage/
    └── deploy-publish/
```

## 5. Código operativo real y ruta de transición

La arquitectura final todavía convive con el runtime Wordflow operativo. No se debe apagar ni reescribir el hot path hasta paridad.

```text
extensions/wordflow/
├── reception/
├── planner/
├── engine/
│   ├── code_path_runner.py
│   ├── programming_pipeline.py
│   ├── programming_kwargs.py
│   ├── input_quality_bar.py
│   ├── skill_native_compiler.py
│   ├── goal_lock.py
│   └── cognitive_loop.py
├── motors/
├── connectors/
├── contracts/
├── schemas/
├── state/
├── policies/
└── tests/

extensions/wordflow_kernel/
├── gateway/
├── bridge/
├── engines/
├── checkpoint.py
├── engine_registry.py
├── fail_closed.py
├── ficha.v2.json
└── bootstrap_*.py
```

### Regla de evolución
`REUSE → REFERENCIAR/COPY con SHA cuando proceda → ADAPT → TEST → CUTOVER`.

No mover ni reescribir `extensions/wordflow/engine/code_path_runner.py` hasta demostrar paridad de imports, contratos, tests y evidencia.

## 6. Actualización forense X-Ray — documentos vs código

| Requisito/afirmación | Evidencia de código | Estado actualizado |
|---|---|---|
| GOAL_LOCK | `extensions/wordflow/engine/goal_lock.py` contiene `GoalLock`, hash/inmutabilidad, `create_goal_lock`, verificación y validación contra output | **REAL; REUTILIZAR, NO REESCRIBIR** |
| Checkpoint reutilizable | `extensions/wordflow_kernel/checkpoint.py` existe | **REAL/PARCIAL según cableado** |
| Registry base | `extensions/wordflow_kernel/engine_registry.py` existe | **REAL/PARCIAL; candidato a fachada** |
| Policy fail-closed | `extensions/wordflow_kernel/fail_closed.py` existe | **REAL/PARCIAL; candidato a fachada** |
| Ficha/schema v2 | `extensions/wordflow_kernel/ficha.v2.json` existe | **REAL** |
| Bootstrap kernel | `bootstrap_fake.py`, `bootstrap_multi.py`, `bootstrap_v1.py` existen | **PARCIAL; hay variante fake y falta decidir bootstrap canónico** |
| `validator_v2.py` declarado por Claude | no localizado en ruta esperada; búsqueda por nombre no devolvió coincidencia concluyente | **DECLARADO_NO_VERIFICADO / GAP** |
| `UniversalPluginBus.enchufar()` | búsqueda exacta sin coincidencia localizada | **DECLARADO_NO_VERIFICADO** |
| `ContractGenerator.generate()` | búsqueda exacta sin coincidencia localizada | **DECLARADO_NO_VERIFICADO** |
| `AdapterFactory.create()` | búsqueda exacta sin coincidencia localizada | **DECLARADO_NO_VERIFICADO** |
| `PluginRegistry` | búsqueda exacta sin coincidencia localizada | **DECLARADO_NO_VERIFICADO** |
| `mission.py` del cierre Nivel A | no localizado por búsqueda nominal en esta pasada | **FALTANTE/NO VERIFICADO** |
| OpenClaw/Hermes auxiliares | arquitectura previa los identifica como stubs | **ESQ hasta nueva evidencia** |
| p01→p12 modular | Lote 1 ordena terminar cableado, no rehacer | **PARCIAL hasta auditoría del branch/main actual** |

**Corrección importante frente al documento Claude 08:** `goal_lock.py` no debe crearse desde cero. Existe implementación real en Wordflow y la arquitectura manda reutilizarla/referenciarla en el destino canónico.

## 7. Gate de cierre Nivel A antes del Nivel B

Claude define correctamente un gate mínimo que esta arquitectura adopta, pero corregido con la evidencia actual:

```text
Entrada real
→ misión formal
→ GOAL_LOCK existente/reutilizado
→ decisión/ruta mínima
→ ejecución
→ recovery/checkpoint si falla
→ evidencia
→ cierre
```

El Nivel A queda cerrado solo cuando una tarea mínima atraviesa esa cadena desde el entrypoint real sin reparación manual y deja evidencia verificable.

Mientras ese E2E no esté probado, el veredicto global permanece **FAIL-CLOSED / PARCIAL** aunque existan componentes de Nivel B.

## 8. Arquitectura Fables / Mythos incorporada

Los documentos Fables/Claude se consolidan como arquitectura de servicios, no como un segundo kernel:

- `InputBlockReader` → `input-layer/reception` + estado/cola.
- `MissionBuilder / GOAL_LOCK` → `execution-orchestration/mission-planning-goal-lock`, reutilizando la implementación Wordflow.
- DSL/DAG/Contracts → `definition-registry` + `execution-orchestration`.
- Sheriff/Policy → `control-governance` + Policy Engine del kernel.
- Scheduler/Time-Wheel → scheduler/resource governance.
- Multi-API Fabric SINGLE/RACE/QUORUM/SPLIT → capa de routing/model fabric fuera del microkernel puro.
- Fleet Manager/worktrees → `agent-fleet-parallelism` + `execution-engine-pool`.
- Mythos/EURS/DRE → contenido/versiones bajo `reasoning-kernel/decision-on-demand`, no lógica de control hardcodeada.
- Recovery RETRY→ROLLBACK→CHECKPOINT→REPLAN→ESCALATE → durability/resource governance.
- Witness/evidence_hash → observability/research-evidence/closure gates.
- Memoria 5 niveles → `tools-models-memory-knowledge/`, desacoplada del harness.

## 9. Arquitectura de integración de componentes

Todo componente del repositorio o adquirido externamente sigue un solo carril:

```text
COMPONENTE ORIGEN
→ X-RAY estático
→ identificar responsabilidad única
→ comprobar licencia/dependencias/seguridad
→ ficha/contrato
→ decidir TOTAL | PARCIAL | ADAPTADOR | RECHAZAR
→ mapear destino exacto YAIWES
→ aprobación Director
→ movimiento por Sol GPT/GitHub Action
→ verificar destino + SHA
→ ID Crazy Wall
→ cableado Codex quirúrgico
→ tests
→ auditoría post-Codex
→ VERIFIED_CLOSED
```

### Reglas de integración
1. El código original no se reescribe si un adaptador resuelve la incompatibilidad.
2. El kernel no importa directamente un repositorio externo; consume puertos/contratos.
3. No duplicar capacidades compartidas: regla lego.
4. Un reemplazo activo requiere shadow-test + swap o mecanismo equivalente antes del cutover.
5. Nada se descarga de OSS hasta comprobar que no existe ya en `agentes` o `Agentes-motores-Wordflow-YAIWES`.

## 10. Componentes OSS propuestos — estado arquitectónico

Los componentes investigados por Claude son **candidatos**, no dependencias instaladas por defecto:

| Necesidad | Candidato | Estado |
|---|---|---|
| Durabilidad/sesión | Temporal / LangGraph checkpointer | CANDIDATO |
| Multi-API | LiteLLM + asyncio | CANDIDATO |
| Scheduler periódico | APScheduler / croniter | CANDIDATO |
| Cola InputBlock | NATS JetStream / Redis Streams | CANDIDATO |
| Pool paralelo | Ray | CANDIDATO |
| Worktree/subagentes | Grok Build, pieza aislada | CANDIDATO; requiere mount-guard |
| Memoria | Letta/Mem0/Graphiti/LlamaIndex | CANDIDATO |
| Policy/Sheriff | OPA/Casbin | CANDIDATO |
| Verificación schemas | Pydantic/jsonschema | CANDIDATO |
| Retry/breaker | Tenacity/pybreaker | CANDIDATO |
| Observabilidad | OpenTelemetry/Langfuse | CANDIDATO |

La selección final se decide por gap real, licencia, superficie de integración, seguridad, dependencias y pruebas; no por documento.

## 11. Separación sesión ↔ harness

La arquitectura adopta explícitamente:

- **Sesión/estado:** append-only, ledger, checkpoints, evidencia, memoria y trazas sobreviven al cambio de modelos/harness.
- **Harness/kernel/runtime:** decide rutas, ejecuta contratos y puede evolucionar sin destruir historial.

Esto evita que memoria/estado queden acoplados a un modelo o loop específico.

## 12. Maker–Checker y anti auto-evaluación

Generador y evaluador no deben ser la misma instancia/contexto cuando el resultado requiera juicio. El cierre exige criterios objetivos, tests y evidencia. `Judge`/`Verifier` no sustituyen tests deterministas cuando éstos son posibles.

## 13. Gaps arquitectónicos activos tras esta pasada

1. Cerrar la traza Nivel A desde entrypoint hasta evidencia.
2. Verificar/corregir los cinco imports señalados por Claude en sus rutas actuales, sin asumir que siguen rotos.
3. Localizar o materializar `mission.py`/contrato de misión canónico reutilizando implementaciones existentes si existen bajo otro nombre.
4. Elegir/cablear bootstrap canónico; no usar `bootstrap_fake.py` como evidencia de producción.
5. Implementar/adaptar recovery reutilizando `checkpoint.py` antes de crear lógica duplicada.
6. Verificar los símbolos declarados del Enchufe Universal; actualmente solo `ficha.v2.json` está demostrado por esta pasada.
7. Terminar mapa físico de todos los componentes del repo hacia destinos YAIWES.
8. Auditar p01→p12 contra el branch/main actual y mantener `code_path_runner` operativo hasta paridad.
9. Sustituir/llenar stubs OpenClaw/Hermes únicamente después de identificar componentes internos reutilizables.
10. Cerrar contratos por etapa, índice símbolo→test→assert, observabilidad y estado durable.
11. Ejecutar después los bloques reasoning/pool/memoria/multi-API según dependencias reales, no por número de tarea solamente.

## 14. Estado por cuatro pasadas

1. **STRUCTURE:** arquitectura objetivo materializada parcialmente; referencias/scaffolds no equivalen a implementación.
2. **CONNECTIVITY:** existen hot paths y piezas reutilizables, pero quedan destinos sin cableado y componentes declarados no verificados.
3. **BEHAVIOR:** `goal_lock` y varias piezas Wordflow/wordflow_kernel muestran comportamiento real; no hay evidencia suficiente aún del E2E completo del nuevo árbol.
4. **FORENSIC_CLOSURE:** **FAIL-CLOSED / PARCIAL** hasta Nivel A E2E + pruebas/evidencia y posteriores gates de cada bloque.

## 15. Regla de trabajo desde esta actualización

Este README describe exclusivamente arquitectura y su estado X-Ray. El backlog completo Claude 1–90, instrucciones literales del Director, checkpoints, prompts de agentes, estado JSON, notas y plan viven en Crazy Wall.

El siguiente paso arquitectónico no es diseñar otra capa: es completar el inventario componente→destino con evidencia, someter la primera integración al Director y ejecutar el ciclo aprobado de movimiento→verificación→Codex→auditoría.

## 16. Registros centrales del TEAM Runtime

La fuente de verdad del Lote 1 exige que TEAM no sea un agente convencional sino un **runtime integrador/fusionador**. Para evitar que herramientas, skills, modelos y harnesses queden como accesorios externos sin gobernanza, la arquitectura incorpora registros centrales separados pero interoperables:

```text
Registry Fabric
├── Agent Registry
├── Skill Registry
├── Tool Registry
├── Prompt Registry
├── Workflow Registry
├── MCP Registry
├── Knowledge Registry
├── Capability Registry
├── Harness Registry
├── Model Registry
├── Memory Provider Registry
└── Policy Registry
```

Regla de estado para cualquier recurso descubierto:

```text
REGISTERED ≠ AVAILABLE ≠ HEALTHY ≠ AUTHORIZED
```

El Router y el Resource Brain solo pueden seleccionar recursos que hayan pasado discovery, mapping, health, authorization y contract validation.

## 17. Capability Compiler / Specialty Compiler / Evolution Kernel

El Lote 1 establece que TEAM no debe conservar roles, prompts o métodos como texto muerto cuando puedan convertirse en artefactos ejecutables. La arquitectura adopta este pipeline:

```text
REPOSITORY / DOCUMENT / SKILL / AGENT
→ DISCOVERY
→ CAPABILITY EXTRACTION
→ CONTRACT/FICHA
→ TEMPLATE
→ CAPABILITY or SPECIALTY COMPILER
→ DSL / DAG / SCHEMA / VALIDATORS / SHERIFF
→ ADAPTERS
→ TESTS / BENCHMARKS
→ CAPABILITY PASSPORT
→ REGISTRY
→ RUNTIME
```

Un rol como `python.backend.engineer` se materializa como paquete gobernado con manifest, capabilities, goals, inputs, outputs, methods, workflows, schemas, validators, sheriff, adapters, libraries lock, knowledge, examples, benchmarks, failures y learning. El LLM puede descubrir/diseñar; el Evolution Kernel compila; el runtime determinista ejecuta.

## 18. Arquitectura de adquisición selectiva Ruflo / Muse / agentes externos

### Ruflo
No se instala ni se forkea como dependencia permanente. Se congela commit SHA, se reconstruye árbol completo, se genera inventario forense, se valida completitud y después se extraen selectivamente capacidades útiles como memoria/AgentDB/HNSW, graph, swarm, coordination, routing, guidance, security, proof, hooks y learning.

Carril:

```text
SOURCE LOCK
→ COMPLETE TREE
→ FORENSIC INVENTORY
→ COMPLETENESS AUDIT
→ CAPABILITY MAP
→ SELECTIVE EXTRACTION
→ TEAM ADAPTERS
→ CAPABILITY PASSPORT
→ TEAM KERNEL / WORKFLOW
```

### Muse
Muse se trata como referencia de capacidades, no como código descargable oficial mientras no exista fuente verificable. Las capacidades arquitectónicas absorbibles son: persistent event log, background agents, parallel execution, git worktree isolation, planning mode, goal conditioning/goal loop y subagent delegation + context compaction.

Esas capacidades se mapean a state-events-durability, agent-fleet-parallelism, execution-engine-pool, execution-orchestration y session-resilience.

## 19. Paralelismo 100x y ejecución multi-sandbox

Los documentos MAVIS/MAX añaden patrones que quedan fuera del microkernel pero dentro del runtime de ejecución:

- fan-out/fan-in;
- batching;
- sharding por key;
- persistent worker pools;
- priority queue;
- async pipeline con backpressure;
- cache/dedup;
- idempotency keys;
- dead-letter queue;
- outbox + CDC cuando aplique;
- time-wheel;
- pre-warming/autoscaling por queue depth;
- multi-pool por concern;
- worktree y sandbox isolation.

El microkernel solo decide política/orden/contrato. La implementación de throughput vive en `execution-engine-pool`, `agent-fleet-parallelism`, `resource-governance`, `state-events-durability` y `execution-orchestration`.

## 20. Workflow ↔ Memory/Audit Orchestrator

La memoria de largo contexto no se implementa intentando colocar 20M tokens en la ventana activa. Se define como memoria externa jerárquica recuperable.

Fronteras:

```text
WORKFLOW = qué hacemos ahora
MEMORY/AUDIT = qué información recuperamos, conservamos y validamos
SANDBOX = dónde ejecutamos la unidad
LLM = procesa/razona la unidad asignada
CONSOLIDATOR = integra piezas globalmente
AUDITOR = verifica confiabilidad/completitud
CHECKPOINT = recuperación/rollback/continuación
ROUTER = selecciona recursos
POLICY = autoridad
STATE MACHINE = transiciones deterministas
```

Contrato mínimo:

```text
WORKFLOW
→ GET_CONTEXT / GET_MEMORY / GET_EVIDENCE / GET_STATE / GET_HISTORY / GET_ARTIFACT / GET_RELATIONS
→ MEMORY/AUDIT: RETRIEVE → RERANK → AUDIT → RELATE → BUILD_CONTEXT
→ CONTEXT PACK
→ SANDBOX → LLM
→ STATE DELTA
→ MEMORY/AUDIT: VALIDATE → STORE → AUDIT → CONSOLIDATE
→ WORKFLOW
```

La UI permanece última; el comportamiento real debe funcionar sin interfaz.

## 21. Workspace Orchestration / Multi-project

Cada proyecto puede materializarse como workspace aislado administrado por:

```text
ORQUESTADOR
├── Workspace Manager
├── Agent Manager
├── Document Manager
├── Git Manager
├── Knowledge Manager
├── Memory Manager
└── Sync Manager
```

El workspace mantiene IDs, configuración, documentación, código, memoria, graph, logs, checkpoints, prompts, reports y state. Esta capa vive en `multi-project-orchestration/` y no modifica el microkernel.

## 22. Input anchoring y pre-investigación

El orquestador incorpora la separación conceptual:

```text
RAW INPUT
→ InputClassifier
↘ BackgroundResearch en paralelo
→ Structured/Socratic Questions cuando sean necesarias
→ Integrator
→ AnchoredInput
→ Orquestador principal
```

El input anclado conserva tipo, keywords, entidades, aclaraciones del usuario, contexto investigado, confianza y gaps. La investigación paralela no debe modificar el GOAL_LOCK original.

## 23. Cobertura documental Lote 1 — 24 entradas físicas registradas

| # | Documento Lote 1 | Aporte arquitectónico absorbido |
|---|---|---|
| 1 | `11-razonamiento-mythos.md` | EURS, Mythos 40, Fables, micro-ciclo, DRE, separación control/LLM |
| 2 | `Descargar muse code y fusiónar componentes con agente team YAIWES.md` | event log, background agents, parallel, worktrees, planning, goal loop, compaction |
| 3 | `Descargar y integrar la capacidades del agente rufo con el agente TEAM.md` | adquisición determinista, source-lock, inventario, extracción selectiva, adapters |
| 4 | `FABLES_Mythos_Paso_01_Ingesta.md` | ingesta/input, contratos iniciales y preparación Mythos |
| 5 | `FABLES_Mythos_Paso_02B_Codigo.md` | ejecución/código/validación del pipeline Fables |
| 6 | `FABLES_Mythos_Paso_03C_Cierre.md` | cierre, evidencia, verificación y salida |
| 7 | `Json promt fables grupo a .md` | schemas/prompts estructurados; contenido versionado, no control hardcodeado |
| 8 | `PLAN_YAIWES_AGENTE_WORDFLOW.md` | mapa origen→destino, regla lego, hot path, S1–S12 como fuente operativa trasladada a Crazy Wall |
| 9 | `README.md` | índice del Lote 1 |
| 10 | `Sistema ... descubre → registra → mapea → verifica → selecciona → prepara → carga → ejecuta.md` | Resource/Capability/Memory Provider Registry y health/authorization states |
| 11 | `core kernel razonamiento fusión para Yaiwes.md` | cognitive kernel/operators/model router y razonamiento como graph/skills |
| 12 | `diagram-v0.html` | visualización histórica de arquitectura |
| 13 | `diagram-v1.html` | visualización histórica/evolución |
| 14 | `diagram-v2.html` | visualización histórica/evolución |
| 15 | `diagram-v3.1.html` | visualización histórica/evolución |
| 16 | `diagram-v3.html` | visualización histórica/evolución |
| 17 | `todo el concepto ... fuente de la verdad ... agente TEAM nueva versión.md` | TEAM como runtime fusionador, universal harness, registries, determinismo alto |
| 18 | `Ley principal ... OpenClaw y Hermes ... TEAM.md` | capability distillation/compiler, no absorber cerebros, conservar capacidades/runtimes |
| 19 | `MAVIS-PARALLEL-100X.md` | worker pool, priority queue, cache, batch, backpressure, async, dedup |
| 20 | `MAX-SYSTEM-100X-FINAL-1.md` | fanout, sharding, time-wheel, idempotency, DLQ, outbox/CDC, multi-pool, prewarm |
| 21 | `si o si orquestador parte 2.md` | Workspace Orchestration multi-proyecto |
| 22 | `si o si para el orquestador Maxbry.md` | input anchor, pre-research paralelo, herramientas transversales |
| 23 | `memoria del Wordflow ... 20 millones ...` | Memory/Audit contract, context fabric y memoria externa jerárquica |
| 24 | `falta integrar al kernel o extensión kernel del Wordflow1.md` | specialty/evolution compiler y capacidades ejecutables versionadas |

Ningún documento del Lote 1 se usa como prueba de implementación: solo como requisito/fuente arquitectónica.

## 24. Cobertura Claude — 09/09 literal + arquitectura absorbida

| Claude | Arquitectura absorbida |
|---|---|
| 01 | kernel base, 8 primitivas, wrappers, manifest, regresión |
| 02 | reasoning/governance, contracts, timeout, idempotencia, sheriff/judge/forensic |
| 03 | workflow real, DAG/FSM, pool, adapters, mount guard, memoria |
| 04 | observabilidad, durability, retry/breaker, watchdog, E2E, cierre |
| 05 | arquitectura Fables completa y separación sesión/harness |
| 06 | catálogo OSS como candidatos, no dependencias automáticas |
| 07 | Time-Wheel, Multi-API, InputBlock, Fleet, memoria 5 niveles, chat |
| 08 | gate kernel simple Nivel A antes de Nivel B |
| 09 | protocolo de integración/reutilización de código; afirmaciones verificadas contra fuente antes de aceptar |

## 25. Veredicto de cobertura arquitectónica

**Cobertura documental:** `PASS_DOCUMENTAL_LOTE1_24 + CLAUDE_09`.

**Cobertura de implementación:** `FAIL_CLOSED_PARTIAL` porque todavía faltan verificaciones/cableados/tests reales.

La arquitectura se considera documentalmente fusionada; no se considera implementada. Cualquier contradicción futura entre documento y código se resuelve a favor del código real y actualiza este mismo README, nunca creando una arquitectura paralela.

---

# ANEXO A — PRESERVACIÓN DE LA ARQUITECTURA ORIGINAL 2026-09-01

> Este anexo **no es una segunda arquitectura**. Conserva la información arquitectónica no operativa del README original (blob `9408ccf30843983a91546c963638d48f28e60ae9`) que fue eliminada accidentalmente durante una edición previa. Se excluyeron únicamente las tablas/listas de tareas 1–70 y sus checkpoints, porque por instrucción del Director pertenecen al Crazy Wall. El contenido conservado sigue sujeto al X-Ray actual: una afirmación histórica no equivale a evidencia de implementación.

## Criterio final de "primera versión completa"

La v1 está cerrada solo si las 4 condiciones siguientes son verdaderas al mismo tiempo:

1. El manifest de las 8 primitivas del Kernel TEAM no tiene ningún estado vacío.
2. Existe al menos un workflow real, probado E2E, que pasa por reception→mission→decision→execution→evidence→closure sin usar stubs.
3. El pool paralelo ejecuta al menos 2 agentes/workers reales con roles distintos y un agregador que produce una decisión final.
4. La auditoría X-Ray repetida muestra cero placeholders en `kernel-principal/` y cobertura de tests en `reasoning-kernel/` y `extension-kernel/`.

Si alguna de las 4 no se cumple, el veredicto sigue siendo `FAIL-CLOSED / PARCIAL` — no se declara v1 completa a medias.

## Arquitectura completa fusionada — cuatro niveles (base original preservada)

```text
main/
└── agente-yaiwes/
    ├── code-programming-engine/                         [PARCIAL/REF]
    │   ├── engine-modules/
    │   │   ├── code_path_runner.py                     [REF al hot path]
    │   │   ├── programming_pipeline.py                 [REF al hot path]
    │   │   └── cognitive_loop.py                       [REF/PARCIAL]
    │   ├── code-path-execution/
    │   │   ├── programming-modular-v1/
    │   │   ├── p01...p12                               [FALTANTE en main]
    │   │   └── evidence/                               [PARCIAL]
    │   ├── standards-forensic/
    │   ├── schema-contracts-io/
    │   ├── external-motor-bridge/
    │   ├── multi-account-bridge/
    │   ├── inbox-normalization/
    │   └── module-tests/
    ├── kernel-principal/
    │   ├── control-layer/
    │   │   └── SOURCE.md                               [REF]
    │   ├── extension-kernel/
    │   │   ├── abi-mount/
    │   │   ├── capability-registry/
    │   │   ├── capability-passport/
    │   │   ├── native-learning/
    │   │   └── mount-guard/
    │   ├── reasoning-kernel/
    │   │   ├── decision-on-demand/
    │   │   ├── expert-panel-router/
    │   │   ├── consensus-trigger/
    │   │   ├── goal-dual-driver/
    │   │   └── workflow-capacity/
    │   ├── resource-governance/
    │   │   ├── resource-broker-gate/
    │   │   ├── lease-management/
    │   │   ├── watchdog/
    │   │   ├── circuit-breaker/
    │   │   └── retry-policy/
    │   ├── internal-bus/
    │   └── execution-manifest/
    ├── input-layer/
    │   ├── cli-entry/
    │   ├── route-entry/
    │   ├── cross-tool-session-import/
    │   └── reception/
    ├── definition-registry/
    │   ├── workflow-definition/
    │   │   ├── yaml-dag/
    │   │   ├── step-template/
    │   │   └── source-hierarchy/
    │   ├── agent-definition/
    │   ├── task-definition/
    │   ├── tool-definition/
    │   ├── skill-definition/
    │   ├── schema-contracts/
    │   ├── domain-specific-contracts/
    │   ├── declared-dependency-catalog/
    │   └── authorization-model/
    ├── control-governance/
    │   ├── contracts-and-gates/
    │   ├── sheriff-sentinel-council/
    │   ├── forensic-verdict/
    │   ├── symbol-test-requirement-index/
    │   ├── policy-guardrails-permissions/
    │   ├── refute-repair/
    │   ├── pre-post-closure-gates/
    │   └── gap-registry-and-tasks/
    ├── multi-workflow-engine/
    │   ├── shared-services/
    │   │   ├── workflow-registry/
    │   │   ├── runner-host/
    │   │   ├── dashboard-budget/
    │   │   └── control-ops/
    │   └── instances/
    │       ├── workflow-1/
    │       ├── workflow-2/
    │       ├── workflow-3/
    │       └── workflow-N/
    ├── execution-orchestration/
    │   ├── state-machine-executor/
    │   ├── dag-executor/
    │   ├── sequential-parallel-loop-route/
    │   ├── container-pod-isolation/
    │   ├── task-generation/
    │   ├── deterministic-execution/
    │   ├── mission-planning-goal-lock/
    │   ├── classifier-scheduler/
    │   ├── dependency-injection-context/
    │   └── programming-pipeline/
    ├── agent-fleet-parallelism/
    ├── execution-engine-pool/
    │   ├── adapter-layer/                              [PARCIAL]
    │   ├── capability-matching/
    │   ├── parallel-dispatch/
    │   ├── worktree-isolation/
    │   ├── result-normalization/
    │   └── auxiliary-role-agents/                      [STUBS]
    ├── mesh-routing-collaboration/
    ├── pipeline-runtime/
    ├── codebase-intelligence/
    ├── session-resilience/
    ├── identity-config/
    ├── human-in-the-loop/
    ├── communication-notifications/
    ├── control-plane-ui/
    ├── state-events-durability/
    │   └── dead-letter-handling/
    ├── tools-models-memory-knowledge/
    │   └── mcp-transport/
    ├── research-evidence/
    ├── security-auth/
    ├── observability/
    │   └── trace-history/
    ├── multi-project-orchestration/
    ├── artifact-output-storage/
    ├── deploy-publish/
    │   ├── multi-account-registry/
    │   ├── push-injection/
    │   ├── publish-schema-layer/
    │   ├── remote-crud-ops/
    │   └── deployment-target-selector/
    ├── extensions/                                    [REF]
    ├── PIPELINE/                                      [REF]
    ├── agents/                                        [REF]
    └── .github-workflows-refs/                        [REF]
```

## Código operativo real y Wordflow actual — base original preservada

La arquitectura nueva no sustituyó por completo el runtime anterior. El flujo ejecutable principal permanece aquí:

```text
main/
└── extensions/
    ├── wordflow/
    │   ├── reception/
    │   │   └── convert / normalización
    │   ├── planner/
    │   │   └── misión / tareas / clasificación
    │   ├── engine/
    │   │   ├── code_path_runner.py                    [HOT PATH REAL]
    │   │   ├── programming_pipeline.py                [REAL]
    │   │   ├── programming_kwargs.py                  [REAL]
    │   │   ├── input_quality_bar.py                   [REAL]
    │   │   ├── skill_native_compiler.py               [REAL]
    │   │   ├── goal_lock.py                           [REAL]
    │   │   └── cognitive_loop.py                      [REAL/PARCIAL]
    │   ├── motors/
    │   ├── codegen/
    │   ├── connectors/
    │   ├── contracts/
    │   ├── schemas/
    │   ├── standards/
    │   ├── state/
    │   ├── store/
    │   ├── policies/
    │   ├── accounts/
    │   └── tests/
    └── wordflow_kernel/
        ├── gateway/
        │   ├── intelligence.py                        [PUNTO DE ENCHUFE]
        │   └── router_http.py                         [ADAPTADOR HTTP]
        ├── runtime/
        ├── contracts/
        └── auxiliary/
            ├── openclaw_stub.py                       [STUB]
            └── hermes_stub.py                         [STUB]
```

### Flujo transversal original

```text
Entrada
→ reception.convert
→ goals / goal_lock
→ mission + planner
→ task_classifier
→ programming_pipeline
→ code_path_runner
→ motors / tools / adapters
→ evidence
→ gates forenses
→ artefacto / despliegue
```

## Las 8 capas de decisión definidas en la base original

Según el diseño Kernel TEAM, el microkernel contiene exactamente 8 primitivas y no debe contener navegador, OCR, Git, Docker ni IA; solo decide qué se ejecuta, quién lo ejecuta y cuándo:

1. **Event Loop** — recibe eventos y los despacha.
2. **DSL Engine** — interpreta lenguaje declarativo.
3. **Scheduler** — orden y momento de ejecución.
4. **Runtime** — entorno de ejecución de capacidades.
5. **Registry** — catálogo de capacidades, workflows y agentes del pool.
6. **Router** — selecciona capacidad/workflow/agente.
7. **Policy Engine** — reglas duras de autorización y control.
8. **State Manager** — fuente de verdad del estado.

La base original fija como guardrail que el Kernel TEAM debe permanecer pequeño: si una función puede fallar sin tumbar el sistema, debe vivir fuera del microkernel como servicio/capacidad.

## Patrón de auto-replicación original

La réplica es **Actor Model con inyección de rol por contrato**: el código de cada worker es idéntico y lo que cambia es el `TASK CONTRACT`, no un prompt que inventa identidad. Patrones de referencia conservados: Ray Actors, Kubernetes ReplicaSet/Job, Erlang/OTP supervisor, `ProcessPoolExecutor`/`multiprocessing.Pool` y Celery workers.

La auditoría original identificó cuatro requisitos de robustez que permanecen válidos hasta demostrar cierre: idempotencia, deadlines, validador de contrato explícito y concurrencia segura en State Manager.

## Mythos y fuentes de razonamiento — base original preservada

La base original mapeó el esqueleto de Mythos a piezas OSS como referencias, nunca como prueba de implementación:

| Grupo Mythos | Referencia/patrón | Uso arquitectónico |
|---|---|---|
| 1–10 | DSPy | firmas/módulos tipados para comprensión y descomposición |
| 11–20 | Tree of Thoughts + Mixture-of-Agents | ramas/hipótesis y agregación |
| 21–30 | Reflexion + Voyager | reflexión, memoria episódica y skills reutilizables |
| 31–40 | AlphaCodium + Mixture-of-Agents | ranking/fusión/síntesis |
| Pipeline completo | AI-Scientist | organización por fases y auto-revisión |

Regla conservada: estas piezas entran como **capacidades** bajo `extension-kernel`/reasoning on demand; nunca sustituyen el Kernel TEAM determinista.

## Árbol de decisión para integrar una pieza nueva

1. Si da el mismo resultado con el mismo input sin juicio → **capacidad** → `extension-kernel/capability-registry/`.
2. Si es una secuencia fija de capacidades → **workflow** → `multi-workflow-engine/instances/workflow-N/`.
3. Si necesita juicio/modelo/memoria propia que no se desmonta → **agente de pool** → `execution-engine-pool` / `agent-fleet-parallelism`.

`goal-dual-driver` conserva su casa en `kernel-principal/reasoning-kernel/goal-dual-driver/`. El procesamiento de tareas nuevas conserva la frontera `input-layer/reception/` → `definition-registry/task-definition/` → `execution-orchestration/task-generation/`.

## Extension Kernel — semántica original preservada

- `capability-registry/`: catálogo de capacidades.
- `capability-passport/`: licencia, fingerprint, fuente y versión.
- `abi-mount/`: puerto/contrato técnico que el kernel consume.
- `mount-guard/`: validación de pasaporte, contrato y seguridad antes del montaje.
- `native-learning/`: historial de confiabilidad de capacidades.

**Regla dura:** el kernel no importa directamente un repositorio externo; consume el puerto/ABI. El origen queda detrás del adaptador.

## Selección de workflows y reasoning on demand

1. La tarea entra por `input-layer` con `task-definition`.
2. `classifier-scheduler` calcula complejidad/riesgo/ambigüedad.
3. `expert-panel-router` intenta match contra workflows registrados.
4. Si existe match de alta confianza, se ejecuta sin LLM.
5. Solo si no existe match suficiente, `consensus-trigger`/`decision-on-demand` habilita razonamiento probabilístico.

Mythos/EURS/DRE son contenido versionado bajo `decision-on-demand`; el kernel determinista decide cuándo se habilitan.

## Metodología original de extracción/poda

Se preservan los patrones arquitectónicos Anti-Corruption Layer, Ports & Adapters y Strangler Fig:

1. localizar una responsabilidad única;
2. separar funciones que **deciden** de las que **hacen**;
3. definir el puerto TEAM antes de tocar el origen;
4. escribir/adaptar el adaptador;
5. impedir imports directos del origen desde el kernel;
6. validar en sandbox/simulation/mount-guard;
7. versionar contrato y fallback;
8. garantizar idempotencia.

Para aceptar un agente completo como pool se conservan los criterios: aislamiento, contrato I/O, red auditada, licencia, coste, reproducibilidad, no redundancia, observabilidad, fallo limpio y procedencia confiable. Si falla en varios criterios, se prefiere extracción selectiva.

## Capas externas al LLM — nomenclatura original

Los términos preservados son: **Orchestrator, Agent Framework, Cognitive Layer, Control Plane y Agent Runtime**. El stack MYTHOS→FSM→ROUTER→SHERIFF→SENTINEL→VERIFIER→CRITIC→JUDGE→POLICY ENGINE→PYDANTICAI→RETRY ENGINE→LLM se interpreta como control plane + cápsula probabilística.

Las cadenas de razonamiento de 35/40 pasos no se consideran control determinista; permanecen dentro del reasoning on demand. Alternativas/referencias conservadas: DSPy, LangGraph, Guidance, Instructor y LMQL.

La estructura Prelude→Recurrent Block→Coda se conserva como referencia conceptual, con la advertencia original: un bloque recurrente dentro de pesos/modelo no debe confundirse con una capa de orquestación externa. Para agentes sobre LLM ya entrenado se usan patrones Self-Refine, Reflexion, ToT, GoT o ciclos condicionales.

## Componentes OSS de referencia preservados

| Función | Opciones de referencia |
|---|---|
| FSM | transitions / XState |
| Router | semantic-router / RouteLLM |
| Sheriff/Policy | OPA / Cerbos / Casbin |
| Sentinel | Guardrails AI / NeMo Guardrails / Llama Guard / Presidio |
| Verifier | PydanticAI / Guardrails / jsonschema |
| Critic | Self-Refine / Reflexion / CRITIC |
| Judge | TruLens / DeepEval / Ragas / Prometheus |
| Retry | Tenacity / backoff / Stamina |
| Orquestación stateful | LangGraph |
| Reasoning compiler | DSPy |
| Memoria | Letta / Mem0 |
| Durabilidad | Temporal / Dagu |
| Observabilidad | Langfuse / OpenTelemetry |
| Sandbox | E2B / gVisor / Firecracker |
| Multi-model routing | LiteLLM |

## OpenClaw/Hermes — referencias originales preservadas

| Componente | Referencia original | Uso |
|---|---|---|
| identidad + memoria | Letta | identidad/core memory + archival memory |
| memoria episódica ligera | Mem0 / Zep | memoria enchufable |
| delegación | CrewAI / AutoGen/AG2 | protocolo multiagente |
| razonamiento durable | LangGraph | grafo/checkpoint |
| gateway multicanal | n8n | entrada de canales |
| skills instalables | MCP + registry | descubrimiento de herramientas |
| heartbeat | APScheduler / cron + durable engine | activación periódica |
| framework integral | Agno | referencia de memoria/equipos/tools/knowledge |

Estas son referencias/candidatos históricos; cualquier incorporación efectiva requiere auditoría actual de licencia, seguridad, disponibilidad y compatibilidad.

## Qué existe y qué falta — matriz original preservada

| Área | Evidencia original | Estado original | Falta demostrable |
|---|---|---:|---|
| Árbol PLAN_100 | Scaffold materializado | PARCIAL | Sustituir ESQ por cuerpos reales y probarlos |
| Hot path de programación | `extensions/wordflow/engine/code_path_runner.py` | REAL | Mantener hasta paridad de tests |
| Pipeline de programación | `programming_pipeline.py` y módulos asociados | REAL/PARCIAL | Cadena integral verificada |
| Kernel Wordflow | `extensions/wordflow_kernel/` | PARCIAL | Adaptadores reales y pruebas E2E |
| Router de inteligencia | `gateway/intelligence.py`, `router_http.py` | PARCIAL | Providers reales y failover probado |
| Motor modular p01–p12 | Declarado/documentado | FALTANTE | Archivos ejecutables p01–p12 |
| OpenClaw/Hermes auxiliares | Archivos stub | ESQ | Adaptadores funcionales |
| Índice de símbolos | Referenciado | FALTANTE | Export Markdown verificable |
| Esquemas por etapa | Parciales/globales | FALTANTE | Contratos input/output por etapa |
| Índice test→assert | No demostrado | FALTANTE | Trazabilidad requisito→test→assert |
| Evidencia CI en observabilidad | Dispersa | PARCIAL | Ingesta en `trace-history` |
| Estado global persistente | Fragmentado | PARCIAL | Máquina durable única |
| GapRegistry persistente | Parcial | PARCIAL | Persistencia y transición probada |
| FourPassController global | Documentos/piezas | PARCIAL | Controlador único ejecutable |
| Recepción y handoff | Parcial | PARCIAL | Auto-load y handoff verificable |
| Cadena DOC→OUTPUT | No cerrada E2E | FALTANTE | DOC→REQ→CODE→TEST→EVIDENCE→OUTPUT_CONSUMED |
| Historial append-only | Ledger parcial | PARCIAL | Garantía y prueba de inmutabilidad |
| Protección post-verify | No cerrada | PARCIAL | Sin bypass y defaults seguros |

## Veredicto de cuatro pasadas — original preservado

1. **STRUCTURE:** árbol objetivo descrito/materializado con refs/placeholders; no prueba implementación completa.
2. **CONNECTIVITY:** puntos de conexión reales con catálogos/rutas/dual homes/dependencias pendientes.
3. **BEHAVIOR:** hot path real; evidencia insuficiente para toda la arquitectura nueva.
4. **FORENSIC_CLOSURE:** `FAIL-CLOSED / PARCIAL`; PASS de descargas/carpetas/actions no cierra gaps de runtime.

## Regla de evolución original

No mover ni reescribir `extensions/wordflow/engine/code_path_runner.py` hasta paridad de imports, contratos, tests y evidencia. Ruta: **REUSE → COPY con SHA → ADAPT → TEST → CUTOVER**, manteniendo trazabilidad origen→destino.

## Auditoría forense TEAM/SDPA — fuentes, cableado y GAPS

Se preservan las cuatro auditorías originales:

1. [Auditoría 01 — Estructura](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-01-ESTRUCTURA-XRAY-2026-09-01.md)
2. [Auditoría 02 — Conectividad](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-02-CONECTIVIDAD-XRAY-2026-09-01.md)
3. [Auditoría 03 — Comportamiento](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-03-COMPORTAMIENTO-XRAY-2026-09-01.md)
4. [Auditoría 04 — Cierre y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-04-CIERRE-GAPS-XRAY-2026-09-01.md)

### Fuentes SDPA preservadas

- [SDPA Architecture Document](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/SDPA_Architecture_Document.md)
- [Resumen de la propuesta SDPA](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/RESUMEN-PROPUESTA-SDPA.md)

### Localización original del código TEAM

```text
PIPELINE/03_TEAM_KERNEL_PARTE1.md                  diseño TEAM v3
PIPELINE/06_PERFIL_MAESTRO_TEAM_SEALS.md           perfil maestro
PIPELINE/10_KERNEL_THOUGHT_PROTOCOL.md              protocolo de pensamiento
extensions/wordflow_kernel/                         kernel de control real/parcial
extensions/wordflow/                                runtime y hot path real
agente-yaiwes/kernel-principal/                     espejo/scaffold parcial
control-layer/                                      contratos, council y evolution
Agente core kernel Yaiwes principal/                ZIP de componentes; no runtime
```

### Resultado TEAM/SDPA original preservado

- TEAM tiene diseño documental y piezas funcionales, pero no se consideró paquete/runtime autónomo completo.
- `extensions/wordflow_kernel/`: 94 Python, 27 tests, base reutilizable según la auditoría original.
- `agente-yaiwes/kernel-principal/`: 49 Python, 18 placeholders, 0 tests propios según la auditoría original.
- `Agente core kernel Yaiwes principal/`: 502 ZIP; inventario, no kernel instalado.
- OpenClaw y Hermes aparecían como stubs.
- Defaults Fake/Mock demostraban interfaces, no producción.
- SDPA se marcó incompleto: DecisionEngine único, Ask-Consil 12 ejecutable, Merkle State global, AST universal, Inventory unificado, merge semántico y verificación integral pendientes.

**Veredicto histórico TEAM/SDPA:** `FAIL-CLOSED / PARCIAL`.

## Auditoría corregida por cada raíz del Crazy Wall — referencias originales preservadas

- [Índice maestro — seis raíces YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/INDICE-AUDITORIA-XRAY-SEIS-RAICES-YAIWES-2026-09-01.md)
1. [R1 — Desplegar](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R1-DESPLEGAR-XRAY-2026-09-01.md)
2. [R2 — PIPELINE](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R2-PIPELINE-XRAY-2026-09-01.md)
3. [R3 — Método de trabajo](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R3-METODO-TRABAJO-XRAY-2026-09-01.md)
4. [R4 — Refactoria](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R4-REFACTORIA-XRAY-2026-09-01.md)
5. [R5 — YAIWES / Agente TEAM / Kernel](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R5-YAIWES-TEAM-KERNEL-XRAY-2026-09-01.md)
6. [R6 — Wordflow Code](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R6-WORDFLOW-CODE-XRAY-2026-09-01.md)

Los HTML originales utilizados como mapa permanecen preservados y enlazados desde el índice.
