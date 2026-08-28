---
name: wordflow-paso-full
description: Control completo PASO 0-8 recuperado de commit 3ff622fe mas extract hermana-zip y X-Ray S1-S12. Trigger Download code, Download N, Desplegar N, Refactoria, OP1 OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, council12. Cruzar contra wordflow-paso-control y PREVIOUS-SKILL-1.1.md. No borrar el skill viejo hasta revision Director.
metadata:
  type: workflow
  version: "2.0.0-recovered"
  status: REVIEW
  previous_commit: "3ff622fea9a44d8b2200759bbd122a29575b3dd0"
  previous_skill: wordflow-paso-control
  repo: maxbry123-commits/agentes
---

# Wordflow Paso Full

Skill NUEVO. El skill `wordflow-paso-control` NO se borra. Cruzar este archivo vs `references/PREVIOUS-SKILL-1.1.md` vs `references/INPUT-BLOCK.md` vs `references/RULES.yaml`.

## Overview

Protocolo de control. INPUT BLOCK vive en `references/INPUT-BLOCK.md` items 1-32. Cada PASO es tarjeta IN DO FORBID GATE OUT NEXT. Ancla YAML `references/RULES.yaml`. LLM no imprime PASS.

Leer `references/SOURCE-MAP.md` `references/COUNCIL-12.md` `references/PASO-DETALLE.md` `references/EXTRACT-XRAY.md`. Correr `scripts/check-tarjeta.sh`.

## Arranque

1. validate-skill.sh. FAIL = no ejecutar.
2. Cruzar INPUT BLOCK 1-32.
3. Council 12 in.
4. PASO_EN_CURSO in 0-8 y OUT in OUT1-3.
5. Una tarjeta. EVIDENCE. Gate rojo STOP.

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

Token solo env. Maxbry_123_tokens EXTERNAL_GH_B_TOKEN EXTERNAL_GH_C_TOKEN HF_TOKEN TARGET_REPO_TOKEN. Runtime Python o YAML. JSON solo ficha.

## Tres raices

Download code = zips + `{slug}/` reconstruido + bandeja `Download N`. Extrae. No refactoriza. No despliega.

Desplegar = lote NUEVO `Desplegar N`. Runtime `Desplegar 2`. Estado por nombre. Deploy tail.

Refactoria = VIEJO. `source/` intocable. `new/` se escribe. Cable `Plan X-N -> Desplegar N -> Refactoria/refactoria-plan-x-N`.

## Actions lock

- assets/research-download-chain-final.yml blob `5950933bcf567a34e197e96c59e845451124eb35`
- assets/batch-copy-root-files.yml
- assets/extract-downloaded-zips.yml
- assets/download-extract-xray.yml
- python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
- bash scripts/extract_reconstruct.sh "Download code/archivos"
- python3 scripts/xray_crosscheck.py "Download code/archivos" audit work/source

No reescribir packer. Lista 01-20 lock.

## PASO 0 — Auditar fuentes (item 1-2,9)

```
IN     repo agentes
       repo TAREA-1
       repo Agentes-motores-Wordflow-YAIWES
       references/SOURCE-MAP.md
DO     abrir en los 3 repos
         docs/METODO_ZIP_COPY_DETERMINISTA.md
         docs/GUIA-DESPLIEGUE-ZIP-UNIVERSAL.md
       confirmar mismo metodo extract+copy
       auditar cada path del SOURCE-MAP
FORBID inventar guia si el path 404
GATE   los 3 repos muestran la guia zip O gaps listados
OUT    lista path+sha de guias
NEXT   PASO 1
```

## PASO 1 — Download Action + lista 20 (item 4,10)

```
IN     skills/research-download-chain/SKILL.md
       assets FORENSIC-PASS yml blob 5950933bcf567a34e197e96c59e845451124eb35
       assets FORENSIC-PASS py  blob bfc7634f500f6ded03b296ddfebc6dac35c56462
DO     COPIAR lista 01-20 al workflow
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
NEXT   PASO 1b
```

## PASO 1b — Extract hermana-zip + X-Ray S1-S12

Regla Director. Destino = misma raiz del zip. Reconstruct por slug. Prohibido auditar fragmento.

```
Download code/archivos/SearchOS_0001.zip
Download code/archivos/SearchOS_0002.zip
        -> Download code/archivos/SearchOS/
```

```
IN     zips + RESEARCH_DOWNLOAD_MANIFEST.jsonl
       assets/extract-downloaded-zips.yml
       assets/download-extract-xray.yml
       references/EXTRACT-XRAY.md
DO     S1 QUEUE
       S2 DOWNLOAD (packer lock, no clone suelto)
       S3 ZIP INTEGRITY unzip -tq
       S4 RECONSTRUCT todas las partes ordenadas a {slug}/
       S5 checkout source_commit del manifest (NO main)
       S6 inventory paths
       S7 missing extra
       S8 size
       S9 sha256
       S10 X-Ray
       S11 evidence audit/
       S12 global gate
       bash scripts/extract_reconstruct.sh "Download code/archivos"
       python3 scripts/xray_crosscheck.py "Download code/archivos" audit work/source
FORBID auditar SearchOS_0001 aparte
       comparar contra HEAD main
       reescribir packer
GATE   dest {slug}/ no vacio
       report audit/{slug}.xray.yaml
OUT    arbol reconstruido
NEXT   PASO 2
```

Nota lock. Files >8MiB el packer los parte en .chunks. SHA vs blob original puede diferir. No reescribir packer.

Un job GitHub Action `.github/workflows/download-extract-xray.yml`.

## PASO 2 — Bandeja Download N (item 11-14)

```
IN     N in {1,2,3}
       arbol reconstruido PASO 1b
DO     mkdir -p "Download code"
       mkdir -p "Download code/Download N"
       elegir OP1 o OP2
FORBID mezclar OP1 y OP2 sin evidencia
GATE   carpeta N existe
OUT    bandeja N
NEXT   OP1 o OP2
```

### OP1 parte

```
DO     enrutar todos los repo a Download N
       extraer SOLO subset
       COPY -> Download code/Download N/<mapped>
FORBID reescribir origen
GATE   paths pedidos existen
NEXT   cruzado
```

### OP2 completo

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
NEXT   PASO 3 si OP1. PASO 4 si OP2 en dest
```

## PASO 3 — Extract COPY + Fables + UOOS (item 15-18)

```
IN     METODO_ZIP_COPY_DETERMINISTA
       GUIA-DESPLIEGUE-ZIP-UNIVERSAL
       Desplegar/Desplegar 1
       UOOS parte 1 y parte 2
       PIPELINE/07 Enchufe Universal = Fables
       Wordflow Code/FICHAS/07_ENCHUFE_UNIVERSAL.ficha.v2.yaml
       GUIA_REGISTRO_PLUGINS
       PIPELINE/57 EXTRACT_LITERAL
DO     partir del arbol reconstruido PASO 1b
       COPY no rewrite a live_root
       sha256 src == sha256 dst
       plugin I/O obligatorio
         plugin_id contrato inputs outputs extension_point estado
       JSON o prompt -> .py EXTRACT_LITERAL
       reglas o skill -> .yaml
       leer UOOS + ficha ANTES de plugin
       repetir mismo metodo resto archivos
FORBID editar origen auto-fix regenerar tocar registrado
GATE   sha match AND plugin AND UOOS 1-2 AND ficha
OUT    copia live_root + plugin
NEXT   PASO 4
```

## PASO 4 — GitHub Action copy queue (item 19-21)

YAML en `references/PASO-DETALLE.md` y `assets/batch-copy-root-files.yml`.

```
IN     owner/repo dest
       secret dest
DO     workflow_dispatch
       checkout source path=source
       checkout dest path=target token=env dest
       GITHUB_TOKEN source NO cruza dest
       QUEUE o find maxdepth 1
       cp map raiz/src/config/scripts/tests
       un commit un push no force
       plugin I/O post-copy
FORBID llenar raiz force-push token source contra dest
GATE   QUEUE en dest mapeado AND plugin
OUT    commit dest
NEXT   PASO 5
```

## PASO 5 — Estado + write atomico (item 22-24)

```
IN     Desplegar/Desplegar N
       tambien Desplegar 2 si runtime vive ahi
DO     analizar CADA archivo
       nombre = estado contenido interno NO se toca
         archivo.yaml pendiente ORIGINAL
         process_archivo.yaml IA trabajando
         done_archivo.yaml auditado
         alias Director ♾️_ y ✅_
       seguridad = COPY HASH DIFF VALIDATE ATOMIC RENAME
       ORIGINAL READ-ONLY SHA256 AI en TEMP fail conserva original
FORBID editar bytes del original para marcar
GATE   original intacto OR sha_pre==sha_leida
OUT    lote nombrado
NEXT   PASO 6
```

## PASO 6 — Deploy determinista (item 25,28)

```
IN     Desplegar 1 y Desplegar 2
       PIPELINE/08 apply_push
       PIPELINE/08 determinista
       Wordflow Code/core/code_path_runner.py leer no editar
       env Maxbry_123_tokens
DO     incorporar metodo determinista de ESOS archivos
       cablear deploy al FINAL
         reception.convert -> goals -> planner -> runner
         -> loop_bridge -> evidence -> DEPLOY
       DRY_RUN default
       REAL si GITHUB_DEPLOY_REAL=1
FORBID JSON runtime editar runner
GATE   cola termina en DEPLOY
OUT    ruta deploy activa
NEXT   PASO 7
```

## PASO 7 — Prompt + estandares (item 26)

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

## PASO 8 — Router A/B/C + 3 OUT + X-Ray docs (item 27-32)

Diagrama en `references/PASO-DETALLE.md`.

```
IN     config/external_accounts.yaml
       env Maxbry_123_tokens A maxbry123-commits
       env EXTERNAL_GH_B_TOKEN B abc1tienda-web
       env EXTERNAL_GH_C_TOKEN C HOLD
DO     registry SOURCE read WORK process DEST write
       repos agentes TAREA-1 YAIWES Wordflow-Code frontend
       token paraguas Maxbry_123_tokens
       CABLE A Wordflow Code arquitectura
       CABLE B apply_push deploy
       elegir UNA salida
FORBID write C si HOLD
       deploy sin X-Ray y sin council
GATE   registry + OUT + X-Ray + 12 goals out
NEXT   Tarea 3 copias solo con evidencia
```

### OUT1
UOOS parte 1 y 2 en chat `.py` o `.yaml`. json solo ficha.

### OUT2
owner/repo desde docs o preguntar. Si no existe CREATE luego apply_push.

### OUT3
raiz organizada cuenta A + evidence.

### X-Ray docs inbound
MD -> code EXTRACT_LITERAL PIPELINE/57. Luego council 12 in/out. Si no existe crear en sandbox y registrar plugin.

## Tarea 3 destinos (item 32)

```
canonical  skills/wordflow-paso-full/
verificacion skills/wordflow-paso-control/   NO BORRAR hasta Director
copia      Metodo de trabajo/wordflow-paso-full/
copia      Download code/wordflow-paso-full/
copia      Desplegar/wordflow-paso-full/
copia      Refactoria/wordflow-paso-full/
parche     Wordflow Code/Readme/Readme1/CABLE-PASO-FULL.md
```

## STOP

nodo saltado, token en claro, packer reescrito, SHA fail, plugin ausente, source/ editado, fragmento auditado, C HOLD write, validate-skill FAIL, borrar skill viejo sin OK Director.
