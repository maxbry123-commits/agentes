> **SUPERSEDED (2026-09-20)** - Este slot se reasigno. `codex` en `agent_sources/` es codigo real pero requiere compilar el monorepo `codex-rs` con toolchain Rust/cargo - no es un install simple para correr este handoff hoy. N-1.1 paso a `aider` -> ver `Claude notas/handoffs/HANDOFF-aider.md` y `Claude notas/NOTA-2026-09-20-swap-agentes-fase0.md`. No se borra este archivo por R03 (nunca borrar); queda solo como registro historico.

---

# Handoff — agente `codex` (agent_sources/codex, confirmado con contenido real)

Fuente de verdad: `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` + `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml`. Rol de Codex en el DAG (N-2.12): AUDITOR — independiente, no escribe código de producción, verifica. Este nodo respeta ese rol: es infraestructura/CI, no edición del kernel.

Nodo asignado (fase_0_desbloqueo, sin dependencias — ejecutable ya, y bloquea N-1.2 y N-3.1, es decir es el nodo con mas impacto de desbloqueo de los 5 de fase 0):

## N-1.1 - Materializar submodules en CI
- fuente_director: L475
- accion: cablear `git submodule update --init` con sparse-checkout en un workflow de GitHub Actions
- motivo: el gitlink NO trae codigo; sin esto ningun nodo puede extraer logica real de los submodules montados
- acceptance:
  - un run de CI lista archivos reales de al menos 1 submodule
  - el run no supera 5 minutos
- evidence: run_id, log_con_listado, sha_workflow
- regla dura del contrato (R05): sparse-checkout obligatorio - el repo pesa 16.4GB, un checkout completo muere o tarda ~13min (evidencia ya registrada: runs 35467245568 y 35468506302 murieron asi)

## Contrato de salida esperado
```json
{
  "mission_id": "N-1.1-codex-2026-09-20",
  "status": "WAITING_SIGNAL",
  "summary": "",
  "goal_restated": "Cablear git submodule update --init con sparse-checkout en un workflow de Actions que liste archivos reales de al menos 1 submodule en menos de 5min",
  "steps_done": [],
  "steps_pending": ["N-1.1"],
  "artifacts": [],
  "contracts_active": ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"],
  "sheriff_state": "YELLOW",
  "risk_score": 3,
  "evidence_hash": null,
  "errors": [],
  "warnings": ["checkout completo del repo esta PROHIBIDO por tamano (R05)"],
  "next_action": "Escribir/editar workflow en .github/workflows con sparse-checkout, correrlo, capturar run_id",
  "signals_pending": 0,
  "mode": "wordflow",
  "chef_pass": "collect",
  "raw_refs": ["Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.1"]
}
```

Reglas heredadas del contrato: R01 no codigo desde cero, R02 max 500 LOC, R04 no PASS sin evidencia, R05 sparse-checkout obligatorio (critico para este nodo especificamente), R06 anotar antes de avanzar, R08 nunca escalar - gap_ladder 1..20, agotado -> FLAG + siguiente nodo.
