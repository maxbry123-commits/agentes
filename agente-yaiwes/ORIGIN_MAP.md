# ORIGIN_MAP — seed (S1/S3)

Mapa completo origen → destino se completa en **S3** con todas las filas del Paso 3.

## Hallazgos ancla
| Origen | Destino |
|--------|--------|
| wordflow_kernel/gateway/intelligence.py + router_http.py | execution-engine-pool/adapter-layer |
| engines/openclaw_stub.py, hermes_stub.py | execution-engine-pool/auxiliary-role-agents |
| code_path_runner.py / programming-modular-v1 | code-programming-engine/code-path-execution |
| goal_lock.py | execution-orchestration/goal-lock (única vez) |
| cognitive_loop.py | execution-orchestration/mission-planning (única vez) |
| evidence_packet.py | observability/evidence-packet (única vez) |

Ver PLAN: `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md` S4–S9.
