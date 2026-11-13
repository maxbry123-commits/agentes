# Apache Airflow Core — Wordflow YAIWES

Clasificación: **B** — orquestador/workflow DAG.

**Función:** definir DAGs, dependencias, scheduling y estados de ejecución.

**Microflujo:** `DAG definition ➡️ scheduler/timetable ➡️ task dependencies ➡️ executor/runtime ➡️ DagRun/state ➡️ evidence`.

**Código movido:** `src/airflow/` y metadatos mínimos `pyproject.toml`, `hatch_build.py` desde `airflow-core`.

**No movido:** README, docs, tests y subproyectos auxiliares del monorepo.

**Cableado:** `adapter.py` + `WIRING.json` + `ficha.airflow.v2.json` hacia Universal Plugin Bus v2 / Ficha Contract v2. Fail-closed, 0% LLM.
