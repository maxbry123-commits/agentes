# EVIDENCE — PLAN30 T10–T15

Contrato: `tel.workflow/v3` · estado de esta evidencia: `VERIFIED_CLOSED` para T10–T15.

## Provenance y destinos
- C01 origen `Loop Engineer/Loop-Engineer/loop/runner.py` blob `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` → destino `Agente Yaiwes principal/execution-orchestration/deterministic-execution/serial_dispatch.py` blob `77017b70239cedcce26f1df4a076272572f0927b`.
- C02 origen `Loop Engineer/Loop-Engineer/loop/runcontrol.py` blob `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` → destino `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/run_control_adapter.py` blob `aa4f62571044d873e3969bc7f747bfc83e3047a6`.
- C03/C04 patrones Elspeth blobs `98b791e350e3a2829fb2c2977cc0fbc25beb4321` + `c89a5d9d2354ae549845aeab9a90cc3ab14f853e`, commit `720d441336434d227c2a00caaac100db48a07d5c` → destino `resume_identity.py` blob `dc440bd180194d6cef2bf1b38b1ef1b85138ef0b`.
- C05 patrón StrategyDelta `rules.py` blob `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b`, commit `efcfcb20f09117504b00f682ada1bfff2b04b649` → destino `control-governance/strategy_delta_guard.py` blob `46efd22bd7b5ac3c22cc5ca084788d46b4b5b16b`.
- Test repo `Agente Yaiwes principal/tests/test_plan30_loop_runtime.py` content blob tras fix loader: `e1b1e3a4e4ca79e5dee00d5676a6038c6426bc31`, commit `3b7f0cec153ef03656f76dcd693c17fe061f7a78`.

## Test real
Ejecución local aislada de los mismos contenidos del repo, sin acceso de red y sin dependencias externas de los proyectos fuente:

```text
.....                                                                    [100%]
5 passed in 0.06s
```

Casos comprobados:
1. `dispatch_once` selecciona el primer pending cuyas dependencias están hechas y llama al dispatcher exactamente una vez.
2. Una dependencia ausente deja la selección bloqueada.
3. `ResumeIdentity` conserva `input_hash` y aumenta `attempt` solo con `node_id + INPUT_BLOCK + checkpoint_id` idénticos; cambios son rechazados.
4. `StrategyDeltaGuard` rechaza estrategia repetida y delta-hash ya fallido; acepta un delta materialmente nuevo.
5. Pause/resume exige el checkpoint exacto y conserva `iteration_id`.

## Resultado
- T10 `VERIFIED_CLOSED`
- T11 `VERIFIED_CLOSED`
- T12 `VERIFIED_CLOSED`
- T13 `VERIFIED_CLOSED`
- T14 `VERIFIED_CLOSED`
- T15 `VERIFIED_CLOSED`

Siguiente nodo: T16 — Ficha/contratos de los módulos integrados.