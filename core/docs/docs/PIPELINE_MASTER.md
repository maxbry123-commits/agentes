---
# PIPELINE MASTER — Componentes del Orquestador Universal v1.0

## Metadata

- Versión: 1.0
- Estado: MVP funcional
- 5 documentos MD + 12 archivos .py
- 10 Loops, 16 Razonamiento, 16 Recuperación
- 10 Goals enforced

## Componentes

### 1. DSL Engine (`orchestrator.py::DSLEngine`)
- Decorador `@node(id, depends_on, gate, sandbox, repair_max)`
- Parsea definición declarativa de nodos
- Valida: ids únicos, depends_on existen, gates existen en Sheriff

### 2. DAG Engine (`orchestrator.py::DAGEngine`)
- `networkx.DiGraph` con add_node, add_edge
- `topological_order()` para orden de ejecución
- `has_cycles()` para validación pre-flight
- `get_dependents(node_id)` para repair (qué nodos re-ejecutar)

### 3. State Machine (`state.py::WorkflowState`)
- Dataclass con: input_data, goal_hash, completed_nodes, current_node, retry_counts
- `persist()`: escritura atómica con fsync + os.replace
- `load()`: reanuda desde workflow_state.json
- Thread-safe con lock

### 4. Sheriff (`sheriff.py::Sheriff`)
6 gates:
- **completitud**: output es dict, tiene `status` ∈ {ok, completed, success}
- **coherencia**: tipos correctos (tasks=list, teams_created=dict, document_index=list)
- **formato**: required_fields presentes en output
- **sandbox_isolation**: sandbox_id del output == sandbox_id esperado
- **repairs_ok**: repair_count[node] < repair_max
- **approval**: state.approvals[node_id] == "GO"

### 5. Sentinel (`sentinel.py::Sentinel`)
- `events[]`: lista acotada a 5000, FIFO
- `node_executions{}`: counter por node_id
- `LOOP_THRESHOLD=10`, `DEADLOCK_THRESHOLD=20`
- `metrics()`: total_events, loops, deadlocks, uptime

### 6. Juez (`juez.py::Judge`)
3 simulaciones:
- **real**: ejecuta la app/tests, verifica que pass
- **adversarial**: fuzzing + inputs maliciosos (null, overflow, unicode raro)
- **regression**: compara status con baseline_output.json
- Si 3/3 GO → atomic_write_json(baseline_output.json, ...)

### 7. Validador (`sheriff.py::Validador`)
- Contrato JSON: required_fields[], type_map{field: type}
- Valida output del nodo contra contrato
- Devuelve {valid, missing[], type_errors[]}

### 8. Verificador (`sheriff.py::Verificador`)
- Ejecuta tests/lint/diff **dentro del sandbox**
- Output: {pass, errors[], coverage, duration}
- Si pass=False → trigger repair

### 9. Supervisor (`sandbox.py::Supervisor`)
- Lifecycle de sandboxes: start, health_check, kill, restart, destroy
- Circuit breaker por sandbox (5 fallos → open 60s)
- Cleanup de contenedores huérfanos al startup
- Scrub de secrets en logs

### 10. Consensus (`consensus.py::Consensus`)
- 3 sandboxes paralelos (Claude, Mimo, OpenCode)
- Cada uno propone: plan, dependencias, riesgos
- Juez compara y elige el plan 2-de-3
- Si los 3 disienten → escala a Director

### 11. Repair (`repair.py::RepairEngine`)
- Implementa F1-F16
- Counter por nodo: repair_count[node]
- Si counter < 2 → F7 con nuevo error
- Si counter == 2 → escalate

### 12. Router (`router.py::Router`)
- Asigna sandbox por sub-tarea
- Criterio: round-robin o capacidad (CPU/RAM)
- Respeta circuit breaker (skip si open)
- Devuelve: {sandbox_id, agent_type, expected_loop}

## Archivos Python

| Archivo | Líneas | Función |
|---------|--------|---------|
| orchestrator.py | ~400 | loop engine, goal/scope lock, DSL/DAG/state |
| router.py | ~150 | asignación de sandboxes |
| sandbox.py | ~200 | docker wrapper + supervisor |
| sheriff.py | ~200 | 6 gates + validador + verificador |
| sentinel.py | ~150 | eventos, loops, métricas |
| juez.py | ~180 | 3 simulaciones + baseline |
| consensus.py | ~120 | 2-de-3 |
| repair.py | ~180 | F1-F16 |
| state.py | ~150 | workflow_state atómico |
| agents/base.py | ~60 | ABC |
| agents/claude_code.py | ~80 | wrapper claude |
| agents/mimo_code.py | ~80 | wrapper mimo |
| agents/opencode.py | ~60 | wrapper opencode |
| main.py | ~80 | CLI + demo |
| tests/test_mvp.py | ~200 | smoke test |
| **TOTAL** | **~2230** | MVP funcional |

## Reglas de estado

- **P0-1**: escritura atómica con `atomic_write_json` (fsync + os.replace)
- **P0-2**: graceful shutdown con `install_shutdown_handlers` (SIGTERM/SIGINT)
- **P0-3**: circuit breaker por sandbox (5 fallos → open 60s)
- **P0-4**: exponential backoff en retry (base 0.5, cap 10, jitter 10%)
- **P0-5**: DSL validator pre-flight
- **P0-6**: dead letter queue (dead_letter.json) en escalations
- **P0-7**: compensate en @node decorator (rollback si falla)
- **P0-8**: health check (health.json) por nodo

## Cómo se ejecuta

```bash
cd /workspace/orchestrator-universal
python main.py --template template.json
```

O programáticamente:

```python
from orchestrator import run_orchestrator

template = {
    "objetivo": "construir API REST",
    "planificar": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10"],
    "organizar": { ... },
    "tareas": [...],
    "metas": [...],
    "proposito": "...",
    "refutaciones": [...],
    "consensus": "fast"  # o "single" o "full"
}

result = run_orchestrator(template)
print(result["status"])  # "ok" o "fail"
print(result["completed_loops"])
```
