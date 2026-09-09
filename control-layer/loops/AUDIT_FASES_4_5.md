# Auditoría Loop System — post Fase 4 + 5

## Entregado ahora

### Fase 4
| Módulo | Path |
|--------|------|
| Registry | registry.py |
| Lease | lease.py |
| Heartbeat | heartbeat.py |
| DLQ | dlq.py |
| Supervisor | supervisor.py |

### Fase 5
| Módulo | Path |
|--------|------|
| InMemoryPlugin | plugins/memory_inproc.py |
| InMemoryGraphPlugin | plugins/graph_inproc.py |
| StrategyMemory | strategy_memory.py |
| ResultCache | result_cache.py |

## Mapa completo actual

```
LoopSupervisor
  ├── Registry / Lease / Heartbeat / DLQ
  └── LoopEngine
        ├── StateMachine + invariants
        ├── PhaseRunner + Sheriff (9)
        ├── PolicyEngine (YAML DSL)
        ├── RecoveryEngine (11 actions)
        ├── ProgressEvaluator + Adaptive
        ├── BudgetGovernor
        ├── RiskEngine + HumanGate
        └── Events → Memory/Graph plugins
              ├── StrategyMemory
              └── ResultCache
```

## Qué funciona bien
1. Contratos formales + SM determinista
2. Detect ≠ decide (policy separada)
3. Engine reutilizable multi project/agent
4. Plugins desacoplados por eventos
5. Supervisor in-process con max_concurrent + orphan recovery
6. Strategy memory + cache listos para wire fino

## Gaps / mejoras prioritarias

### P0 — cableado fino (aún no automático)
- [ ] LoopEngine no llama ProgressEvaluator/BudgetGovernor/Risk en run_iteration por defecto (hay que inyectar en handlers o ampliar engine)
- [ ] Supervisor no persiste contextos a disco (solo RAM)
- [ ] StrategyMemory.suggest_strategy no se aplica solo al crear run
- [ ] ResultCache no se consulta en start de fase

### P1 — robustez
- [ ] Idempotency_key enforcement en run_iteration (dedup)
- [ ] Event hash chain verify al leer memoria
- [ ] Detectors reales (stall/oscillation) wired a progress delta — hoy policy recibe detectors externos
- [ ] Lease multi-worker real (Redis) — hoy in-process
- [ ] Heartbeat emit LoopEvent HEARTBEAT

### P2 — distribución / prod
- [ ] Persistence: registry/dlq/state → JSONL o DB
- [ ] Deterministic replay desde event log
- [ ] Simulator + chaos tests
- [ ] Observability metrics export (OTel)
- [ ] CapabilityRequest → Router real del control-layer

### P3 — avanzado (docs originales)
- [ ] MHYTOS parallel strategy executor
- [ ] 1080 catalog generator
- [ ] Refutation 50Q (solo schema slot)
- [ ] Experience graph semantic similarity (vector)
- [ ] Budget reallocation multi-task automática

## Lo que NO falta en arquitectura
- Separación WORKFLOW/TASK/LOOP/ITERATION
- Interfaces Memory/Graph
- Human gate / risk
- DLQ + requeue
- Policy DSL editable sin tocar Python

## Recomendación siguiente
1. Wire P0: engine.run_iteration integra budget.charge + progress + risk gate
2. Persistencia mínima registry+events JSONL
3. Tests integración Supervisor end-to-end

Score arquitectura: **8.5/10** (era 7/10 pre-contratos; sube con F4/F5)
Score implementación producción: **6/10** (in-memory, falta persist + wire automático)
