# PIPELINE 03 — TEAM KERNEL v3.0 (Parte 1/3)

**Fecha:** 2026-08-09  
**Estado:** PERFIL INCORPORADO  
**Proyecto:** TEAM Kernel (MAXBRY)  
**Versión:** 3.0 (basado en 44 documentos S1-S16)  
**Regla central:** 0% LLM en el núcleo · 90/10 determinista/razonamiento  
**Unidad:** TODO es una FICHA (Enchufe v2.0)

---

## 1. Diagrama Horizontal Transversal

```
INPUT
  → InputBlockReader (Hash Chain)
  → MissionBuilder (GOAL_LOCK)
  → DSL→DAG Compiler (Autoensamblaje)
  → ContractSelector (Fingerprint→Threat→Rules→Graph→Reverse)
  → Sheriff 5 Estados (GREEN/YELLOW/ORANGE/RED/BLACK)
  → Scheduler (Sharding + Time-Wheel)
  → Multi-API Fabric (SINGLE/RACE/QUORUM/SPLIT) + Fleet Manager
  → Ejecución Paralela (Worktrees + Sandbox Pool)
  → Auditoría 3 Capas (Adversarial→Cruzada→Maker-Checker)
  → MYTHOS 40 pasos (14 D / 16 P / 10 H)
  → Recovery 5 Niveles (RETRY→ROLLBACK→CHECKPOINT→REPLAN→ESCALATE)
  → CAPA_7 Witness (Evidencia L1-L4 + evidence_hash)
  → CERTIFICACIÓN (30/30 Checks)
```

---

## 2. Estructura de Datos Nuclear

### 2.1 Enchufe v2.0 (Ficha Universal)

```python
@dataclass
class Ficha:
    artifact_id: str
    version: str
    estado: str          # draft | testing | active | deprecated | revoked
    categoria: str       # pipeline | transversal | acelerador
    rol: str             # source | transform | sink | service
    consume: Dict[str, str]
    expone: Dict[str, str]
    ejecucion: Dict
    presupuesto: Dict
    firma_gpg: str
    failover: Dict
```

### 2.2 Contract Engine (85 contratos)

- `Contract` (id C00..C85, capa L1..L8, severity, trigger, requires, failure_action)
- `Fingerprint` (network, write, secret, external, irreversible, parallel, cross_system)
- `ThreatScore` (data_risk + op_risk + ext_risk)

### 2.3 Sheriff 5 Estados

```
GREEN = aprobado
YELLOW = revisión
ORANGE = shadow (3 shadow ok → GREEN)
RED = rechazado
BLACK = bloqueado (solo Director lo levanta)
```

### 2.4 MYTHOS Engine (40 pasos)

- 14 D (determinista, 0% LLM)
- 16 P (probabilístico, 100% LLM cápsula)
- 10 H (híbrido)

### 2.5 Agent Adapter (Flota)

Contrato obligatorio: `execute`, `health`, `capabilities`, `limits`, `contracts_supported`, `sandbox_profile`, `evidence_output`.

### 2.6 State Engine (Event Sourcing)

Campos: meta, mision, plan, flota, loops, sandboxes, memoria, evidencia, sheriff.

---

## 3. Mapa de Módulos (LOC + Función)

| Bloque | Módulo | LOC | Función |
|--------|--------|-----|---------|
| S3 | enchufe/validator_v2.py | 260 | 36 invariantes |
| S4 | registry/store.py | 150 | Fuente única de verdad |
| S5 | sheriff/checks.py | 220 | 22 checks + FSM 5 estados |
| S6 | kernel/mission.py | 130 | GOAL_LOCK + clasificador |
| S7 | kernel/dsl.py + dag.py | 290 | DSL→DAG, autoensamblaje |
| S9 | kernel/scheduler.py + runtime.py | 240 | Ejecuta DAG, 0% LLM |
| S11 | openclaw_plugin/bridge.py | 150 | Intercepta turn de OpenClaw |
| S12 | memory/runtime.py | 140 | 9 memorias |
| S13 | witness/packager.py | 80 | CAPA_7 + evidence_hash |
| S15 | capsulas/base.py | 120 | Cápsulas LLM (44 gates) |
| S16 | recovery/ladder.py | 140 | 5 niveles + checkpoint |
| S18 | ker/loader.py | 130 | Extension Loader |
| S27 | absorb/license_auditor.py | 110 | Filtro legal |
| S28 | absorb/extractor.py | 150 | AST quirúrgico |
| S33 | parallel/pool.py | 60 | MavisPool |
| S38c | parallel/timewheel.py | 70 | O(1) triggers |
| S39 | inputblock/store.py | 120 | Hash chain + TTL |
| S45 | llmnet/fanout.py | 150 | RACE/QUORUM/SPLIT |
| S46 | fleet/manager.py | 150 | Flota nativa |
| S51 | loops/claude_loop.py | 140 | ReAct 9 fases |
| S52 | sentinela/core.py | 90 | Auto-mejora aislada |
| S53 | state/engine.py | 130 | Atomic write + replay |
| S54 | corazon/snapshot.py | 110 | Snapshot cada N acciones |
| S55 | mythos/orquestador.py | 140 | 40 pasos + replan |

**Total estimado:** ~3.400 LOC (motor) + 85 YAML contratos + adapters.

---

## 4. Reglas de Oro (L01-L15 + 90/10)

```yaml
L01: Investigar OSS antes de proponer código nuevo
L02: Un archivo = una responsabilidad (≤200 líneas)
L03: Nunca borrar código → feature flags
L04: Flags SOLO en config.py
L05: Nunca inventar APIs → solo lo verificable
L06: Dependencias con versión exacta
L07: Archivos nuevos = aprobación del Director
L08: Nunca saltar el DAG
L09: Ejecución solo en sandbox declarado
L10: Estado → solo vía eventos (nunca directo)
L11: Toda tarea genera evidencia o no existió
L12: Toda salida pasa por Tribunal
L13: Anti-scope-creep: solo lo pedido
L14: Ambigüedad → 1 pregunta concreta
L15: Mismo input → mismo output (reproducibilidad)

determinista (90%):
  Scheduler · DSL DAG · Sheriff · Memory · Workflow Engine
  Capability/Plugin/Skill Compiler · Harness Manager
  Recovery · Rollback · Trazabilidad

llm_capsulas (10%):
  Council / consenso
  Investigación compleja
  Generación inicial sin plantilla
  Resolver ambigüedad
```

---

## 5. Punto de Entrada (main.py — esquema)

```python
kernel = TeamKernel()
sheriff = Sheriff(contracts=ContractCompiler().load_all())
block = InputBlockReader().capture(input_text)
mission = kernel.mission_builder.build(block)
dag = kernel.dsl_compiler.compile(mission)
dag = sheriff.validate(dag)

if dag.estado in (RED, BLACK):
    raise Exception(...)

resultado = MythosOrchestrator().run(dag, level=dag.nivel_cognitivo)
evidencia = kernel.witness.pack(resultado)

if kernel.certify(evidencia).checks == 30:
    return evidencia.final_output
else:
    return kernel.recovery.escalate(evidencia)
```

---

## 6. Gaps detectados (5 pasadas — 8% abierto)

### Documentos faltantes
- S14: Cierre final (42 checks + decisión repos)
- S15: Cápsulas LLM completas (solo parcial)

### Especificación faltante (MYTHOS)
- GAP_27: Paso 03-B (cuerpo de 5 fases F1-F5)
- GAP_29: 26 schemas JSON de salida (pasos P/H)

### Código pendiente
- hybrid_split()
- timewheel.tick() / schedule()
- inyector.inject()
- 3 adapters de flota (aider/cline/codex)
- verificar.py (despliegue)

### Decisiones pendientes del Director
- Estructura de repos (1 vs 8)
- Umbrales Sentinela / Corazón / Council / checkpoints
- Backend Tier 2/3 (SQLite vs Postgres)
- Clones máximos y TTL micro-agente

### Artefactos faltantes
- maps/hermes_memory_map.json (3 memorias nativas)
- contracts YAML faltantes (implementado: false)
- absorb/licenses.yaml
- absorb/surgeon_map.yaml

---

## 7. Micro-diagrama transversal (gobierno)

```
DSL · DAG · Schema · Sheriff · Sentinela · Juez · Supervisor · Validador · Verificador · Orquestador
```

---

## 8. Trazabilidad

- Origen: input block Director (2026-08-09) — “TEAM KERNEL — ESPECIFICACIÓN EJECUTABLE (PARTE 1/3)”
- Incorporado al perfil del PIPELINE
- Próximo: Parte 2/3 (funciones D de MYTHOS + schemas + despliegue)

**Estado:** listo para auditoría.
