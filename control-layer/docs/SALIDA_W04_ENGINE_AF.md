# SALIDA W04 — Engine A–F

**Estado: CERRADA 100%**

## Core
| Módulo | Path |
|--------|------|
| LoopEngine | `loops/engine.py` |
| Phase handlers + ejecutar→Adapter | `loops/phase_handlers.py` |
| NodesLoader auto-register | `loops/nodes_loader.py` |
| AgentAdapter + CallableAgent | `loops/agent_adapter.py` |
| CapabilityRouter | `loops/capability_router.py` |
| MHYTOS strategies | `loops/mhytos.py` |
| Progress + from phases | `progress.py` · `progress_from_phases.py` |
| Bootstrap hydrate/resume | `loops/bootstrap.py` |
| runtime_factory | `loops/runtime_factory.py` |

## A–F (wiring)
| Letter | Qué |
|--------|-----|
| A | `ejecutar` dispatch capability → Adapter |
| B | `nodes/*.yaml` → register agents |
| C | Supervisor persist_dir + metrics |
| D | MHYTOS parallel/adversarial/consensus |
| E | Progress desde outputs reales de fases |
| F | Bootstrap hydrate + resume runs |

## Flujo mínimo
```
nodes_loader → adapter → make_default_handlers → LoopEngine.run_once
```

## Siguiente
**W05** — Supervisor persist+metrics
