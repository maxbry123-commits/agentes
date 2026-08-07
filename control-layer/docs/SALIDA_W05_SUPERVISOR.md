# SALIDA W05 — Supervisor persist + metrics

**Estado: CERRADA 100%**

## Entregable
`loops/supervisor.py` — `LoopSupervisor` + `SupervisorConfig`

## API
| Método | Rol |
|--------|-----|
| `create(ctx)` | registra run |
| `run_once(run_id, …)` | una iteración engine |
| `command(run_id, cmd)` | START/PAUSE/RESUME/CANCEL/… |
| `recover_orphans()` | lease expirado → recover |
| persist_dir | serializa contexto/eventos |
| metrics | contadores por run |

## Defaults
- `persist_dir` activo por config
- metrics on create/run_once
- phase_context → capability/strategy a handlers

## Siguiente
**W06** — Registry / Lease / HB / DLQ / Replay
