# SALIDA W06 — Registry · Lease · Heartbeat · DLQ · Replay

**Estado: CERRADA 100%**

| Módulo | Path | Rol |
|--------|------|-----|
| Registry | `loops/registry.py` | runs activos / lookup |
| Lease | `lease.py` · `lease_backend.py` | ownership TTL |
| Heartbeat | `heartbeat.py` | liveness |
| DLQ | `dlq.py` | fallos irrecuperables |
| Replay | `replay.py` | re-ejecución determinista desde eventos |
| Persist store | `persistence_store.py` · `persist.py` | snapshots |
| Simulator | `simulator.py` | chaos/dry paths |
| Metrics | `metrics.py` | contadores |
| Event chain | `event_chain.py` | hash verify |

## Invariantes
- Lease expirado → orphan → recover/DLQ
- Replay no muta historial; solo re-aplica
- DLQ no borra evidence

## Siguiente
**W07** — AgentAdapter + CapabilityRouter + NodesLoader
