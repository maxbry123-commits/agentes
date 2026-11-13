# EVIDENCE PLAN30 T17 — HISTORY REFUTATION EngineRegistry

Fecha: 2026-09-07.
Contrato: `tel.workflow/v4`.
Modo: `FAIL_CLOSED_EXECUTION_LOOP`.
Nodo: `PLAN30_T17_PLUGIN_REGISTRY_WIRING`.
Paso Director: 2 — SOLO COPIAR código ya seleccionado.
HEAD pre-delta: `152a466a80fc2f72ffdefa721b439a0359540c71`.

## StrategyDelta ejecutado
Se inspeccionó el historial Git de la referencia stale `extensions/wordflow_kernel/engine_registry.py` sin restaurar, mover ni reescribir código.

## Provenance exacta
- Repo: `maxbry123-commits/agentes`.
- Ruta histórica: `extensions/wordflow_kernel/engine_registry.py`.
- Commit histórico inspeccionado: `863263c5b3b4313e20940bc7ee74c9afc9eca10c`.
- Blob SHA: `500d121878f4102b0b58cc2e743a01e00af13b15`.
- URL: `https://github.com/maxbry123-commits/agentes/blob/863263c5b3b4313e20940bc7ee74c9afc9eca10c/extensions/wordflow_kernel/engine_registry.py`.
- Función observada: `EngineRegistry.load/attach/list/get`; valida Ficha mediante `ficha_loader`; el propio docstring la etiqueta `T20 — EngineRegistry` y declara que no ejecuta engines.
- Commit posterior de consolidación: `7583407b97de10f4e53a0f0386c79d01f4e92e1f`, mensaje `organize: consolidate YAIWES code, docs and extraction-only Actions`.

## Refutación fail-closed
Este archivo es un donor histórico real, pero NO se selecciona/copía en T17 todavía: (1) está etiquetado T20, no T17; (2) depende de `ficha_loader`; (3) no prueba compatibilidad con el Capability Registry runtime requerido por T17; (4) la ruta fue retirada durante consolidación; (5) no existe destino T17 autorizado demostrado para copiarlo sin riesgo de restaurar arquitectura obsoleta.

Resultado: `HISTORICAL_DONOR_PROVEN_BUT_NOT_SELECTED` + `COPY_BLOCKED_DESTINATION_COMPATIBILITY`.
No COPY, no MOVE, no REWRITE, no cambio de porcentaje; T17 continúa `EN_CURSO`.

## Siguiente StrategyDelta
Buscar un donor CURRENT/SELECTED de Capability Registry runtime en `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` y repos auxiliares autorizados, registrando ruta+URL+commit/blob SHA+función+destino antes de COPY_ONLY. No reutilizar el donor histórico salvo nueva evidencia explícita de compatibilidad y destino.

Estado: `ACTIVE_LOOP`.
