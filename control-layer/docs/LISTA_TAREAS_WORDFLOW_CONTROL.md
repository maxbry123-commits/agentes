# Lista SOLO capa de control universal Wordflow
# Excluye: HF · binario temporal · memoria avanzada · P1-CONVERTIDOR · fases pipeline proyecto vivo

| # | Tarea | Salida | Estado |
|---|--------|--------|--------|
| W01 | Contratos loop + schemas D1–D10 | `loops/contracts/*` · `schemas/*` | ✅ |
| W02 | State machine + 9 phases + Sheriff | `loops/state_machine.py` · `phases.py` | ✅ |
| W03 | Policy DSL + Recovery 11 | `loops/policy/*` · `recovery.py` | ✅ |
| W04 | Engine A–F (adapter, progress, MHYTOS, bootstrap) | `loops/engine.py` · `phase_handlers.py` · `bootstrap.py` | ✅ |
| W05 | Supervisor persist+metrics | `loops/supervisor.py` | ✅ |
| W06 | Registry/Lease/HB/DLQ/Replay | `loops/registry.py` … | ✅ |
| W07 | AgentAdapter + CapabilityRouter + NodesLoader | `agent_adapter.py` · `nodes_loader.py` | ✅ |
| W08 | runtime_factory (generic path, sin exigir bin) | `runtime_factory.py` | ✅ |
| W09 | Plantillas UOOS B1–B10 + pipeline guía | `templates/uoos/*` · `templates/pipeline/*` | ✅ |
| W10 | Despliegue determinista 5 pasos (scripts) | `despliegue/*` | ✅ |
| W11 | Schema validators deterministas | `skills/validate_schemas.py` | ✅ esta salida |
| W12 | Bootstrap proyecto → engine/supervisor | `bootstrap_project.py` | ✅ esta salida |
| W13 | Índice 100% + README | `WORDFLOW_100.md` · `README.md` | ✅ esta salida |

## Pendiente FUERA de esta lista (acordado)
HF · binario · memoria Wordflow · PIPELINE 00–20 poblado · OUSS/Drive · P1-CONVERTIDOR
