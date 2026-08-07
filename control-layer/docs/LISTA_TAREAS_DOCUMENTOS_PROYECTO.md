# Lista de tareas — documentos del proyecto (actualizada)

## D1–D10 plantillas / research

| ID | Documento | Estado | Siguiente acción |
|----|-----------|--------|------------------|
| D1 | PROJECT_MANIFEST | ✅ v2.0 | — |
| D2 | state.json | ❌ | research + plantilla 100× |
| D3 | nodes/*.yaml | ⚠️ loader sí / plantilla research no | research + B3 v2 |
| D4 | dag/*.yaml | ❌ | research + plantilla |
| D5 | loops/*.yaml | ✅ engine + B5 v2 | research externo opcional |
| D6 | council/tribunal | ❌ | research + plantilla |
| D7 | plan/ | ⚠️ pipeline guía añadida | D7 plan general + pipeline docs |
| D8 | recovery/ | ❌ | research + plantilla |
| D9 | config/ | ⚠️ token/repo/backup + deploy_config | unificar |
| D10 | RECETA_AGENTE | ❌ | research + plantilla |

## PIPELINE (guía plan — NO runtime)

| Item | Estado |
|------|--------|
| FASE_TEMPLATE | ✅ |
| AUDIT_INDEX_TEMPLATE | ✅ |
| PIPELINE_GUIDE | ✅ |
| plan/pipeline/*.md por fase 00–20 | ❌ generar bajo proyecto |
| skill audit_index determinista | ❌ opcional |
| P1-CONVERTIDOR (doc→ficha) | ❌ track aparte |

## Despliegue determinista v2

| Item | Estado |
|------|--------|
| deploy_config.yaml template | ✅ |
| organizador.py dry-run + protected + SIN_REGLA | ✅ |
| verificar.py evidence | ✅ |
| ORDEN_AGENTE | ✅ |
| desplegador.py idempotente | ❌ reusar/portar v1 |
| detector_version.py + CHANGELOG | ❌ |
| subir_a_github.sh | ❌ |
| verificar remoto ls-remote | ❌ (local ok) |

## Loops / control-layer

| Item | Estado |
|------|--------|
| Engine A–F + P0–P3 | ✅ |
| Runtime agentes reales (executor_factory) | ❌ |
| ENCHUFE boot → nodes | ❌ |

## Orden de retoma recomendado
1. D2 state.json plantilla
2. D3 nodes plantilla research
3. D4 dag plantilla
4. plan/pipeline fases bajo proyecto concreto
5. desplegador + detector + push
6. D6–D8–D10
7. runtimes reales
