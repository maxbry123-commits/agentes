---
# ARCHITECTURE — Orquestador Universal v1.0

## Visión

Orquestador universal que conecta el chat a **cualquier agente** mediante **sandboxes aislados**.
El orquestador NO toca código interno de los agentes: solo define goal, asigna sandbox, recibe output.

## Capas

```
CHAT ──► ORQUESTADOR ──► SUPERVISOR ──► ROUTER ──► [SANDBOX A | B | C | N]
                  ▲                                              │
                  └──────── Juez/Sentinel ◄──────────────────────┘
```

### 1. CHAT (interfaz)
- Único punto de entrada/salida con el usuario
- Acepta plantilla: objetivo, planificar, organizar, tareas, metas, propósito, refutaciones

### 2. ORQUESTADOR (cerebro)
- **Goal Lock**: congela objetivo + hash, valida en cada nodo
- **Scope Lock**: define sandbox_id, recursos, timebox
- **Loop Engine**: ejecuta los 10 loops en orden
- **State Machine**: persiste workflow_state.json atómicamente
- **DSL Engine**: parsea `@node(id, depends_on, gate, sandbox, repair_max)`
- **DAG Engine**: networkx DiGraph, topological_sort, cycle detection

### 3. SUPERVISOR (árbitro)
- **Sheriff**: 6 gates (completitud, coherencia, formato, sandbox_isolation, repairs_ok, approval)
- **Validador**: contrato de output (JSON schema, required_fields)
- **Verificador**: ejecuta tests/lint/diff dentro del sandbox
- **Sentinel**: eventos, loops, deadlocks, métricas por sandbox
- **Juez**: 3 simulaciones (real, adversarial, regression vs baseline)
- **Consenso**: 3 modelos proponen, 2-de-3 elige

### 4. ROUTER (despachador)
- Decide: qué agente, qué sandbox, qué modelo
- Round-robin o por capacidad (CPU/RAM disponibles)
- Mantiene circuit breaker por sandbox (5 fallos → open 60s)

### 5. SANDBOXES (ejecutores)
- Uno por agente: `claude_code`, `mimo_code`, `opencode`, `hf_space`, etc.
- Docker: `--network=none`, `--read-only` salvo `/work`, `--cpus=1`, `--memory=1g`, `--pids-limit=256`
- Lifecycle: start → exec → kill → restart → destroy
- Cambio de backend = cambiar entrypoint, el resto no se entera

## 10 GOALS

| # | Goal | Enforcement |
|---|------|-------------|
| G1 | Goal Lock: objetivo inmutable durante ejecución | hash(goal) en workflow_state, validado en cada nodo |
| G2 | Scope Lock: agente solo opera en su sandbox | path whitelist en SANDBOX_ROOT |
| G3 | Aislamiento total entre sandboxes | docker network none + read-only mounts |
| G4 | Trazabilidad 100% | Sentinel.events[] con timestamp + sandbox_id |
| G5 | Recuperación ante fallo | REPAIR loop max=2 → escalate (Telegram+DLQ) |
| G6 | Validación antes de avanzar | Sheriff.validate() en cada nodo |
| G7 | Determinismo verificable | replay desde workflow_state.json |
| G8 | Recursos limitados | docker --cpus --memory --pids-limit |
| G9 | No escape de secrets | env pass-through, scrub en logs |
| G10 | STOP limpio | N13 destroy + sandbox rm |

## 10 LOOPS (multi-agente)

```
L1  Goal Lock + Plan (parse plantilla, descomponer objetivo)
L2  Consensus plan: Claude+Mimo+OpenCode proponen, Juez elige
L3  Asignar sandbox por sub-tarea (1 por agente, paralelo)
L4  Claude Code EJECUTA (escribe código)
L5  Mimo Code VERIFICA (pytest + diff review)
L6  Mimo Code REPARA si L5 falla (patch mínimo)
L7  Mimo Code VALIDA (ruff/black/mypy)
L8  Loop repair: L6→L7 hasta 2 ciclos
L9  Sentinel: métricas + OpenManus watchdog
L10 Juez: 3 simulaciones (real / adversarial / regression)
```

## Multi-agente en paralelo

- L2 consensus: 3 sandboxes en paralelo (mismo prompt, distintos modelos)
- L3 asignación: round-robin o por capacidad
- L4/L5 secuencial (verify espera output de execute)
- L9/L10 paralelos entre sí
- L6-L8: Mimo solo (repair no necesita Claude)

## Mapa de datos

```
goal_hash ──► G1 en cada nodo
   │
   ▼
DSL ──► DAG ──► topologic_order ──► sandbox[i] ──► output
   │                                              │
   ▼                                              ▼
workflow_state.json ◄── persist ◄── Sheriff.validate ◄── Verifier.run
   │
   ▼
Sentinel.metrics ──► Juez.simulate ──► baseline_output.json
   │
   ▼
repair_count[node] < 2 ? REPAIR : ESCALATE
```

## Archivos

```
orchestrator-universal/
├── docs/
│   ├── ARCHITECTURE.md       (este archivo)
│   ├── LOOP_ENGINE.md         (10 loops + 16 R + 16 F)
│   ├── INPUT_BLOCK.md         (plantilla + bloques 9-11)
│   ├── REFUTACIONES.md        (3 roles atacando)
│   └── PIPELINE_MASTER.md     (componentes)
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py        (loop engine + goal/scope lock)
│   ├── router.py              (asignación de sandboxes)
│   ├── sandbox.py             (docker wrapper)
│   ├── sheriff.py             (6 gates)
│   ├── sentinel.py            (eventos, métricas)
│   ├── juez.py                (3 simulaciones)
│   ├── consensus.py           (2-de-3)
│   ├── repair.py              (F1-F16)
│   ├── state.py               (workflow_state atómico)
│   └── agents/
│       ├── __init__.py
│       ├── base.py            (Agent ABC)
│       ├── claude_code.py     (claude)
│       ├── mimo_code.py       (mimo)
│       └── opencode.py        (opencode)
├── tests/
│   └── test_mvp.py
├── main.py
├── requirements.txt
└── README.md
```
