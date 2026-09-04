# README — Arquitectura fusionada YAIWES · X-Ray

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Base original:** arquitectura fusionada X-Ray 2026-09-01  
**Actualización forense:** 2026-09-03  
**Regla:** GitHub y el código ejecutable son la verdad. Una carpeta o documento no demuestra que una capacidad esté operativa.

> Este `README.md` es la arquitectura canónica única de `Readme arquitectura Yaiwes/`. Las tareas, checkpoints, instrucciones del Director, instrucciones literales de Claude, notas de agentes y estado operativo se mantienen fuera de la arquitectura, dentro de `Crazy Wall Orquestador/`.

## 1. Fuentes fusionadas y trazabilidad

### Arquitectura/código previo
1. `Readme arquitectura estructura raíz de agente Yaiwes wordflow.md`
2. `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`
3. `agente-yaiwes/STRUCTURE.md`
4. `agente-yaiwes/README.md`
5. `PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md`
6. `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
7. `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md`
8. `PIPELINE/FORENSE_PASADA_01_STRUCTURE.md`
9. `PIPELINE/FORENSE_PASADA_02_CONNECTIVITY.md`
10. `PIPELINE/FORENSE_PASADA_03_BEHAVIOR.md`
11. `PIPELINE/FORENSE_PASADA_04_CIERRE.md`

### Lote 1 — documentos de arquitectura YAIWES
La revisión incorpora el inventario completo de `Documentos arquitectura Yaiwes lote 1/`, incluyendo Mythos/Fables, Muse, Rufo, PLAN YAIWES, core kernel de razonamiento, diagramas v0–v3.1, Ley Principal TEAM, MAVIS/MAX-SYSTEM, orquestador, memoria Wordflow y el documento de faltantes de kernel/extensión-kernel.

El documento `PLAN_YAIWES_AGENTE_WORDFLOW.md` reafirma como reglas: no inventar planes paralelos; no reescribir el hot path sin paridad; aplicar regla lego; reutilizar `goal_lock.py`, `cognitive_loop.py` y `evidence_packet.py` por referencia; usar `gateway/intelligence.py` + `router_http.py` como punto de enchufe; y terminar/cablear p01→p12 en vez de rehacerlos.

### Instrucciones Claude
Se cruzan literalmente los documentos 01–09 de `Documentos proyectos Yaiwes instrucciones de Claude/`: bloques 1–4, arquitectura Fables, investigación OSS, Loops/Multi-API/Memoria/Chat, protocolo de cierre simple y guía de integración de código.

La lista operativa Claude 1–90 fue retirada de este README y conservada 1:1 en `Crazy Wall Orquestador/INPUT-CLAUDE-LITERAL/`.

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

Este README describe exclusivamente arquitectura y su estado X-Ray. El backlog completo Claude 1–90, instrucciones literales del Director, checkpoints, prompts de agentes, estado JSON, notas y plan viven en `Crazy Wall Orquestador/`.

El siguiente paso arquitectónico no es diseñar otra capa: es completar el inventario componente→destino con evidencia, someter la primera integración al Director y ejecutar el ciclo aprobado de movimiento→verificación→Codex→auditoría.
