# Handoff - agente `smolagents` (agent_sources/smolagents, verificado pip-installable)

Reemplaza a `claude_code` y a `opencode` en este slot. Motivo del cambio: ver `Claude notas/NOTA-2026-09-20-swap-agentes-fase0.md`.

Verificado hoy: `pyproject.toml` con `[project.scripts] smolagent = "smolagents.cli:main"` y `webagent = "..."`, build-backend setuptools estandar, dependencias pip normales (huggingface-hub, requests, rich, jinja2). Instalable con pip sin toolchain adicional.

Fuente de verdad: `Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml` + `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml`.

## N-1.3 - Montar mcode (unico gap de descarga)
- accion: Git Data API - POST /git/trees (mode=160000, type=commit) -> commits -> refs
- metodo_probado_en: commit f13f8f9
- acceptance: GET agent_sources/mcode devuelve html_url a repo externo
- Verificado hoy: mcode NO existe en agent_sources/, el gap sigue abierto

## N-1.4 - Subir 5 keys NVIDIA como secrets + test real
- accion: sellado libsodium via ctypes sobre libsodium.so.23
- metodo_probado_en: memoria.md seccion 11 (7 GROQ)
- secrets: NVIDIA_API_KEY_1..5 - base_url https://integrate.api.nvidia.com/v1 - modelo minimaxai/minimax-m2.7
- acceptance: GET /actions/secrets lista los 5 + test HTTP 200 desde Actions (el sandbox no tiene red a NVIDIA)
- [FLAG-1 sigue abierto]: keys ya expuestas en texto plano en repo publico, subir el secret no revoca la exposicion previa

## N-2.11 - Construir la biblioteca RAG (13 subcarpetas vacias)
- carpetas: templates / skills / plugins / prompts
- regla asociada: R11 (consultar biblioteca antes de escribir cualquier schema)
- bloquea: N-1.5

## Contrato de salida esperado
```json
{
  "mission_id": "N-1.3+N-1.4+N-2.11-smolagents-2026-09-20",
  "status": "WAITING_SIGNAL",
  "summary": "",
  "goal_restated": "Montar mcode + subir 5 NVIDIA keys selladas con test real + construir biblioteca RAG consultable",
  "steps_done": [],
  "steps_pending": ["N-1.3", "N-1.4", "N-2.11"],
  "artifacts": [],
  "contracts_active": ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"],
  "sheriff_state": "YELLOW",
  "risk_score": 4,
  "evidence_hash": null,
  "errors": [],
  "warnings": ["FLAG-1 abierto: keys NVIDIA expuestas antes de este nodo"],
  "next_action": "N-1.3 primero (no depende de nada), luego N-1.4, luego N-2.11",
  "signals_pending": 0,
  "mode": "wordflow",
  "chef_pass": "collect",
  "raw_refs": ["Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.3", "Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-1.4", "Claude notas/PLAN-DSL-DAG-01-NODOS.yaml#N-2.11"]
}
```

Reglas heredadas del contrato: R01 no codigo desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia, R06 anotar antes de avanzar, R08 nunca escalar - gap_ladder 1..20.
