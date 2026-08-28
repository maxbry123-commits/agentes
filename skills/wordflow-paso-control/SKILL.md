---
name: wordflow-paso-control
description: Control YAML-first PASO 0-8 download-zip-copy-plugin-deploy. Trigger on Download code, Desplegar N, Refactoria source/new, OP1 OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, X-Ray, DAG RULES.yaml. Ancla assets workflow + extract. No omitir nodos. No rewrite origen.
metadata:
  type: workflow
  version: "1.2.0"
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
- Cmd download `python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'`

No reescribir packer. Lista 01-20 lock en skill research-download-chain.

## Extract zip (sistema)

Regla completa en `references/RULES.yaml` clave `extract_zip`.

```
unzip -t ZIP
unzip -q ZIP -d .staging/{slug}
filtrar __MACOSX .DS_Store path-traversal
cp -a src live_root   # COPY no rewrite
sha256 src == sha256 dst
plugin I/O
JSON|prompt -> .py
reglas|skill -> .yaml
```

Guia `docs/METODO_ZIP_COPY_DETERMINISTA.md` esta 404 en agentes. Hasta que exista, esta seccion + RULES.yaml son la guia. No inventar otro packer.

## DAG

Nodos y edges solo en `references/RULES.yaml` `dag:`. Texto aqui es comentario. Ejecutar en orden de edges. Skip prohibido.

## PASO compacto (detalle en YAML)

```
p0 audit 3 repos
p1 Action download 20 repos
p2 mkdir Download code + Download N
op1 parte -> Download N
op2 tree|fork -> DEST_ROOT
cross SHA
p3 extract+Fables+UOOS
p4 batch-copy yml + plugin I/O
p5 estado nombre + atomic write
p6 deploy tail Wordflow Code
p7 copiar estandares al prompt
p8 registry A/B/C + 2 cables
xray EXTRACT_LITERAL
council 12 in/out
out1 chat UOOS
out2 dest create+push
out3 raiz A organizada
```

## Token

Solo env. `Maxbry_123_tokens` `EXTERNAL_GH_B_TOKEN` `EXTERNAL_GH_C_TOKEN`. C=HOLD.

## Copias cableadas

Ver `references/RULES.yaml` `cables:`.

## STOP

YAML ancla ausente, nodo saltado, token en claro, SHA fail, plugin ausente, source/ editado, packer reescrito, C HOLD write, validate-skill FAIL.
