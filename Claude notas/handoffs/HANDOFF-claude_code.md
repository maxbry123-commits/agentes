> **SUPERSEDED (2026-09-20)** - Este slot se reasigno. `claude_code` en `agent_sources/` es repo de documentacion/changelog, no codigo fuente instalable del CLI (sin package.json en la raiz) - no sirve para ejecutar este handoff. N-1.3 y N-1.4 pasaron a `smolagents` -> ver `Claude notas/handoffs/HANDOFF-smolagents.md` y `Claude notas/NOTA-2026-09-20-swap-agentes-fase0.md`. No se borra este archivo por R03 (nunca borrar); queda solo como registro historico.

---

# Handoff - agente `claude_code` (agent_sources/claude_code, confirmado con contenido real)

Fuente de verdad: `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` (reglas R01-R12, gap_ladder, gobernanza) + `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml` (nodos). No se inventa formato nuevo: este handoff reutiliza `output_contract.yaml` (Core kernel Yaiwes/control-layer/schemas/) para el reporte y el `id` propio del DAG para la traza.

Nodos asignados (fase_0_desbloqueo, sin dependencias pendientes - ejecutables ya):

## N-1.3 - Montar mcode (unico gap de descarga)
- fuente_director: L1458_L1464
- accion: Git Data API - POST /git/trees (mode=160000, type=commit, sha pineado) -> POST /git/commits -> PATCH /git/refs/heads/main
- metodo_probado_en: commit f13f8f9
- acceptance: GET agent_sources/mcode devuelve html_url a repo externo
- evidence: commit_sha, respuesta_api
- Verificado hoy 2026-09-20: mcode NO existe en agent_sources/ (confirmado por listado directo del arbol, no por busqueda) - el gap sigue abierto.

## N-1.4 - Subir 5 keys NVIDIA como secrets + test real
- fuente_director: L1531_L1580
- accion: sellado libsodium via ctypes sobre libsodium.so.23
- metodo_probado_en: memoria.md seccion 11 (mismo metodo ya usado con las 7 GROQ)
- secrets: NVIDIA_API_KEY_1..5
- base_url: https://integrate.api.nvidia.com/v1 - modelo: minimaxai/minimax-m2.7
- acceptance: GET /actions/secrets lista los 5 + test desde Actions HTTP 200 no vacio
- nota_critica: el sandbox de Claude tiene la red bloqueada a NVIDIA (CONNECT 403) - el test real solo puede correr desde GitHub Actions, no desde aqui.
- [FLAG-1 del contrato sigue abierto]: esas 5 keys ya estan en texto plano en el historial de un repo publico - subirlas como secret no revoca la exposicion previa; regenerarlas en NVIDIA es responsabilidad del Director, no bloquea este nodo.

## Contrato de salida esperado (output_contract.yaml, campos obligatorios)
```json
{
  "mission_id": "N-1.3+N-1.4-claude_code-2026-09-20",
  "status": "WAITING_SIGNAL",
  "summary": "",
  "goal_restated": "Montar mcode como gitlink real + subir 5 NVIDIA keys como secrets sellados, con test real desde Actions",
  "steps_done": [],
  "steps_pending": ["N-1.3", "N-1.4"],
  "artifacts": [],
  "contracts_active": ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"],
  "sheriff_state": "YELLOW",
  "risk_score": 4,
  "evidence_hash": null,
  "errors": [],
  "warnings": ["FLAG-1 abierto: keys NVIDIA expuestas antes de este nodo"],
  "next_action": "Ejecutar N-1.3 primero (no depende de nada), luego N-1.4",
  "signals_pending": 0,
  "mode": "wordflow",
  "chef_pass": "collect",
  "raw_refs": ["Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.3", "Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.4"]
}
```

Reglas heredadas del contrato (no repetir de memoria, leer el contrato si hay duda): R01 no codigo desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia (sha256 + read-back), R06 anotar antes de avanzar (Claude notas + Crazy Wall + handoff + memoria.md), R08 nunca escalar - si hay gap, gap_ladder 1..20 y FLAG + siguiente nodo.
