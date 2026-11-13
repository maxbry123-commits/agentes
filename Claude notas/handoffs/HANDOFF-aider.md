# Handoff - agente `aider` (agent_sources/aider, verificado pip-installable)

Reemplaza a `codex` en este slot. Motivo del cambio: ver `Claude notas/NOTA-2026-09-20-swap-agentes-fase0.md`.

Verificado hoy: `pyproject.toml` con `[project.scripts] aider = "aider.main:main"`, build-backend setuptools estandar, dependencias declaradas en requirements.txt. Instalable con pip sin toolchain adicional (a diferencia de codex, que requiere cargo/Rust para compilar codex-rs).

Fuente de verdad: `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` + `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml`.

## N-1.1 - Materializar submodules en CI
- fuente_director: L475
- accion: cablear git submodule update --init con sparse-checkout en un workflow de GitHub Actions
- acceptance: un run de CI lista archivos reales de al menos 1 submodule, en menos de 5 minutos
- evidence: run_id, log_con_listado, sha_workflow
- regla dura (R05): sparse-checkout obligatorio, checkout completo del repo de 16.4GB muere o tarda ~13min
- bloquea: N-1.2, N-3.1 (el nodo de fase_0 con mas impacto de desbloqueo)

## N-2.8 - Leer los 7 archivos de gobernanza (posibles stubs)
- archivos: sheriff, sentinel, judge, guardian, supervisor, validator, verifier (en control-layer/)
- accion: leer contenido real; si son stubs, cablearlos con la cadena de gobernanza del contrato
- acceptance: veredicto por archivo (REAL o STUB); los stubs quedan cableados
- bloquea: N-2.9, N-2.12

## Contrato de salida esperado
```json
{
  "mission_id": "N-1.1+N-2.8-aider-2026-09-20",
  "status": "WAITING_SIGNAL",
  "summary": "",
  "goal_restated": "Cablear submodules en CI con sparse-checkout + verificar y cablear los 7 archivos de gobernanza",
  "steps_done": [],
  "steps_pending": ["N-1.1", "N-2.8"],
  "artifacts": [],
  "contracts_active": ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"],
  "sheriff_state": "YELLOW",
  "risk_score": 3,
  "evidence_hash": null,
  "errors": [],
  "warnings": [],
  "next_action": "N-1.1 primero (desbloquea mas nodos), luego N-2.8",
  "signals_pending": 0,
  "mode": "wordflow",
  "chef_pass": "collect",
  "raw_refs": ["Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.1", "Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-2.8"]
}
```

Reglas heredadas del contrato: R01 no codigo desde cero, R02 max 500 LOC, R04 no PASS sin evidencia, R05 sparse-checkout obligatorio, R06 anotar antes de avanzar, R08 nunca escalar - gap_ladder 1..20.
