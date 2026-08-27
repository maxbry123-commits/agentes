# PLAN GUÍA DE TRABAJO

**Repo:** maxbry123-commits/agentes · main  
Molde: PIPELINE/PLAN_MODELO_UNIVERSAL.md  
Plan misión intacto: PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md  
Este archivo es la guía operativa. No reescribe YAIWES.

## RAÍCES VIVAS
Desplegar · PIPELINE · Método de trabajo · Refactoria · Yaiwes wordflow · Wordflow Code · notas-trabajo-grock

`despliegue/` ≠ `Desplegar/`.

## CABLEADO
Plan X número N → Desplegar/Desplegar N/ → Refactoria/refactoria-plan-x-N/
Sin lote: WAIT. No crear carpeta vacía.

Desplegar = inbox del lote.  
Refactoria = mesa (source/ foto del vivo, new/ reescritura, ×3, luego destino).

## FASE 2 — CÓMO SE HACE (detalle)

Objetivo: el Director sube un lote; Grok audita docs vs code; se diseña lo que falta con plugins; se aprueba; se cablea un plan ejecutable para GPT.

### Paso 1 — Lote
El Director sube documentos y code a `Desplegar/Desplegar N/`.
ZIP: hash → extraer a staging (el ZIP no se vacía) → inventario.
N = número de este plan. No mezclar con otro N.

### Paso 2 — X-Ray cruzado (4 u 8 pasadas)
Comparar el lote contra el code vivo del Wordflow.
12 goals mínimos:
1. Qué está en Desplegar y no en el code.
2. Qué está en el code y no en Desplegar.
3. Qué está incompleto.
4. Qué se puede mejorar.
5. Dónde se ubica cada archivo y por qué.
6. Qué existe y funciona.
7. Qué rompe.
8. Qué bloquea.
9. Qué falta.
10. Cómo se soluciona cada GAP.
11. Hot path: ¿se toca? si sí, paridad obligatoria.
12. Checkpoint de lo cerrado al 100%.

Cada hallazgo: CHAT_APROBADO | PIPELINE_EXISTENTE | INVESTIGACION_NUEVA | GAP | DESCARTADO.
Checkpoint en `PIPELINE/checkpoints/{{PLAN_ID}}/`.
NO-STOP: GAP → diagnosticar → resolver → verificar → registrar → seguir.

### Paso 3 — Diseño de code faltante
Grok usa el prompt de chat 1 solo para diseñar el code que falta.
Regla plugin: el núcleo consulta el registro; kernel_N = fila nueva; no se reescribe el base.
extension-kernel = ejemplo (abi-mount, registry, mount-guard). No dump.

### Paso 4 — Carga y debate
El Director sube el code nuevo a Desplegar N.
Se revisa y se aprueba antes de integrar.

### Paso 5 — Cablear el plan
Grok instancia `PIPELINE/PLAN_{{PLAN_ID}}.md` desde el molde.
Cablea:
- ENLACE_DESPLEGAR = Desplegar/Desplegar N/
- ENLACE_REFACTORIA = Refactoria/refactoria-plan-{{PLAN_ID}}/
- destinos Yaiwes wordflow | Wordflow Code
- archivos a modificar en source/
- guías y método
- raíz de cada archivo
GPT solo trabaja en esa ruta.

Archivo que pisa un vivo: source/ → new/ → ×3 (diff, tests, checklist) → destino.
No borrar source/ en el mismo task.

Luego Fase 3, 4, 5 con el mismo método.

## REGLAS
FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.
Anotar = archivo nuevo; no reescribir el base.
Hot path: extensions/wordflow/engine/code_path_runner.py
