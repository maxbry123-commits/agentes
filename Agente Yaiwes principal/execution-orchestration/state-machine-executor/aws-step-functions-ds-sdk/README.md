# AWS Step Functions Data Science SDK — Wordflow YAIWES

## Rol
Componente clasificado **B**: workflow/orquestador de máquinas de estado. Compila estados y cadenas Python a grafos Amazon States Language y administra creación, ejecución, consulta y parada de workflows Step Functions.

## Microflujo
`State/Chain -> Graph/ValidationVisitor -> ASL JSON -> Workflow -> boto3 Step Functions -> Execution -> events/output`.

## Integración YAIWES
Destino canónico: `execution-orchestration/state-machine-executor/aws-step-functions-ds-sdk/`.
El código upstream útil vive en `stepfunctions/`; los tests se conservan en `tests/`. El README upstream, documentación, ZIP y auxiliares no se trasladan.

## Enchufe universal
`adapter.py` expone una superficie import-safe para `UniversalPluginBus v2` y `ficha.aws_step_functions.v2.json` declara I/O, ejecución, sandbox, evidencia, telemetría, health y failover. `WIRING.json` fija las rutas del bus y del contrato.

## Estado
`testing` hasta completar las 10 pasadas X-Ray y verificación repetible. Fail-closed: sin evidencia no se marca VERIFIED_CLOSED.
