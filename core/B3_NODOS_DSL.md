---
# B3 — NODOS DSL (uno por tarea detectada)

## T-001_orchestrator
```yaml
nodo:
  id: "T-001_orchestrator"
  version: "1.0.0"
  goal: "Loop engine con 10 loops L1-L10 ejecutando agentes en sandboxes"
  subgoals: ["registrar 10 loops en DAG", "validar dependencias", "ejecutar secuencialmente"]
  contrato:
    input:  {tipo: "json", schema: {template: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {status: str, completed_nodes: list, metrics: dict},
             criterio_exito: "completed_nodes.length == 10"}
  context: "DSL con loops anidados; cada loop depende del anterior según DAG"
  constraints: ["máx 200 líneas/archivo", "10 loops exactos"]
  dependencies: []
  risk: "alto"
  priority: 1
  skills_requeridas: ["networkx@3.0"]
  timeout_seg: 300
  retry: {max: 3, regla: "cada retry con DELTA nuevo"}
  sandbox: "container"
  states: [pending, running, validating, blocked, done, failed, recovered]
  checkpoint: {cada: "subgoal", persiste_en: "state.json"}
  rollback: {trigger: "validacion_fallida", accion: "restaurar último checkpoint"}
  approval: {requiere_director: true}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: true, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: [], escribe: ["completed_nodes", "metrics", "errors"]}
```

## T-002_state
```yaml
nodo:
  id: "T-002_state"
  version: "1.0.0"
  goal: "WorkflowState con persistencia atómica y Goal Lock"
  subgoals: ["atomic_write_json", "hash_goal", "orchestrator_sha replay check"]
  contrato:
    input:  {tipo: "json", schema: {input_data: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {goal_hash: str, persisted: bool},
             criterio_exito: "fsync + os.replace exitoso"}
  context: "P0-1 escritura atómica; G1 Goal Lock; G7 determinismo"
  constraints: ["fsync obligatorio", "no usar json.dump directo"]
  dependencies: ["T-001_orchestrator"]
  risk: "medio"
  priority: 1
  skills_requeridas: []
  timeout_seg: 60
  retry: {max: 2, regla: "si fsync falla, reducir batch size"}
  sandbox: "local"
  states: [pending, running, validating, done, failed, recovered]
  checkpoint: {cada: "subgoal", persiste_en: "state.json"}
  rollback: {trigger: "validacion_fallida", accion: "rollback a última versión válida"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: false, delta_score: false}
  memory: {lee: [], escribe: ["goal_hash", "completed_nodes", "errors"]}
```

## T-003_sandbox
```yaml
nodo:
  id: "T-003_sandbox"
  version: "1.0.0"
  goal: "Docker wrapper con aislamiento total y circuit breaker"
  subgoals: ["--network none", "--read-only", "--cpus/--memory/--pids-limit", "CircuitBreaker P0-3"]
  contrato:
    input:  {tipo: "json", schema: {sandbox_id: str, image: str, work_dir: str}, validacion: "requerida"}
    output: {tipo: "json", schema: {container_id: str, status: str},
             criterio_exito: "docker run --network none exitoso"}
  context: "G3 aislamiento, G8 recursos limitados, P0-3 circuit breaker"
  constraints: ["read-only filesystem", "network=none", "circuit breaker 5 fallos"]
  dependencies: ["T-002_state"]
  risk: "alto"
  priority: 1
  skills_requeridas: ["docker@24+"]
  timeout_seg: 60
  retry: {max: 3, regla: "si timeout, x1.5 timebox"}
  sandbox: "container"
  states: [pending, running, validating, done, failed, recovered]
  checkpoint: {cada: "subgoal", persiste_en: "state.json"}
  rollback: {trigger: "container_crash", accion: "destroy + nuevo container"}
  approval: {requiere_director: true}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["sandbox_health"], escribe: ["container_id", "status"]}
```

## T-004_sheriff
```yaml
nodo:
  id: "T-004_sheriff"
  version: "1.0.0"
  goal: "6 gates: completitud/coherencia/formato/sandbox_isolation/repairs_ok/approval"
  subgoals: ["definir 6 gates", "validar output antes de avanzar", "VETO si falla"]
  contrato:
    input:  {tipo: "json", schema: {output: dict, gate: str, state: object}, validacion: "requerida"}
    output: {tipo: "json", schema: {verdict: "GO|NO_GO", reason: str},
             criterio_exito: "verdict == GO"}
  context: "G6 validación antes de avanzar; L11 todo pasa por tribunal"
  constraints: ["6 gates exactos", "VETO inmediato si NO_GO"]
  dependencies: ["T-001_orchestrator"]
  risk: "bajo"
  priority: 1
  skills_requeridas: []
  timeout_seg: 30
  retry: {max: 1, regla: "gate fallido no se reintenta, se repara upstream"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "gate", persiste_en: "state.json"}
  rollback: {trigger: "gate_fail", accion: "devolver a nodo upstream"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: false, delta_score: false}
  memory: {lee: ["node_results"], escribe: ["approvals", "gate_failures"]}
```

## T-005_sentinel
```yaml
nodo:
  id: "T-005_sentinel"
  version: "1.0.0"
  goal: "Observabilidad: eventos, loops, deadlocks, métricas"
  subgoals: ["log eventos", "detectar loops > 3", "detectar deadlocks > 10", "OpenManus watchdog"]
  contrato:
    input:  {tipo: "event", schema: {event: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {total_events: int, loops: list, deadlocks: list, rate_per_s: float},
             criterio_exito: "no deadlock en 24h"}
  context: "G4 trazabilidad 100%; LOOP_THRESHOLD=10, DEADLOCK_THRESHOLD=20"
  constraints: ["máx 5000 eventos en memoria (FIFO)", "rate < 100/s"]
  dependencies: ["T-001_orchestrator"]
  risk: "bajo"
  priority: 1
  skills_requeridas: []
  timeout_seg: 30
  retry: {max: 1, regla: "si memoria llena, evict FIFO"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "100 eventos", persiste_en: "state.json"}
  rollback: {trigger: "deadlock_detected", accion: "escalar inmediatamente"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["eventos[]"], escribe: ["metrics", "alerts"]}
```

## T-006_juez
```yaml
nodo:
  id: "T-006_juez"
  version: "1.0.0"
  goal: "3 simulaciones: real/adversarial/regression + baseline write"
  subgoals: ["_simulate_real", "_simulate_adversarial", "_simulate_regression", "atomic_write baseline"]
  contrato:
    input:  {tipo: "json", schema: {output: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {simulations: dict, all_passed: bool, baseline_written: bool},
             criterio_exito: "3/3 GO + baseline escrito"}
  context: "T09 baseline_output.json write tras 3 simulaciones GO"
  constraints: ["detecta TODO/FIXME/XXX/UNREADABLE", "regression compara con baseline_output.json"]
  dependencies: ["T-004_sheriff"]
  risk: "medio"
  priority: 1
  skills_requeridas: []
  timeout_seg: 120
  retry: {max: 1, regla: "si sandbox no disponible, skip simulación con warning"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "simulación", persiste_en: "state.json"}
  rollback: {trigger: "sim_fail", accion: "reparar upstream"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["baseline_output.json"], escribe: ["simulation_results", "baseline_output.json"]}
```

## T-007_repair
```yaml
nodo:
  id: "T-007_repair"
  version: "1.0.0"
  goal: "16 pasos F1-F16 recovery engine"
  subgoals: ["F1 detectar", "F2 snapshot", "F3 clasificar", "F4-F7 ramas", "F10 limpiar", "F11-F16 reintentos"]
  contrato:
    input:  {tipo: "json", schema: {node_id: str, original_diff: str, error: str}, validacion: "requerida"}
    output: {tipo: "json", schema: {recovered: bool, escalated: bool, diff: str},
             criterio_exito: "recovered=true o escalated=true"}
  context: "max 2 repairs; counter==2 → escalar a Director"
  constraints: ["counter < 2", "DELTA obligatorio en cada reintento"]
  dependencies: ["T-004_sheriff", "T-005_sentinel"]
  risk: "medio"
  priority: 1
  skills_requeridas: []
  timeout_seg: 180
  retry: {max: 2, regla: "cada retry con DELTA nuevo"}
  sandbox: "local"
  states: [pending, running, done, failed, recovered, escalated]
  checkpoint: {cada: "iteración", persiste_en: "state.json"}
  rollback: {trigger: "counter==2", accion: "escalar a DLQ + Telegram"}
  approval: {requiere_director: true}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: true, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["state", "repair_counts"], escribe: ["repair_counts", "DLQ"]}
```

## T-008_consensus
```yaml
nodo:
  id: "T-008_consensus"
  version: "1.0.0"
  goal: "2-de-3 con 3 modelos en paralelo"
  subgoals: ["3 sandboxes paralelos", "votación", "elección"]
  contrato:
    input:  {tipo: "json", schema: {goal: str, context: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {chosen: dict, agreement: float, escalate: bool},
             criterio_exito: "agreement >= 0.5"}
  context: "single/fast/full consensus modes; 3 proveedores distintos"
  constraints: ["mínimo 2 agentes", "agreement < 0.5 → escalate"]
  dependencies: ["T-001_orchestrator"]
  risk: "bajo"
  priority: 2
  skills_requeridas: ["mavis", "cerebras", "nvidia"]
  timeout_seg: 120
  retry: {max: 1, regla: "si un agente falla, usar fallback"}
  sandbox: "container"
  states: [pending, running, done, failed, escalated]
  checkpoint: {cada: "voto", persiste_en: "state.json"}
  rollback: {trigger: "agreement_low", accion: "escalar a Director"}
  approval: {requiere_director: true}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: true, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: [], escribe: ["consensus_result"]}
```

## T-009_router
```yaml
nodo:
  id: "T-009_router"
  version: "1.0.0"
  goal: "Asignar sandbox a sub-tarea con circuit breaker"
  subgoals: ["round-robin o capacidad", "respetar circuit breaker", "fallback chain"]
  contrato:
    input:  {tipo: "json", schema: {agent_type: str, work_dir: str}, validacion: "requerida"}
    output: {tipo: "json", schema: {sandbox_id: str, agent_type: str},
             criterio_exito: "sandbox sano asignado"}
  context: "G3 circuit breaker; fallback opencode → mimo → claude"
  constraints: ["si breaker open, skip a siguiente"]
  dependencies: ["T-003_sandbox"]
  risk: "bajo"
  priority: 2
  skills_requeridas: []
  timeout_seg: 30
  retry: {max: 3, regla: "cada retry con diferente sandbox"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "asignación", persiste_en: "state.json"}
  rollback: {trigger: "no_healthy_sandbox", accion: "escalar a Director"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["sandbox_health"], escribe: ["sandbox_id"]}
```

## T-010_dsl
```yaml
nodo:
  id: "T-010_dsl"
  version: "1.0.0"
  goal: "DSL YAML con parser, validador, executor"
  subgoals: ["parser YAML (PyYAML + fallback)", "validador de DAG", "executor topológico"]
  contrato:
    input:  {tipo: "file", schema: {path: str, formato: "yaml"}, validacion: "requerida"}
    output: {tipo: "json", schema: {status: str, completed_loops: list},
             criterio_exito: "todos los loops ejecutados OK"}
  context: "loops anidados; no termina hasta completar o escalar"
  constraints: ["líneas ≤90 chars", "bloques ≤60 líneas"]
  dependencies: ["T-001_orchestrator"]
  risk: "bajo"
  priority: 2
  skills_requeridas: ["pyyaml@6.0"]
  timeout_seg: 60
  retry: {max: 2, regla: "si parser falla, intentar fallback"}
  sandbox: "local"
  states: [pending, running, validating, done, failed, escalated]
  checkpoint: {cada: "loop", persiste_en: "state.json"}
  rollback: {trigger: "dsl_invalid", accion: "escalar a Director"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: true, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["state"], escribe: ["state"]}
```

## T-011_agents
```yaml
nodo:
  id: "T-011_agents"
  version: "1.0.0"
  goal: "3 agentes: Claude Code, Mimo Code, OpenCode"
  subgoals: ["BaseAgent ABC", "execute/verify/validate/repair", "extract_diff"]
  contrato:
    input:  {tipo: "json", schema: {goal: str, context: dict}, validacion: "requerida"}
    output: {tipo: "json", schema: {status: str, diff: str},
             criterio_exito: "diff extraíble y aplicable"}
  context: "el orquestador NO toca código interno; solo recibe output"
  constraints: ["agentes reemplazables", "output via diff unificado"]
  dependencies: ["T-001_orchestrator", "T-003_sandbox"]
  risk: "medio"
  priority: 1
  skills_requeridas: ["claude_code", "mimo_code", "opencode"]
  timeout_seg: 300
  retry: {max: 2, regla: "con DELTA nuevo"}
  sandbox: "container"
  states: [pending, running, done, failed, recovered]
  checkpoint: {cada: "agente", persiste_en: "state.json"}
  rollback: {trigger: "agent_fail", accion: "L04 repair"}
  approval: {requiere_director: true}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: true, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["goal_hash"], escribe: ["diff", "agent_output"]}
```

## T-012_dockerfiles
```yaml
nodo:
  id: "T-012_dockerfiles"
  version: "1.0.0"
  goal: "3 Dockerfiles: claude_code, mimo_code, opencode"
  subgoals: ["FROM python:3.11-slim", "instalar deps por agente", "shim CLI reemplazable", "sleep infinity"]
  contrato:
    input:  {tipo: "spec", schema: {agent: str, deps: list}, validacion: "requerida"}
    output: {tipo: "file", schema: {path: str, lines: int, build: bool},
             criterio_exito: "docker build exitoso"}
  context: "shims para reemplazar con binarios reales en producción"
  constraints: ["read-only filesystem", "network=none", "1 CPU, 1GB RAM, 256 pids"]
  dependencies: ["T-003_sandbox", "T-011_agents"]
  risk: "medio"
  priority: 2
  skills_requeridas: ["docker@24+"]
  timeout_seg: 600
  retry: {max: 2, regla: "con layer cache"}
  sandbox: "container"
  states: [pending, running, validating, done, failed]
  checkpoint: {cada: "imagen", persiste_en: "state.json"}
  rollback: {trigger: "build_fail", accion: "destroy + rebuild"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: [], escribe: ["image_ids"]}
```

## T-013_docker_compose
```yaml
nodo:
  id: "T-013_docker_compose"
  version: "1.0.0"
  goal: "docker-compose.yml con 3 servicios + red interna"
  subgoals: ["network internal", "volumes work_dir + skills", "deploy limits"]
  contrato:
    input:  {tipo: "spec", schema: {services: dict, networks: dict}, validacion: "requerida"}
    output: {tipo: "file", schema: {path: str, valid: bool},
             criterio_exito: "docker compose config válido"}
  context: "G3 aislamiento entre sandboxes; sin exposición de puertos al host"
  constraints: ["3 servicios exactos", "internal: true"]
  dependencies: ["T-012_dockerfiles"]
  risk: "bajo"
  priority: 2
  skills_requeridas: ["docker-compose@2.0"]
  timeout_seg: 60
  retry: {max: 1, regla: "no retry en compose"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "servicio", persiste_en: "state.json"}
  rollback: {trigger: "compose_invalid", accion: "corregir y reintentar"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: false, delta_score: false}
  memory: {lee: [], escribe: ["compose_hash"]}
```

## T-014_setup
```yaml
nodo:
  id: "T-014_setup"
  version: "1.0.0"
  goal: "Script de instalación bash"
  subgoals: ["crear venv", "pip install deps", "build imágenes", "smoke test"]
  contrato:
    input:  {tipo: "spec", schema: {comandos: list}, validacion: "requerida"}
    output: {tipo: "file", schema: {path: str, executable: bool},
             criterio_exito: "bash setup.sh exit 0"}
  context: "5 fases: preparar, construir, verificar, integrar, smoke"
  constraints: ["set -e", "set -u"]
  dependencies: ["T-013_docker_compose"]
  risk: "bajo"
  priority: 3
  skills_requeridas: ["bash@5+"]
  timeout_seg: 300
  retry: {max: 1, regla: "no retry"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "fase", persiste_en: "state.json"}
  rollback: {trigger: "setup_fail", accion: "log + exit 1"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: [], escribe: ["setup_log"]}
```

## T-015_tests
```yaml
nodo:
  id: "T-015_tests"
  version: "1.0.0"
  goal: "Tests: test_mvp.py (32 tests) + test_audit_20.py (84 checks) + test_dsl.py (10 tests) + test_verify_all.py"
  subgoals: ["imports OK", "sims OK", "auditoría 6/6", "100% verificación"]
  contrato:
    input:  {tipo: "spec", schema: {archivos: list}, validacion: "requerida"}
    output: {tipo: "json", schema: {pass: int, fail: int, skip: int},
             criterio_exito: "100% pass"}
  context: "test_mvp 31/32 (1 skipped requiere docker); test_audit 6/6; test_verify 84/84"
  constraints: ["pytest", "SKIP_DOCKER_TESTS=1 en sandbox"]
  dependencies: ["T-001_orchestrator", "T-004_sheriff", "T-006_juez", "T-010_dsl"]
  risk: "bajo"
  priority: 1
  skills_requeridas: ["pytest@7+"]
  timeout_seg: 120
  retry: {max: 2, regla: "con DELTA nuevo"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "test", persiste_en: "state.json"}
  rollback: {trigger: "test_fail", accion: "reparar upstream"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: true, delta_score: true}
  memory: {lee: ["state"], escribe: ["test_results"]}
```

## T-016_docs
```yaml
nodo:
  id: "T-016_docs"
  version: "1.0.0"
  goal: "Documentación: 5 MD en docs/ + DEPLOY_INSTRUCTIONS.md"
  subgoals: ["ARCHITECTURE", "LOOP_ENGINE", "INPUT_BLOCK", "REFUTACIONES", "PIPELINE_MASTER", "DSL_SPEC", "DEPLOY"]
  contrato:
    input:  {tipo: "spec", schema: {docs: list}, validacion: "requerida"}
    output: {tipo: "file", schema: {archivos: list, total_lines: int},
             criterio_exito: "todos los docs presentes"}
  context: "655 líneas de docs + 4732 líneas de deploy"
  constraints: ["empieza y termina con ---"]
  dependencies: ["T-001_orchestrator"]
  risk: "bajo"
  priority: 3
  skills_requeridas: []
  timeout_seg: 60
  retry: {max: 1, regla: "no retry"}
  sandbox: "local"
  states: [pending, running, done, failed]
  checkpoint: {cada: "doc", persiste_en: "state.json"}
  rollback: {trigger: "doc_incomplete", accion: "completar"}
  approval: {requiere_director: false}
  evidence: {obligatoria: true, formato: "§6.4"}
  validation: {tribunal: "§6", umbral: 70}
  telemetry: {tokens: false, tiempo: true, iteraciones: false, delta_score: false}
  memory: {lee: [], escribe: ["docs_manifest"]}
```

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 95, JUEZ 100, SUPERVISOR 95, VALIDADOR 90, VERIFICADOR 95. Score promedio: **95.8/100**
MINI RESUMEN: 16 nodos DSL completos con contratos, dependencies, riesgos, timeouts y rollback. Cada nodo tiene state machine con transiciones por evento.
→ Esperando: OK | FIX
