from pathlib import Path

path = Path("Readme arquitectura Yaiwes/README.md")
marker = "<!-- YAIWES_COMPONENT_INTEGRATION_LEDGER_20260906 -->"
block = """

<!-- YAIWES_COMPONENT_INTEGRATION_LEDGER_20260906 -->
## Integraciones verificadas — componentes incorporados a la estructura YAIWES

Esta sección es un delta quirúrgico aditivo. Consolida componentes físicamente incorporados durante el ciclo de integración; no reemplaza ni reescribe secciones anteriores.

| Componente | A/B/C | Ubicación en `Agente Yaiwes principal/` | Qué incorpora |
|---|---|---|---|
| APScheduler | B | `execution-orchestration/task-classifier-scheduler/` | scheduling de tareas, triggers, jobs, datastores, brokers y executors sync/async |
| AWS Step Functions Data Science SDK | B | `execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk/` | construcción, validación y serialización de máquinas de estado ASL, Chain/Graph y workflows |
| Ajv | C | `definition-registry/schema-contracts/ajv/` | validación determinista JSON Schema/JTD y errores estructurados de contrato |
| Apache APISIX | C | `mesh-routing-collaboration/apisix-api-gateway/` | gateway modular: routing, plugins, upstream/balancer, discovery, SSL/secrets sobre OpenResty/Lua |
| Apache Airflow | B | `execution-orchestration/dag-executor/apache-airflow/` | DAG scheduling/execution, TaskInstance, estado, pools, triggers, retries y executors |
| Argo Workflows | B | `execution-orchestration/dag-executor/argo-workflows/` | controlador Kubernetes de Workflow CRD, DAG/templates, pods, reconcile, persistencia y estado |
| Azure Durable Functions | B | `execution-orchestration/state-machine-executor/azure-durable-functions/` | orchestrators, activities, entities, TaskHubWorker, replay/checkpoint y providers de durabilidad |

### Regla común de conexión
`componente ➡️ adapter ➡️ Ficha Contract v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus ➡️ módulo arquitectónico ➡️ health/evidence`.

### Trazabilidad de integración
- APScheduler: MOVE `8a5c87b9b8ee79acab3de31e36a5eeb85d558d80`; verify run `34055059156`.
- AWS Step Functions DS SDK: MOVE `e7541c54575521d96a106e51e12f2a46e574eda8`; repair `637eadee85c7bfcc7c05f7ae5137114dc67d09d5`; verify run `34059002899`.
- Ajv: MOVE `95713304ee644b053efed4c9947af75bf71fd87c`; verify run `34061366845`.
- Apache APISIX: MOVE `ceda29c79c9a33fe054ec81e1da318b95c6d584d`; repair `5bce9fddd39da3f4f7b2d79d1f6ab2c428e75c6d`; verify run `34062622979`.
- Apache Airflow: MOVE `341ec322890e54d2ba1e817a13421821359f9a32`; verify SHA `f11f6b658b029713a7446bd0b72071a07f88fa64`; run `34065546339`.
- Argo Workflows: MOVE `5d54fd6e40cc9b35271bf3e6303a61f418288ab0`; verify SHA `c35e2383565ce7b0710afe6dfb876ea665dbbb89`; run `34066136917`.
- Azure Durable Functions: MOVE `02e9e0e6b3bb22b6084ea277f44cf3a90cbe551b`; build fix `3ab973ca6cd8993b0bcb35b7fad3556006f43f92`; verify run `34068938060`.
"""

text = path.read_text(encoding="utf-8")
if marker in text:
    print("marker already present; no change")
else:
    path.write_text(text.rstrip() + block.rstrip() + "\n", encoding="utf-8")
    print("surgical append prepared")
