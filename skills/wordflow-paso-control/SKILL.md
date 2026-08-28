---
name: wordflow-paso-control
description: Control ejecutable PASO 0 a 8 download-zip-copy-plugin-deploy. Trigger on Download code, Download N, Desplegar N, OP1 parte, OP2 fork completo, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, X-Ray, council12, skill-creator. Una tarjeta por paso con IN DO FORBID GATE OUT NEXT. No dump. No rewrite origen.
metadata:
  type: workflow
  version: "1.1.0"
  status: CONTROL
  skill_creator: "init+validate 1.1.0"
  repo: maxbry123-commits/agentes
---

# Wordflow Paso Control

## Overview

Protocolo de control para que otra AI ejecute el pipeline Wordflow. No es el INPUT BLOCK. El INPUT BLOCK esta en `references/INPUT-BLOCK.md`. Cada PASO tiene tarjeta completa. Si un campo de tarjeta falta, el skill esta incompleto y hay que parar.

Leer tambien `references/SOURCE-MAP.md` `references/COUNCIL-12.md` `references/PASO-DETALLE.md` `references/AUDIT-SKILL-CREATOR.md`. Correr `scripts/check-tarjeta.sh` antes de declarar el skill listo.

## Arranque (skill-creator)

1. Validar este directorio con validate-skill.sh. Si FAIL, no ejecutar pipeline.
2. Cruzar `references/INPUT-BLOCK.md` items 1-32.
3. Correr council 12 in desde `references/COUNCIL-12.md`.
4. Identificar PASO_EN_CURSO in {0,1,2,3,4,5,6,7,8} y OUT in {OUT1,OUT2,OUT3}.
5. Ejecutar UNA tarjeta. Emitir EVIDENCE. Gate rojo = STOP.
6. LLM no imprime PASS.

### EVIDENCE por tarjeta

```
paso: N
op: OP1|OP2|none
out: OUT1|OUT2|OUT3|none
in_leidos: [paths]
cmds: [comandos]
sha_src: ...
sha_dst: ...
gate: OK|FAIL
next: ...
gaps: []
```

Token solo env. Alias Maxbry_123_tokens EXTERNAL_GH_B_TOKEN EXTERNAL_GH_C_TOKEN HF_TOKEN TARGET_REPO_TOKEN. Runtime Python o YAML. JSON solo ficha registrada.

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
GATE   los 3 repos muestran la guia zip
       SOURCE-MAP paths existen o gaps listados
OUT    lista path+sha de guias
NEXT   PASO 1
```

## PASO 1 — Download Action + lista repos (item 4,10)

```
IN     skills/research-download-chain/SKILL.md
       seccion 20 repos LOCK
       assets FORENSIC-PASS yml blob 5950933bcf567a34e197e96c59e845451124eb35
       assets FORENSIC-PASS py  blob bfc7634f500f6ded03b296ddfebc6dac35c56462
DO     COPIAR la lista 01-20 al input del workflow
         SearchOS SearXNG OpenDeepResearch GPT-Researcher STORM
         Shandu Vane Haystack Crawl4AI Perplexica
         Dagu Conductor Temporal Argo-Workflows Kestra
         LangGraph Hatchet Windmill Dagster Prefect
       disparar .github/workflows/research-download-chain-final.yml
       python3 scripts/research_download_chain.py \
         'Download code/archivos' '_work/research-download'
FORBID reescribir packer
       cambiar SPLIT_TARGET=12000000 MAX_ZIP=17000000
       add/remove slugs o cambiar orden
GATE   grep -c '"status": "COMPLETE"' MANIFEST == 20
       cada zip <= 17000000
       unzip -tq == 0
OUT    Download code/archivos/{slug}_{part}.zip
       RESEARCH_DOWNLOAD_MANIFEST.jsonl
NEXT   PASO 2
```

## PASO 2 — Bandeja Download code / Download N (item 11-14)

```
IN     N in {1,2,3} = tarea en curso
       zips PASO 1
       skill research-download-chain (enrutador)
DO     mkdir -p "Download code"
       mkdir -p "Download code/Download N"
       elegir OP1 o OP2
FORBID mezclar OP1 y OP2 en el mismo N sin evidencia
GATE   "Download code/Download N" existe
OUT    bandeja N
NEXT   OP1 o OP2
```

### OP1 — solo parte del code

```
DO     usar skill descarga para enrutar TODOS los repo a Download N
       seleccionar subset de paths que si se usan
       extraer SOLO ese subset
       COPY -> Download code/Download N/<mapped>
FORBID reescribir bytes del zip ni del origen
GATE   cada path pedido existe en N
       paths no pedidos no se copian a live_root
NEXT   cruzado
```

### OP2 — repo o agente completo

```
DO     si software_completo OR agente_completo
         crear raiz nueva en main del dest
         O fork y cablear esa raiz
       COPY tree completo fuente -> DEST_ROOT
FORBID dest owner/repo no declarado
GATE   tree dest cubre tree fuente
NEXT   cruzado
```

### Cruzado fuente (obligatorio)

```
DO     comparar repo fuente vs dest archivo a archivo
GATE   MISSING=0 EXTRA_inesperado=0 SHA_MISMATCH=0
OUT    evidencia paths+sha
NEXT   PASO 3 si OP1
       PASO 4 si OP2 ya vive en dest
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
DO     unzip -t ZIP
       unzip -q ZIP -d .staging/<slug>
       filtrar __MACOSX .DS_Store Thumbs.db path-traversal
       COPY (no rewrite) a la raiz donde va a VIVIR el archivo
       sha256(src)==sha256(dst)
       registrar plugin I/O obligatorio
         plugin_id, contrato, inputs, outputs, extension_point, estado
       JSON o prompt -> emitir .py EXTRACT_LITERAL
       reglas o skill -> .yaml
       leer UOOS + ficha ANTES de armar extension/plugin
       repetir el MISMO metodo con los demas archivos
FORBID editar origen
       auto-fix
       regenerar
       tocar archivo ya registrado
GATE   sha match
       plugin I/O presente
       UOOS 1 y 2 leidos
       ficha leida
OUT    copia en live_root + registro plugin
NEXT   PASO 4
```

## PASO 4 — GitHub Action copy queue (item 19-21)

Detalle YAML en `references/PASO-DETALLE.md`.

```
IN     owner/repo dest
       secret dest TARGET_REPO_TOKEN o alias de cuenta
       QUEUE controlada o find maxdepth 1
DO     on workflow_dispatch
       checkout source path=source fetch-depth 1
       checkout dest   path=target token=env dest fetch-depth 1
       GITHUB_TOKEN del source NO cruza dest
       for FILE in QUEUE
         test -f source/$FILE || exit 1
         cp source/$FILE target/$MAPPED
       map
         README pyproject -> raiz
         app code -> src/
         config -> config/
         tools -> scripts/
         tests -> tests/
       git add + UN commit + UN push
       NO force
       despues del copy registrar plugin I/O entrada y salida
FORBID llenar la raiz
       editar archivo ya registrado
       usar token source contra dest
GATE   cada FILE de QUEUE existe en dest mapeado
       plugin I/O en cada archivo nuevo
OUT    commit dest
NEXT   PASO 5
```

## PASO 5 — Estado por nombre + write atomico (item 22-24)

```
IN     Desplegar/Desplegar 1 lote
       tambien Desplegar 2 si el runtime vive ahi
DO     analizar arquitectura de CADA archivo del lote
       nombre = estado, contenido interno NO se toca para marcar
         pipeline.yaml              pendiente ORIGINAL PROTEGIDO
         process_pipeline.yaml      IA trabajando / conversion
         done_pipeline.yaml         auditado y convertido
         (alias Director) ♾️_pipeline.yaml y ✅_pipeline.yaml
       seguridad NO es el emoji
       seguridad = COPY + HASH + DIFF + VALIDATE + ATOMIC RENAME
       si hay que reescribir
         ORIGINAL READ-ONLY
         SHA256
         AI trabaja TEMP
         DIFF + syntax
         fail -> conservar original
         ok -> rename atomico
         probar que la version leida no cambio
FORBID editar bytes del original para marcar estado
GATE   original intacto
       OR sha_pre == sha_leida AND syntax ok
OUT    lote nombrado + temp limpio
NEXT   PASO 6
```

## PASO 6 — Deploy determinista + tokens (item 25,28)

```
IN     Desplegar/Desplegar 1 documentos
       Desplegar 2 lote runtime
       PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md
       PIPELINE/08_DESPLIEGUE_DETERMINISTA.md
       Wordflow Code/core/code_path_runner.py
       env Maxbry_123_tokens y aliases dest
DO     incorporar el metodo determinista de ESOS archivos
       no reescribir runner
       cablear deploy al FINAL del code path
         reception.convert -> goals -> planner -> code_path_runner
         -> loop_bridge -> evidence -> DEPLOY
       verificar que el motor deploy esta activo al final
       DRY_RUN default
       REAL solo si GITHUB_DEPLOY_REAL=1
FORBID JSON como runtime
       editar code_path_runner.py
GATE   cola del runner termina en DEPLOY
       docs Desplegar 1 leidos
OUT    ruta deploy activa
NEXT   PASO 7
```

## PASO 7 — Prompt code + estandares (item 26)

```
IN     prompt de code en lote Desplegar 1 / Desplegar 2
       PIPELINE ADVANCED_ENGINEERING_STANDARD
DO     BUSCAR el archivo prompt de code
       COPIAR dentro los estandares de programacion de alto nivel
       quedan como REGLA
       EXTRACT_LITERAL gana sobre mejorar
FORBID inventar un prompt nuevo si el lote ya tiene uno
GATE   prompt carga el estandar (grep regla)
OUT    prompt con estandares inyectados
NEXT   PASO 8
```

## PASO 8 — Router + 2 cables + 3 OUT + X-Ray (item 27-32)

Registry y diagrama en `references/PASO-DETALLE.md`.

```
IN     config/external_accounts.yaml
       env Maxbry_123_tokens  cuenta A maxbry123-commits
       env EXTERNAL_GH_B_TOKEN cuenta B abc1tienda-web
       env EXTERNAL_GH_C_TOKEN cuenta C HOLD
DO     registrar cada repo con ruta y modo
         SOURCE_01 SOURCE_02 read
         WORK_01 process
         DESTINATION_01 write
       incluir agentes TAREA-1 YAIWES Wordflow-Code frontend
       token paraguas Maxbry_123_tokens para repos Wordflow Code
       CABLE A = arquitectura programacion en Wordflow Code
       CABLE B = sistema de despliegue apply_push
       elegir UNA salida
FORBID write C si owner=HOLD
       deploy sin X-Ray y sin council
GATE   registry tiene path de cada repo
       OUT elegido
       X-Ray corrio
       council emitio 12 out
OUT    ver tarjetas OUT
NEXT   Tarea 3 copias solo con evidencia
```

### OUT1 chat UOOS

```
DO     emitir UOOS parte 1 y parte 2 en el chat
       formato .py o .yaml
       json solo si es ficha
GATE   ambos documentos UOOS presentes
```

### OUT2 dest remoto

```
DO     owner+repo desde docs del proyecto
       ELSE preguntar en chat cuenta y repo
       si repo no existe CREATE luego apply_push
GATE   dest resuelto AND push o create evidencia
```

### OUT3 cuenta A

```
DO     raiz organizada en maxbry123-commits/agentes
       src/ config/ scripts/ tests/
       + evidence
GATE   estructura destino existe
```

### X-Ray + council12

```
DO     audit_forensic sobre docs inbound
       MD -> code EXTRACT_LITERAL PIPELINE/57
       12 goals in -> council -> 12 goals out
       si modulo council no existe, crearlo en sandbox y registrar plugin
GATE   12 goals out emitidos
```

## Tarea 3 destinos (item 32, post evidencia)

```
canonical  skills/wordflow-paso-control/
copia      Metodo de trabajo/wordflow-paso-control/
copia      Download code/wordflow-paso-control/
copia      Desplegar/wordflow-paso-control/
copia      Refactoria/wordflow-paso-control/
parche     Wordflow Code/Readme/Readme1/ cable only
```

## STOP

path 404, token en claro, packer reescrito, SHA mismatch, plugin I/O ausente, lista 20 repos alterada, OUT2-C HOLD, council sin 12 out, validate-skill.sh FAIL.
