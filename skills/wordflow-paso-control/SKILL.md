---
name: wordflow-paso-control
description: Control por PASO 1-8 del pipeline download-zip-copy-plugin-deploy. Trigger on Download N, Desplegar N, OP1, OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, X-Ray, council12. Ejecutar una tarjeta de control por paso. No dump de checklist. No rewrite origen.
metadata:
  type: workflow
  version: "1.0.0"
  status: CONTROL
  sibling: wordflow-code-deploy-router
  repo: maxbry123-commits/agentes
---

# Wordflow Paso Control

Skill de CONTROL. Cada PASO es una tarjeta ejecutable. INPUT BLOCK vive en `references/INPUT-BLOCK.md`. Council vive en `references/COUNCIL-12.md`. Mapa de fuentes en `references/SOURCE-MAP.md`.

Al activar este skill no listes requisitos. Ejecuta la tarjeta del PASO en curso.

## Arranque

1. Leer `references/INPUT-BLOCK.md` linea a linea. Marcar cada item UNCHECKED.
2. Leer `references/COUNCIL-12.md`. Aplicar 12 goals in antes de escribir.
3. Leer `references/SOURCE-MAP.md`. Si un path fuente no existe, STOP y reportar gap. No inventar.
4. Identificar PASO en curso (1..8) y salida (OUT1|OUT2|OUT3).
5. Ejecutar SOLO esa tarjeta. Emitir EVIDENCE. No avanzar con gate rojo.
6. LLM nunca imprime PASS. PASS solo si el gate de evidencia sale 0.

## Tarjeta comun

Toda tarjeta usa este contrato.

```
IN     paths y secrets que debes leer
DO     acciones en orden
FORBID acciones prohibidas
GATE   predicado medible
OUT    artefactos
NEXT   unico sucesor legal
```

Token solo por nombre de env. Nunca pegar ghp. Alias legales Maxbry_123_tokens EXTERNAL_GH_B_TOKEN EXTERNAL_GH_C_TOKEN HF_TOKEN TARGET_REPO_TOKEN.

Runtime generado = Python o YAML. JSON solo como ficha ya registrada.

## PASO 1 — Download Action

```
IN     skill research-download-chain
       assets FORENSIC-PASS yml + py (blob lock)
       lista REPOS fija
DO     disparar workflow research-download-chain-final.yml
       python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
FORBID reescribir packer, cambiar SPLIT_TARGET MAX_ZIP, add/remove slugs
GATE   MANIFEST count COMPLETE == len(REPOS)
       zip <= 17000000
       unzip -tq == 0
OUT    Download code/archivos/{slug}_{part}.zip
       RESEARCH_DOWNLOAD_MANIFEST.jsonl
NEXT   PASO 2
```

## PASO 2 — Bandeja Download N

```
IN     tarea_en_curso N in {1,2,3}
       zips de PASO 1
DO     mkdir -p "Download code/Download N"
       elegir OP1 o OP2
FORBID mezclar OP1 y OP2 en el mismo N sin evidencia
GATE   carpeta N existe
OUT    Download code/Download N/
NEXT   OP1 o OP2 luego cruzado
```

### OP1 parte del code

```
DO     seleccionar paths
       extraer SOLO esos paths
       COPY a Download code/Download N/<mapped>
FORBID reescribir bytes origen
GATE   cada path pedido existe en dest
NEXT   verificacion cruzada
```

### OP2 repo o agente completo

```
DO     crear raiz nueva en main del dest
       o fork y cablear
       COPY tree completo
FORBID dest no declarado
GATE   tree dest cubre tree fuente
NEXT   verificacion cruzada
```

### Cruzado fuente

```
DO     comparar repo fuente vs dest
GATE   MISSING=0 EXTRA_inesperado=0 SHA_MISMATCH=0
OUT    evidencia lista archivos + sha
NEXT   PASO 3 si OP1; PASO 4 si OP2 ya en dest
```

## PASO 3 — Extract COPY + Fables

```
IN     METODO_ZIP_COPY_DETERMINISTA
       GUIA-DESPLIEGUE-ZIP-UNIVERSAL
       PIPELINE/07 Enchufe Universal = Fables
       GUIA_REGISTRO_PLUGINS
       UOOS parte 1 y parte 2
       ficha de conexion
DO     unzip -t
       unzip -q a .staging/<slug>
       filtrar __MACOSX .DS_Store path-traversal
       COPY a raiz de vida del archivo
       sha256 src == sha256 dst
       registrar plugin I/O en cada archivo reutilizable
         plugin_id contrato inputs outputs extension_point estado
       si payload JSON o prompt -> emitir .py EXTRACT_LITERAL
       si reglas o skill -> .yaml
       repetir mismo metodo en el resto de archivos
FORBID editar origen, auto-fix, regenerar, tocar archivo ya registrado
GATE   sha match AND plugin I/O presente AND UOOS leido
OUT    copia en raiz destino + registro plugin
NEXT   PASO 4
```

## PASO 4 — GitHub Action copy queue

```
IN     owner/repo dest
       secret dest (no GITHUB_TOKEN del source)
DO     checkout source path=source
       checkout dest path=target token=env dest
       construir QUEUE exacta o queue/files.txt
       para cada FILE test -f source/$FILE
       cp source/$FILE target/$MAPPED
       map organico
         README pyproject -> raiz
         app code -> src/
         config -> config/
         tools -> scripts/
         tests -> tests/
       un git add, un commit, un push
FORBID force-push, llenar la raiz, usar token source contra dest
GATE   cada FILE de QUEUE existe en dest mapeado
OUT    commit dest
NEXT   PASO 5
```

## PASO 5 — Estado por nombre + write atomico

```
IN     Desplegar/Desplegar N lote
DO     analizar arquitectura de cada archivo
       marcar estado SOLO en el nombre
         archivo.yaml         ORIGINAL PROTEGIDO pendiente
         process_archivo.yaml copia en proceso
         done_archivo.yaml    auditado
       si hay que reescribir
         READ original
         SHA256
         trabajar TEMP
         DIFF + syntax
         fail -> conservar original
         ok -> rename atomico
FORBID editar bytes del original para marcar estado
       usar emoji como unica seguridad
GATE   original intacto OR (sha leida == sha pre-write AND syntax ok)
OUT    lote nombrado + temp limpio
NEXT   PASO 6
```

## PASO 6 — Deploy determinista

```
IN     Desplegar/Desplegar 1
       Desplegar 2 lote runtime
       PIPELINE/08 apply_push + determinista
       Wordflow Code/code_path_runner.py
DO     leer runner no editarlo
       cablear deploy al final del code path
         reception.convert -> goals -> planner -> code_path_runner
         -> loop_bridge -> evidence -> DEPLOY
       DRY_RUN default
       REAL solo si GITHUB_DEPLOY_REAL=1
FORBID JSON como runtime
GATE   runner termina en DEPLOY
OUT    ruta deploy activa
NEXT   PASO 7
```

## PASO 7 — Estandares dentro del prompt code

```
IN     prompt de code del lote Desplegar
       PIPELINE ADVANCED_ENGINEERING_STANDARD
DO     copiar estandares como REGLA del runtime
       EXTRACT_LITERAL gana sobre mejorar
FORBID reescribir estandar desde cero
GATE   prompt carga el estandar
OUT    reglas inyectadas
NEXT   PASO 8
```

## PASO 8 — Router A/B/C + 3 salidas

```
IN     external_accounts.yaml
       env Maxbry_123_tokens cuenta A y repos Wordflow
       env EXTERNAL_GH_B_TOKEN cuenta B abc1tienda-web
       env EXTERNAL_GH_C_TOKEN cuenta C HOLD
DO     registrar SOURCE read, WORK process, DEST write
       cable A = arquitectura Wordflow Code
       cable B = apply_push
       elegir OUT
         OUT1 chat UOOS parte1+parte2 .py o .yaml (json solo ficha)
         OUT2 owner/repo desde docs o preguntar; crear repo si falta
         OUT3 raiz organizada cuenta A + evidence
       X-Ray inbound docs
       MD -> code EXTRACT_LITERAL PIPELINE/57
       council 12 goals in -> council -> 12 goals out
FORBID write a C mientras owner=HOLD
       deploy sin council
GATE   registry completo AND OUT elegido AND X-Ray corrio
OUT    push o chat o evidence
NEXT   copiar este skill a destinos Tarea 3 solo despues de evidencia
```

## Destinos Tarea 3 (despues de evidencia)

```
canonical  skills/wordflow-paso-control/
copia      Metodo de trabajo/wordflow-paso-control/
copia      Download code/wordflow-paso-control/
copia      Desplegar/wordflow-paso-control/
copia      Refactoria/wordflow-paso-control/
parche     Wordflow Code/Readme/Readme1/  cable only
```

## STOP

path fuente ausente, token en claro, packer reescrito, SHA mismatch, plugin I/O ausente, OUT2-C sin owner, council sin 12 goals out.
