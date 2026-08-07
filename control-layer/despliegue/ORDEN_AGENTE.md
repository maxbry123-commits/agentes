# Orden universal al agente — despliegue v2.0

```
Estás bajo despliegue determinista v2.0. NO analices, NO opines, NO propongas.
Solo ejecuta en orden y reporta la salida. Si falla, detente y pega el error:

1. python3 control-layer/despliegue/organizador.py --dry-run . --config config/deploy_config.yaml
   [ESPERA OK Director sobre plan.json]
2. python3 control-layer/despliegue/organizador.py . --config config/deploy_config.yaml
3. python3 control-layer/despliegue/verificar.py ./repos_listos --plan plan.json
4. pega evidence.json y detente.
```

(Expandir con desplegador/detector/subir cuando existan en el repo del proyecto.)
