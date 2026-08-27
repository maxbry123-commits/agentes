# PLAN_LIMPIEZA_Y_GAPS — instancia del molde (GPT ejecuta esto)

Instanciado por Grok desde:
PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2.md
+ PARCHE_1 + PARCHE_1-1
+ DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md (solo reglas de inbox; no hay lote)
No editar los archivos de Guia-plan. No reescribir PLAN_YAIWES_AGENTE_WORDFLOW.md.
FAIL-CLOSED. LLM no declara PASS. HTTP 200 ≠ PASS.

## INPUT BLOCK

```text
PLAN_ID:            LIMPIEZA_GAPS
AGENTE:             GPT
TAREA:              Cerrar gaps YAIWES G1-G7 con evidencia; luego listar basura de main; borrar solo con aprobación Director
OBJETIVO:           G1/G3/G4 con run CI real; G2 residual explícito; G5 BLOCKER si no hay source; G6/G7 no reabrir sin causa; limpieza de raíces no canónicas
FUENTE:             PLAN_YAIWES_AGENTE_WORDFLOW.md + .github/workflows/verify-gap-indexes.yml + árbol main
DESTINOS:           PIPELINE/checkpoints/LIMPIEZA_GAPS/ ; Refactoria/refactoria-plan-LIMPIEZA_GAPS/ si se reescribe vivo
ALCANCE:            gaps G1-G7 + inventario de basura + borrado solo aprobado
FUERA_DE_ALCANCE:   editar Guia-plan subido; fabricar p01-p12; tocar hot path sin paridad; force-push; inventar G1_G3_CI_PASS.md
CRITERIO_PASS:      cada Sn con ficha + commit/read-back o BLOCKER documentado
CRITERIO_100%:      G1/G3/G4 con URL de Actions run; inventario B aprobado o HOLD; 0 fake PASS
N_DESPLEGAR:        WAIT
HOT_PATH_SE_TOCA:   NO
```

ENLACE_DESPLEGAR: WAIT (no crear Desplegar vacío)
ENLACE_REFACTORIA: Refactoria/refactoria-plan-LIMPIEZA_GAPS/
ENLACE_CHECKPOINT: PIPELINE/checkpoints/LIMPIEZA_GAPS/

## DAG
INPUT → BIND → SHERIFF → S1 → S2 → S3 → S4 → S5 → 12-ASK → VEREDICTO
NO-STOP. GAP → diagnosticar → resolver → registrar → seguir.

## S1 — G1 y G3 (CI real)
```yaml
id: S1
objetivo: Cerrar G1 symbol index y G3 test-assert solo con run de verify-gap-indexes
goal_in: Evidencia CI o OPEN explícito
enlace_desplegar: WAIT
enlace_refactoria: Refactoria/refactoria-plan-LIMPIEZA_GAPS/
destino_canonico: PIPELINE/checkpoints/LIMPIEZA_GAPS/S1.md
tag: GAP
sheriff: extensions/wordflow/standards/sheriff.py
guardian: mount-guard + VerdictAuthority
watchdog: extensions/wordflow/engine/watchdog.py
hot_path_afectado: false
estado: PLANNED
checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S1.md
```
Acción: pedir al Director Run workflow https://github.com/maxbry123-commits/agentes/actions/workflows/verify-gap-indexes.yml
PASS solo si: run verde + URL + G1_G3_CI_PASS.md escrito por Actions. No crear ese md a mano.

## S2 — G4 log CI
```yaml
id: S2
objetivo: Adjuntar log/URL del mismo run como evidencia G4
tag: GAP
estado: PLANNED
checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S2.md
```
Sin run = OPEN. No markdown inventado.

## S3 — G2 parcial
```yaml
id: S3
objetivo: Dejar G2 PARCIAL y listar residual OPEN. No forzar PASS.
tag: PIPELINE_EXISTENTE
estado: PLANNED
checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S3.md
```

## S4 — G5 G6 G7
```yaml
id: S4
objetivo: G5 BLOCKER si no hay source p01-p12. G6/G7 no reabrir si cable OpenClaw sigue.
tag: GAP
estado: PLANNED
checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S4.md
```
Prohibido fabricar módulos p01-p12.

## S5 — Inventario limpieza (NO borrar aún)
```yaml
id: S5
objetivo: Listar paths no canónicos. Borrar solo líneas que el Director marque SI.
tag: INVESTIGACION_NUEVA
estado: PLANNED
checkpoint: PIPELINE/checkpoints/LIMPIEZA_GAPS/S5.md
```
Vivo (no listar como basura): Desplegar, PIPELINE/Guia-plan (docs subidos), PIPELINE/planes, PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md, PIPELINE/PLAN_LIMPIEZA_Y_GAPS.md, Método de trabajo, Refactoria, Yaiwes wordflow, Wordflow Code, extensions/wordflow (hot path).
Candidatos a listar: agente-yaiwes, agents, TASK-GAPS, PIPELINE/00-64 históricos, wordflow/, groups/, memory/, docs sueltos.
despliegue/ ≠ Desplegar/. No confundir.
Salida S5 = tabla path | por qué | SI/NO Director. Cero borrados sin SI.

## Ficha por Sn
```text
SALIDA:
COMMIT:
READBACK:
ENLACE_GITHUB:
ERRORES:
STATUS: PASS|FAIL|OPEN|BLOCKED
```

## 12-ASK al final (evidencia, no opinión)
1 goal_in literal  2 evidencia GitHub por Sn  3 hot path no tocado  4 sin duplicar lego
5 nada inventado  6 ×3 si hubo Refactoria  7 checkpoint recuperable  8 sin ZIP basura
9 tags  10 GAP con diagnóstico  11 plugins solo si se reescribió  12 veredicto no es autodclaración

## VEREDICTO
ESTADO: PLANNED
FIRMADO_POR: pendiente sheriff + guardian + watchdog
