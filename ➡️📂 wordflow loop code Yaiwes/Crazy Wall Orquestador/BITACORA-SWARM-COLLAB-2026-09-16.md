# BITÁCORA SWARM COLLAB — 2026-09-16

Contrato: `yaiwes.swarm-collaboration-queue/v1`

Cola autoritativa: `➡️📂 Wordflow LOOP Yaiwes/Crazy Wall Orquestador/SWARM-COLLAB-QUEUE-2026-09-16.json`

Reglas activas:
- 1 chat = 1 nodo.
- 1 path = 1 writer activo.
- READ FRESH antes de CLAIM.
- CLAIM obligatorio antes de escribir.
- Máximo 3 pasos de ejecución por tarea.
- PASS sólo con prueba real + evidencia observable.
- No force push.
- No reabrir CODE_GRAPH 30/30 sin evidencia nueva.

## Apertura

- `WF-HF-01` — `IN_PROGRESS` — owner `ORCHESTRATOR_SOL`.
- `WF-COPY-02` — `FREE`.
- `WF-PROFILES-03` — `FREE`.
- `WF-INTAKE-04` — `FREE`.
- `WF-AUTOLOOP-05` — `FREE`.
- `WF-RECOVERY-06` — `FREE`.

Cada ejecutor debe actualizar únicamente su nodo al reclamarlo y registrar: `owner`, `claimed_at`, `base_sha`. Al cerrar debe aportar prueba real, path + SHA256 de archivos tocados y evidencia reproducible.
