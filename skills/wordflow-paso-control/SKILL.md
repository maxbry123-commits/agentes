---
name: wordflow-paso-control
description: Control YAML-first PASO 0-8 download-zip-copy-plugin-deploy. Trigger on Download code, Desplegar N, Refactoria source/new, OP1 OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, X-Ray, DAG RULES.yaml. Ancla extract al lado del zip, reconstruct multi-parte, X-Ray source_commit, workflow unico S1-S12. No auditar fragmentos. No rewrite packer.
metadata:
  type: workflow
  version: "1.3.0"
  status: CONTROL
  ancla: references/RULES.yaml
  repo: maxbry123-commits/agentes
---

# Wordflow Paso Control

## Overview

Ancla = `references/RULES.yaml`. Si SKILL.md y YAML discrepan, gana el YAML. Actions reales viven en `assets/`. No omitir nodos del DAG (`omit_steps: false`).

## Arranque

1. Leer `references/RULES.yaml` completo.
2. Leer `references/INPUT-BLOCK.md`.
3. Validar skill. Correr `scripts/check-tarjeta.sh`.
4. Ejecutar un nodo del DAG. Emitir evidence YAML.
5. LLM no imprime PASS.

## Tres raices (que hace cada una)

### Download code

Inbox de codigo bajado. `archivos/` = zips del Action. `Download N/` = bandeja de la tarea en curso. Aqui se extrae (OP1 parte / OP2 tree). No se refactoriza. No se despliega.

### Desplegar

Inbox de lote NUEVO del plan N. El Director sube docs/code a `Desplegar/Desplegar N/`. Runtime ya existente tambien en `Desplegar/Desplegar 2/`. Aqui se marca estado, se inyectan estandares, se cablea el tail deploy. No se edita origen in-place.

### Refactoria

Sitio de la version VIEJA. Copia a `source/` (intocable). Escribe `new/`. Cruzado x3. Luego integra al path canonico. No borrar viejo sin Director.

Cable plan: `Plan X-N -> Desplegar/Desplegar N -> Refactoria/refactoria-plan-x-N`.

## Actions dentro del skill

- Download lock `assets/research-download-chain-final.yml` blob `5950933bcf567a34e197e96c59e845451124eb35`
- Copy queue `assets/batch-copy-root-files.yml`
- Extract `assets/extract-downloaded-zips.yml`
- Un job S1-S12 `assets/download-extract-xray.yml`
- Cmd download `python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'`

No reescribir packer. Lista 01-20 lock en skill research-download-chain.

## Extract zip (misma raiz que el zip)

Destino = carpeta hermana del ZIP, reconstruida por slug.

```
Download code/archivos/SearchOS_0001.zip
Download code/archivos/SearchOS_0002.zip
        -> Download code/archivos/SearchOS/
```

No extraer ni auditar cada parte por separado. Ordenar `*_NNNN.zip`, unzip -tq, unzip -q todas las partes en UN dest. Script `scripts/extract_reconstruct.sh`.

X-Ray compara el arbol reconstruido contra `source_commit` del MANIFEST.jsonl, no contra main. Script `scripts/xray_crosscheck.py`. unzip extrae. Python hashea.

Cadena S1..S12 en `references/RULES.yaml` `extract_zip.chain`. Skip prohibido.

## DAG

Nodos y edges solo en `references/RULES.yaml` `dag:`. Skip prohibido.

## Token

Solo env. `Maxbry_123_tokens` `EXTERNAL_GH_B_TOKEN` `EXTERNAL_GH_C_TOKEN`. C=HOLD.

## STOP

YAML ancla ausente, nodo saltado, token en claro, SHA fail, plugin ausente, source/ editado, packer reescrito, auditar fragmento `_NNNN`, C HOLD write, validate-skill FAIL.
