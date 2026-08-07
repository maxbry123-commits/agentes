# A14 COMPLETA · Entrypoint Wordflow

## API

WordflowApp(state_dir).run_mission(goal, op_type=..., payload=...)
CLI: python -m wordflow.entrypoint --goal ... --state-dir ...

## Flujo

create_mission → InputBlock → Sentinela → Sheriff → ABI execute → Output Contract

## Siguiente

**A15** — Entrypoint extensión (plugin host)
