# YAIWES Wordflow — Argo Workflows

Clasificación: B — orquestador DAG/workflow.

Capacidad integrada: controlador Kubernetes de workflows con reconciliación, workqueues, DAG/templates, sincronización, persistencia y ejecución mediante el código Go movido desde el componente recuperado.

Flujo: `Workflow CRD ➡️ controller/workqueue ➡️ DAG/templates ➡️ executor/pods ➡️ reconcile ➡️ estado/evidencia`.

La conexión con YAIWES es fail-closed mediante `WIRING.json`, `ficha.argo-workflows.v2.json` y `adapter.py`. El README upstream permanece en el origen y no se usa como README del Wordflow.
