# SALIDA W10 — Despliegue determinista 5 scripts

**Estado: CERRADA 100%**

| Paso | Script |
|------|--------|
| 1 dry-run / organize | `despliegue/organizador.py` |
| 2 copy + git | `despliegue/desplegador.py` |
| 3 semver + CHANGELOG | `despliegue/detector_version.py` |
| 4 push | `despliegue/subir_a_github.sh` |
| 5 evidence | `despliegue/verificar.py` |

Orden: `despliegue/ORDEN_AGENTE.md`  
Config: `templates/despliegue/deploy_config.yaml` · PROJECT `config/`

0% LLM · token vía env del proyecto (D9)

## Siguiente
**W11** — validate_schemas skill
