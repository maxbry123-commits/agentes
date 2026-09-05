# Orden universal al agente — despliegue v2.0 completo

```
Estás bajo despliegue determinista v2.0. NO analices, NO opines, NO propongas.
Solo ejecuta en orden y reporta la salida. Si falla, detente y pega el error:

1. python3 control-layer/despliegue/organizador.py --dry-run . --config config/deploy_config.yaml
   [ESPERA OK Director sobre plan.json]
2. python3 control-layer/despliegue/organizador.py . --config config/deploy_config.yaml
3. python3 control-layer/despliegue/desplegador.py . ./repos_listos --plan plan.json
4. python3 control-layer/despliegue/detector_version.py ./repos_listos
5. bash control-layer/despliegue/subir_a_github.sh MI_USUARIO ./repos_listos
6. python3 control-layer/despliegue/verificar.py ./repos_listos --plan plan.json
7. pega evidence.json y detente.
```
