# Guía de Integración — Objective Engine v2 en el Kernel YAIWES/MAXBRY

> **Versión:** 2.0.0-ALPHA  
> **Fecha:** 2026-08-16  
> **Audiencia:** Agentes LLM (Grok, Claude, Gemini, etc.), desarrolladores, arquitectos  
> **Objetivo:** Saber EXACTAMENTE dónde va cada archivo y cómo se conecta todo

---

## 1. Estructura del Kernel Recomendada

```
yaiwes-kernel/
├── kernel/
│   ├── __init__.py
│   ├── core/                           # Núcleo del sistema
│   │   ├── __init__.py
│   │   ├── config.py                   # Configuración global
│   │   ├── exceptions.py               # Excepciones custom del kernel
│   │   └── logger.py                   # Logging estructurado
│   │
│   ├── objective_engine/               # MOTOR DE OBJETIVOS v2
│   │   ├── __init__.py
│   │   ├── objective_engine.py         # ORQUESTADOR PRINCIPAL
│   │   │   └── Clase: ObjectiveEngine
│   │   │   └── API: run(), replan(), get_status(), export_audit()
│   │   │
│   │   ├── objective_graph.py          # GRAFO COMPUESTO
│   │   │   └── Clases: ObjectiveGraph, ObjectiveNode, ObjectiveEdge
│   │   │   └── Funciones: detect_cycles(), critical_path(), parallel_levels()
│   │   │
│   │   ├── plan_compiler.py            # COMPILADOR DE PLANES
│   │   │   └── Clases: PlanCompiler, ExecutionDAG, ExecutionNode
│   │   │   └── Pipeline: 8 pasos de validación → DAG inmutable
│   │   │
│   │   ├── plan_validator.py           # VALIDADOR MULTI-CAPA
│   │   │   └── Clases: PlanValidator, ValidationReport, ValidationIssue
│   │   │   └── Funciones: validate_graph(), auto_repair()
│   │   │
│   │   ├── objective_memory.py         # MEMORIA DE ESTRATEGIAS
│   │   │   └── Clases: ObjectiveMemory, StrategyRecord, ConsolidatedPattern
│   │   │   └── Funciones: store(), find_similar(), rank_strategies(), consolidate()
│   │   │
│   │   ├── objective_runtime.py        # RUNTIME DE EJECUCIÓN
│   │   │   └── Clases: ExecutionRuntime, WorkerPool, ExecutionResult
│   │   │   └── Funciones: execute(), pause(), resume(), cancel(), resume_from_checkpoint()
│   │   │
│   │   ├── objective_recovery.py       # MOTOR DE RECUPERACIÓN
│   │   │   └── Clases: RecoveryEngine, FailureClassification, AdaptationStrategy
│   │   │   └── Funciones: classify_failure(), analyze_gap(), decide_adaptation(), local_replan()
│   │   │
│   │   └── signals.py                  # SISTEMA DE SEÑALES
│   │       └── Clases: SignalBus, SignalType
│   │       └── Señales: PAUSE, RESUME, CANCEL, APPROVE, REVERT, CHECKPOINT
│   │
│   ├── dsl/                            # DSL de 12 GOALS
│   │   ├── __init__.py
│   │   ├── goals.py                    # Definición de los 12 GOALS
│   │   ├── parser.py                   # Parser del DSL
│   │   └── validator.py              # Validador de DSL
│   │
│   ├── llm/                            # Interfaz LLM
│   │   ├── __init__.py
│   │   ├── client.py                   # Cliente LLM genérico
│   │   ├── prompts/                    # Prompts estructurados
│   │   │   ├── objective_discovery.txt
│   │   │   ├── objective_decompose.txt
│   │   │   ├── failure_classify.txt
│   │   │   └── strategy_synthesize.txt
│   │   └── embeddings.py               # Generación de embeddings
│   │
│   ├── workers/                        # WORKERS POLYGLOT
│   │   ├── __init__.py
│   │   ├── base.py                     # Interfaz base de worker
│   │   ├── python_worker.py            # Worker Python
│   │   ├── shell_worker.py             # Worker Shell
│   │   ├── llm_worker.py               # Worker LLM (llamadas a modelo)
│   │   └── registry.py                 # Registro de workers disponibles
│   │
│   ├── persistence/                    # CAPA DE PERSISTENCIA
│   │   ├── __init__.py
│   │   ├── checkpoint_store.py         # Almacén de checkpoints
│   │   ├── audit_store.py              # Almacén de audit logs
│   │   └── memory_store.py             # Almacén de memoria (JSONL)
│   │
│   ├── observability/                  # OBSERVABILIDAD
│   │   ├── __init__.py
│   │   ├── tracer.py                   # OpenTelemetry tracer
│   │   ├── metrics.py                  # Métricas de ejecución
│   │   └── dashboard.py                # Dashboard interno
│   │
│   └── security/                       # SEGURIDAD Y ÉTICA
│       ├── __init__.py
│       ├── guardrails.py               # Guardrails de objetivos
│       ├── sandbox.py                  # Sandbox de ejecución
│       └── ethics.py                   # Comité de ética (simulado)
│
├── tests/
│   ├── unit/
│   │   ├── test_objective_graph.py     # Tests de grafo
│   │   ├── test_plan_compiler.py       # Tests de compilación
│   │   ├── test_plan_validator.py      # Tests de validación
│   │   ├── test_objective_memory.py    # Tests de memoria
│   │   ├── test_objective_runtime.py   # Tests de runtime
│   │   └── test_objective_recovery.py  # Tests de recuperación
│   │
│   ├── integration/
│   │   ├── test_full_pipeline.py       # Test del pipeline completo
│   │   ├── test_parallel_execution.py  # Test de paralelismo
│   │   └── test_checkpoint_recovery.py # Test de checkpoint + recovery
│   │
│   └── dsl/
│       └── test_12_goals.py            # Tests de los 12 GOALS del DSL
│
├── data/
│   ├── objective_memory/               # Persistencia de memoria
│   │   ├── records.jsonl
│   │   └── patterns.jsonl
│   ├── checkpoints/                    # Checkpoints de ejecución
│   └── audit_logs/                     # Logs de auditoría
│
├── docs/
│   ├── architecture.md                 # Documentación de arquitectura
│   ├── api_reference.md                # Referencia de API
│   └── deployment.md                   # Guía de despliegue
│
├── requirements.txt
├── setup.py
└── README.md
```

---

## 2. Mapa de Dependencias entre Módulos

```
┌─────────────────────────────────────────────────────────────────┐
│                    objective_engine.py                            │
│                    (ORQUESTADOR PRINCIPAL)                        │
├─────────────────────────────────────────────────────────────────┤
│  Usa:                                                           │
│    ├── objective_graph.py  ←── Construye el grafo               │
│    ├── plan_validator.py   ←── Valida antes de compilar         │
│    ├── plan_compiler.py    ←── Compila a ExecutionDAG           │
│    ├── objective_runtime.py ←── Ejecuta el DAG                  │
│    ├── objective_recovery.py ←── Maneja fallos                  │
│    └── objective_memory.py  ←── Almacena/aprende estrategias    │
└─────────────────────────────────────────────────────────────────┘
         ↑
    ┌────┴────┐
    │  llm/   │  ←── objective_engine usa llm_client para enriquecer objetivos
    └─────────┘
         ↑
    ┌────┴────┐
    │ workers/│  ←── objective_runtime usa workers para ejecutar tareas
    └─────────┘
         ↑
    ┌────┴────┐
    │persistence│ ←── objective_memory y runtime usan para guardar estado
    └─────────┘
```

---

## 3. Instrucciones Paso a Paso para Integrar

### Paso 1: Crear la estructura de directorios

```bash
mkdir -p yaiwes-kernel/kernel/{objective_engine,dsl,llm,workers,persistence,observability,security}
mkdir -p yaiwes-kernel/tests/{unit,integration,dsl}
mkdir -p yaiwes-kernel/data/{objective_memory,checkpoints,audit_logs}
```

### Paso 2: Copiar los 8 módulos principales

Copia cada archivo del documento de código a su ubicación:

| Documento fuente | Archivo destino | Prioridad |
|------------------|-----------------|-----------|
| 04_objective_engine.py.md | kernel/objective_engine/objective_engine.py | CRÍTICA |
| 05_objective_graph.py.md | kernel/objective_engine/objective_graph.py | CRÍTICA |
| 06_plan_compiler.py.md | kernel/objective_engine/plan_compiler.py | CRÍTICA |
| 07_plan_validator.py.md | kernel/objective_engine/plan_validator.py | CRÍTICA |
| 08_objective_memory.py.md | kernel/objective_engine/objective_memory.py | CRÍTICA |
| 09_objective_runtime.py | kernel/objective_engine/objective_runtime.py | CRÍTICA |
| 10_objective_recovery.py | kernel/objective_engine/objective_recovery.py | CRÍTICA |

### Paso 3: Crear __init__.py del package

```python
# kernel/objective_engine/__init__.py

from .objective_engine import ObjectiveEngine, EngineResult, ObjectiveDescriptor
from .objective_graph import ObjectiveGraph, ObjectiveNode, EdgeType
from .plan_compiler import PlanCompiler, ExecutionDAG
from .plan_validator import PlanValidator, ValidationReport
from .objective_memory import ObjectiveMemory, StrategyRecord
from .objective_runtime import ExecutionRuntime, ExecutionResult
from .objective_recovery import RecoveryEngine, FailureClassification

__all__ = [
    "ObjectiveEngine",
    "ObjectiveGraph",
    "PlanCompiler",
    "PlanValidator",
    "ObjectiveMemory",
    "ExecutionRuntime",
    "RecoveryEngine",
]
```

### Paso 4: Implementar stubs de dependencias

Los módulos asumen ciertas dependencias que debes implementar:

**A. LLM Client (kernel/llm/client.py)**
```python
class LLMClient:
    async def generate(self, prompt: str, **kwargs) -> str:
        # Tu implementación de LLM (OpenAI, Anthropic, local, etc.)
        pass

    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        # Generar JSON estructurado
        pass
```

**B. Worker Registry (kernel/workers/registry.py)**
```python
class WorkerRegistry:
    def get_worker(self, action_type: str):
        # Retorna un callable que ejecuta la acción
        pass
```

**C. Checkpoint Store (kernel/persistence/checkpoint_store.py)**
```python
class CheckpointStore:
    async def save(self, execution_id: str, checkpoint_data: dict):
        pass

    async def load(self, execution_id: str, checkpoint_id: str) -> dict:
        pass
```

### Paso 5: Implementar los 12 GOALS del DSL

```python
# kernel/dsl/goals.py

from enum import Enum

class GoalType(Enum):
    """Los 12 GOALS del DSL de YAIWES."""
    DISCOVER = "discover"           # G1: Descubrir objetivos
    DECOMPOSE = "decompose"         # G2: Descomponer objetivos
    VALIDATE = "validate"           # G3: Validar planes
    COMPILE = "compile"             # G4: Compilar a DAG
    EXECUTE = "execute"             # G5: Ejecutar tareas
    OBSERVE = "observe"             # G6: Observar resultados
    EVALUATE = "evaluate"           # G7: Evaluar postcondiciones
    CLASSIFY = "classify"           # G8: Clasificar fallos
    ADAPT = "adapt"                 # G9: Adaptar estrategia
    REPLAN = "replan"               # G10: Replanificar
    MEMORIZE = "memorize"           # G11: Almacenar en memoria
    EVOLVE = "evolve"               # G12: Evolucionar objetivos
```

### Paso 6: Test mínimo de integración

```python
# tests/integration/test_full_pipeline.py

import asyncio
import pytest
from kernel.objective_engine import ObjectiveEngine

@pytest.mark.asyncio
async def test_full_pipeline_simple():
    engine = ObjectiveEngine(worker_pool_size=2)

    result = await engine.run(
        root_objective="Calcular la suma de 2+2",
        context={"auto_decompose": False},
    )

    assert result.success is True
    assert result.root_objective is not None
    assert result.execution_dag is not None
    assert len(result.audit_log) > 0
```

### Paso 7: Configurar persistencia

```python
# kernel/core/config.py

from dataclasses import dataclass

@dataclass
class KernelConfig:
    objective_engine_workers: int = 4
    objective_engine_max_retries: int = 3
    objective_memory_path: str = "data/objective_memory"
    checkpoint_interval: int = 1
    enable_guardrails: bool = True
    enable_audit_logging: bool = True
```

---

## 4. Conexiones con el Sistema Existente

### 4.1 Flujo de Datos Completo

```
ANTES (v1):
    [Discovery Engine] → [Plan Lineal] → [Ejecución Secuencial]

DESPUÉS (v2):
    [Discovery Engine] ──→ [ObjectiveNormalizer] ──→ [EvidenceEngine]
                                                      ↓
                                              [ObjectiveGraph]
                                                      ↓
                                              [PlanValidator]
                                                      ↓
                                              [PlanCompiler]
                                                      ↓
                                              [ExecutionRuntime]
                                                      ↓
                                              [Evaluator]
                                                      ↓
                                    ┌─────────────────┴─────────────────┐
                                    ↓                                   ↓
                              [Success]                           [Failure]
                                    ↓                                   ↓
                              [Memory]                          [Recovery]
                                                                      ↓
                                                                  [Replan]
                                                                      ↓
                                                              [Next Loop]
```

### 4.2 Puntos de Integración con el Kernel Existente

| Componente Existente | Punto de Conexión | Tipo de Conexión |
|---------------------|-------------------|------------------|
| Context Manager | ObjectiveEngine.run(context=...) | Input |
| LLM Bridge | llm_client pasado al constructor | Dependencia |
| Tool Registry | node_executor en ExecutionRuntime | Callback |
| Auth/Permissions | Guardrails en PlanValidator | Middleware |
| Audit Logger | export_audit() + _audit_log | Output |
| State Store | CheckpointStore + ObjectiveMemory | Persistencia |
| Metrics | ExecutionResult + tracer | Observabilidad |

---

## 5. Checklist de Integración para Agentes Externos

Si eres Grok, Claude, Gemini u otro agente integrando esto, verifica:

- [ ] Los 7 archivos .py están en kernel/objective_engine/
- [ ] Los __init__.py exportan las clases principales
- [ ] El LLMClient está implementado y conectado
- [ ] El WorkerRegistry tiene al menos un worker por tipo de tarea
- [ ] Los tests de los 12 GOALS pasan
- [ ] La persistencia (data/) tiene permisos de escritura
- [ ] Los guardrails de seguridad están activados
- [ ] El audit logging está habilitado
- [ ] Los checkpoints se guardan correctamente
- [ ] La memoria de estrategias persiste entre reinicios

---

## 6. Notas para el Mantenedor

> **Regla de Oro:** Nunca modificar un ExecutionDAG en runtime. Si necesitas cambiar el plan, detén la ejecución, genera un nuevo ObjectiveGraph, recompila y reejecuta.
>
> **Regla de Plata:** Todo cambio de objetivo debe pasar por ObjectiveEvolution con OLD → NEW → REASON → EVIDENCE → TIMESTAMP.
>
> **Regla de Bronce:** El LLM nunca ejecuta directamente. Siempre compila a ExecutionDAG primero.

---

*Guía de integración generada por Kimi K3 — Mapa completo del kernel*
