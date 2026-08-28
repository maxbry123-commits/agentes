---
name: wordflow-paso-control
description: Control recuperado PASO 0-8 mas extract al lado del zip y X-Ray S1-S12. Trigger on Download code, Download N, Desplegar N, Refactoria source/new, OP1 OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, council12, RULES.yaml. Tarjetas IN DO FORBID GATE OUT NEXT. No auditar fragmentos. No rewrite packer.
metadata:
  type: workflow
  version: "1.4.0-recovered"
  status: CONTROL
  ancla: references/RULES.yaml
  repo: maxbry123-commits/agentes
---

# Wordflow Paso Control

## Overview

Skill RECUPERADO. Cuerpo = tarjetas de control 0-8 (version 1.1) + roles de raices (1.2) + extract/X-Ray (1.3). Ancla YAML = `references/RULES.yaml`. Si texto y YAML discrepan, gana YAML. `omit_steps: false`. LLM no imprime PASS.

Leer `references/INPUT-BLOCK.md` `references/RULES.yaml` `references/SOURCE-MAP.md` `references/PASO-DETALLE.md`. Correr `scripts/check-tarjeta.sh`.

## Arranque

1. Validar skill-creator. FAIL = no ejecutar pipeline.
2. Cruzar INPUT BLOCK 1-32.
3. Identificar PASO_EN_CURSO y OUT.
4. Ejecutar UNA tarjeta. Emitir EVIDENCE.
5. Token solo env. Runtime Python o YAML.

### EVIDENCE

```
paso: N
op: OP1|OP2|none
out: OUT1|OUT2|OUT3|none
in_leidos: []
cmds: []
sha_src: ...
sha_dst: ...
gate: OK|FAIL
next: ...
gaps: []
```

## Tres raices

### Download code
Inbox de codigo bajado. `archivos/` = zips + arbol reconstruido `{slug}/`. `Download N/` = bandeja de tarea. Extrae. No refactoriza. No despliega.

### Desplegar
Inbox lote NUEVO `Desplegar/Desplegar N/`. Runtime en `Desplegar 2`. Estado por nombre. Estandares. Deploy tail. No editar origen.

### Refactoria
Version VIEJA. `source/` intocable. `new/` se escribe. Cruzado x3. Cable `Plan X-N -> Desplegar N -> Refactoria/refactoria-plan-x-N`.

## Actions en el skill

- `assets/research-download-chain-final.yml` blob `5950933bcf567a34e197e96c59e845451124eb35`
- `assets/batch-copy-root-files.yml`
- `assets/extract-downloaded-zips.yml`
- `assets/download-extract-xray.yml`
- Cmd download `python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'`
- Extract `bash scripts/extract_reconstruct.sh "Download code/archivos"`
- X-Ray `python3 scripts/xray_crosscheck.py "Download code/archivos" audit work/source`

Lista 01-20 lock en skill research-download-chain. No reescribir packer.

## Extract + X-Ray (nuevo, no sustituye tarjetas)

Misma raiz que el zip. Reconstruct por slug. Prohibido auditar `_0001` solo.

```
Download code/archivos/SearchOS_0001.zip
Download code/archivos/SearchOS_0002.zip
        -> Download code/archivos/SearchOS/
```

Cadena unica S1 QUEUE S2 DOWNLOAD S3 ZIP INTEGRITY S4 RECONSTRUCT S5 SOURCE COMMIT S6 INVENTORY S7 MISSING/EXTRA S8 SIZE S9 SHA-256 S10 X-RAY S11 EVIDENCE S12 GATE.

Compare contra `source_commit` del MANIFEST.jsonl. No contra main. unzip extrae. Python hashea.

## PASO 0 — Auditar fuentes

```
IN     agentes TAREA-1 YAIWES
       references/SOURCE-MAP.md
DO     abrir guia zip en los 3 repos
       auditar cada path SOURCE-MAP
FORBID inventar guia 404
GATE   gaps listados o paths existen
OUT    path+sha
NEXT   PASO 1
```

## PASO 1 — Download Action + lista 20

```
IN     research-download-chain SKILL
       assets FORENSIC yml/py blobs lock
DO     copiar lista 01-20 al workflow
         SearchOS SearXNG OpenDeepResearch GPT-Researcher STORM
         Shandu Vane Haystack Crawl4AI Perplexica
         Dagu Conductor Temporal Argo-Workflows Kestra
         LangGraph Hatchet Windmill Dagster Prefect
       disparar research-download-chain-final.yml
       python3 scripts/research_download_chain.py \
         'Download code/archivos' '_work/research-download'
FORBID reescribir packer
       cambiar SPLIT_TARGET=12000000 MAX_ZIP=17000000
       add/remove slugs
GATE   MANIFEST COMPLETE == 20
       zip <= 17000000
       unzip -tq == 0
OUT    {slug}_{part}.zip + MANIFEST.jsonl
NEXT   EXTRACT reconstruct luego PASO 2
```

## PASO 1b — Reconstruct + X-Ray

```
IN     zips en Download code/archivos
       RESEARCH_DOWNLOAD_MANIFEST.jsonl
DO     bash scripts/extract_reconstruct.sh "Download code/archivos"
       python3 scripts/xray_crosscheck.py "Download code/archivos" audit work/source
FORBID auditar cada parte aparte
       comparar contra main
GATE   dest Download code/archivos/{slug}/ no vacio
       X-Ray report en audit/
OUT    arbol reconstruido + audit/*.xray.yaml
NEXT   PASO 2
```

Nota lock: files >8MiB el packer los parte en .chunks. SHA vs blob original puede diferir. No reescribir packer.

## PASO 2 — Bandeja Download N

```
IN     N in {1,2,3}
       arbol reconstruido
DO     mkdir -p "Download code"
       mkdir -p "Download code/Download N"
       elegir OP1 o OP2
FORBID mezclar OP1 y OP2 sin evidencia
GATE   carpeta N existe
OUT    bandeja N
NEXT   OP1 o OP2
```

### OP1 parte del code

```
DO     enrutar todos los repo a Download N
       extraer SOLO subset
       COPY -> Download code/Download N/<mapped>
FORBID reescribir origen
GATE   paths pedidos existen
NEXT   cruzado
```

### OP2 repo o agente completo

```
DO     raiz nueva en main dest O fork y cablear
       COPY tree completo
FORBID dest no declarado
GATE   tree dest cubre fuente
NEXT   cruzado
```

### Cruzado

```
DO     comparar fuente vs dest archivo a archivo
GATE   MISSING=0 EXTRA_inesperado=0 SHA_MISMATCH=0
OUT    evidencia paths+sha
NEXT   PASO 3 si OP1; PASO 4 si OP2 en dest
```

## PASO 3 — Extract COPY + Fables + UOOS

```
IN     RULES.yaml extract_zip
       UOOS 1 y 2
       PIPELINE/07 Enchufe = Fables
       ficha.v2
       GUIA_REGISTRO_PLUGINS
       PIPELINE/57 EXTRACT_LITERAL
DO     COPY reconstruido a live_root
       sha256 match
       plugin I/O obligatorio
       JSON|prompt -> .py
       reglas|skill -> .yaml
       repetir mismo metodo resto archivos
FORBID editar origen auto-fix regenerar
GATE   sha match AND plugin AND UOOS leidos
OUT    copia live_root + plugin
NEXT   PASO 4
```

## PASO 4 — GitHub Action copy queue

Detalle `assets/batch-copy-root-files.yml` y `references/PASO-DETALLE.md`.

```
IN     owner/repo dest
       secret dest
DO     workflow_dispatch
       checkout source path=source
       checkout dest path=target token=env dest
       QUEUE o find maxdepth 1
       cp map organico raiz/src/config/scripts/tests
       un commit un push
       plugin I/O post-copy
FORBID force-push token source contra dest llenar raiz
GATE   QUEUE en dest mapeado
OUT    commit dest
NEXT   PASO 5
```

## PASO 5 — Estado + write atomico

```
IN     Desplegar/Desplegar N
DO     analizar cada archivo
       nombre = estado
         archivo.yaml pendiente ORIGINAL
         process_archivo.yaml en proceso
         done_archivo.yaml auditado
         alias Director ♾️_ y ✅_
       seguridad = COPY HASH DIFF VALIDATE ATOMIC RENAME
       fail -> conservar original
FORBID editar bytes del original para marcar
GATE   original intacto OR sha_pre==sha_leida
OUT    lote nombrado
NEXT   PASO 6
```

## PASO 6 — Deploy determinista

```
IN     Desplegar 1 y Desplegar 2
       PIPELINE/08 apply_push + determinista
       code_path_runner.py leer no editar
       env Maxbry_123_tokens
DO     cablear deploy al FINAL
         reception.convert -> goals -> planner -> runner
         -> loop_bridge -> evidence -> DEPLOY
       DRY_RUN default
       REAL si GITHUB_DEPLOY_REAL=1
FORBID JSON runtime editar runner
GATE   cola termina en DEPLOY
OUT    ruta deploy activa
NEXT   PASO 7
```

## PASO 7 — Prompt + estandares

```
IN     prompt code del lote Desplegar
       ADVANCED_ENGINEERING_STANDARD
DO     BUSCAR prompt
       COPIAR estandares dentro como REGLA
       EXTRACT_LITERAL gana
FORBID inventar prompt si el lote ya tiene
GATE   prompt carga estandar
OUT    reglas inyectadas
NEXT   PASO 8
```

## PASO 8 — Router A/B/C + 3 OUT + X-Ray docs

```
IN     external_accounts.yaml
       env Maxbry_123_tokens A maxbry123-commits
       env EXTERNAL_GH_B_TOKEN B abc1tienda-web
       env EXTERNAL_GH_C_TOKEN C HOLD
DO     registry SOURCE read WORK process DEST write
       CABLE A Wordflow Code
       CABLE B apply_push
       elegir OUT
FORBID write C si HOLD
       deploy sin council
GATE   registry + OUT + X-Ray docs + 12 goals out
NEXT   Tarea 3 copias solo con evidencia
```

### OUT1
UOOS parte 1 y 2 en chat `.py` o `.yaml`. json solo ficha.

### OUT2
owner/repo desde docs o preguntar. Si no existe CREATE luego apply_push.

### OUT3
raiz organizada cuenta A + evidence.

### X-Ray docs inbound
MD -> code EXTRACT_LITERAL. Luego council 12 in/out.

## Tarea 3 destinos

```
skills/wordflow-paso-control/
Metodo de trabajo/wordflow-paso-control/
Download code/wordflow-paso-control/
Desplegar/wordflow-paso-control/
Refactoria/wordflow-paso-control/
Wordflow Code/Readme/Readme1/CABLE-PASO-CONTROL.md
```

## STOP

nodo saltado, token en claro, packer reescrito, SHA fail, plugin ausente, source/ editado, fragmento auditado, C HOLD write, validate-skill FAIL.
