# Handoff — agente `opencode` (agent_sources/opencode, confirmado con contenido real)

Fuente de verdad: `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` + `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml`. Rol de OpenCode en el DAG (N-2.12): ESCRITOR. Los dos nodos de abajo son trabajo de escritura/cableado, no de auditoría.

Nodos asignados (fase_0_desbloqueo, sin dependencias — ejecutables ya):

## N-2.8 — Leer los 7 archivos de gobernanza (posibles stubs)
- archivos: sheriff, sentinel, judge, guardian, supervisor, validator, verifier (en `control-layer/`)
- tamano_actual: 389-804 bytes cada uno (según el plan — sin verificar hoy, pendiente para este nodo)
- accion: leer contenido real; si son stubs, cablearlos con la cadena de gobernanza descrita en el contrato (SHERIFF → EJECUTOR → VALIDADOR → VERIFICADOR → SENTINELA → SUPERVISOR → JUEZ → GUARDIAN)
- acceptance: veredicto por archivo (REAL o STUB); los stubs quedan cableados
- crítico: sin esto la cadena de gobernanza del DSL no tiene implementación real — **bloquea N-2.9 y N-2.12** (equipo frontend)

## N-2.11 — Construir la biblioteca RAG (13 subcarpetas vacías)
- carpetas: templates / skills / plugins / prompts
- regla asociada: R11 (antes de escribir cualquier schema, consultar biblioteca/GitHub — prohibido escribir de memoria del LLM)
- acceptance: biblioteca consultable antes de generar cualquier schema
- **bloquea N-1.5** (conversión de los 24 skills a schema DSL DAG)

## Contrato de salida esperado
```json
{
  "mission_id": "N-2.8+N-2.11-opencode-2026-09-20",
  "status": "WAITING_SIGNAL",
  "summary": "",
  "goal_restated": "Verificar si los 7 archivos de gobernanza son stubs y cablearlos si lo son; construir biblioteca RAG consultable en 4 carpetas hoy vacias",
  "steps_done": [],
  "steps_pending": ["N-2.8", "N-2.11"],
  "artifacts": [],
  "contracts_active": ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"],
  "sheriff_state": "YELLOW",
  "risk_score": 3,
  "evidence_hash": null,
  "errors": [],
  "warnings": ["N-2.8 bloquea N-2.9 y N-2.12; N-2.11 bloquea N-1.5 -- priorizar sobre nodos no asignados"],
  "next_action": "Leer los 7 archivos de control-layer primero (mas rapido y desbloquea mas), luego construir la biblioteca RAG",
  "signals_pending": 0,
  "mode": "wordflow",
  "chef_pass": "collect",
  "raw_refs": ["Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-2.8", "Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-2.11"]
}
```

Reglas heredadas del contrato: R01 no código desde cero, R02 máx 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia, R06 anotar antes de avanzar, R08 nunca escalar — `gap_ladder` 1..20, agotado → FLAG + siguiente nodo.
