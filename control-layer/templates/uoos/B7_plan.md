# PLAN — Plantilla B7 (UOOS Parte 1)
# SOURCE: CAPA DE CONTROL 1 · MODO_A despliegue / MODO_B construcción
# Archivo: plan/PLAN_CONSTRUCCION.md  o  plan/PLAN_DESPLIEGUE.md

## 1 · Tipo de plan
- [ ] CONSTRUCCION   (no hay código aún)
- [ ] DESPLIEGUE     (hay código / artefactos listos)

## 2 · Objetivo del plan
(1 frase verificable)

## 3 · Orden de archivos / fases
| Fase | Qué se hace | Criterio de aceptación |
|------|-------------|------------------------|
| F1   |             |                        |
| F2   |             |                        |
| F3   |             |                        |
| F4   |             |                        |

## 4 · Reglas de código (si CONSTRUCCION)
- Cabecera: ruta · responsabilidad · versión · deps
- Funciones ≤ 30 líneas
- `try/except: pass` PROHIBIDO
- Secretos solo en env / token_ref (nunca en repo)
- Máx 200 LOC por archivo (L02)

## 5 · Despliegue (si DESPLIEGUE)
- Lee: `config/token_ref.yaml` · `config/repo_destino.yaml` · `config/backup_destino.yaml`
- Pipeline fijo: organizador → desplegador → detector_version → subir → verificar
- Sin `evidence.json` + tag semver → NO está desplegado

## 6 · Checklist de cierre
- [ ] Todos los nodos del DAG en `done`
- [ ] Tribunal ≥ 70 y sin veto
- [ ] Evidencia completa por nodo
- [ ] Ningún secreto en el árbol del repo
- [ ] evidence.json presente (si hubo push)

## 7 · Prohibido
- Crear fases/tareas no listadas en B3
- Saltar el DAG
- Subir código sin pasar por el pipeline de despliegue
