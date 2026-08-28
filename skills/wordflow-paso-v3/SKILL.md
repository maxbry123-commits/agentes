---
name: wordflow-paso-v3
description: Control v3 PASO 0-8 mas extract AGRUPADO. Partes {slug}_NNNN.zip van a {slug}/ no a {slug}_0001/. Trigger Download code, Desplegar N, Refactoria, OP1 OP2, OUT1 OUT2 OUT3, Maxbry_123_tokens, Fables, UOOS, X-Ray, council12. No edita skills viejos. Lock packer 5950933b bfc7634f.
metadata:
  type: workflow
  version: "3.0.0"
  status: REVIEW
  previous:
    - wordflow-paso-control
    - wordflow-paso-full
    - commit-1.1-3ff622fe
  repo: maxbry123-commits/agentes
---

# Wordflow Paso v3

Skill NUEVO. No edita `wordflow-paso-control` ni `wordflow-paso-full`. Cruzar `references/XRAY-AUDIT-3PASADAS.md` `references/INPUT-BLOCK.md` `references/RULES.yaml`.

## Overview

INPUT BLOCK 1-32 en references. Ancla YAML RULES.yaml. LLM no imprime PASS. validate-skill.sh primero.

## Extract AGRUPADO (corrige workflow per-part)

RECHAZADO:
```
Argo-Workflows_0001.zip -> Argo-Workflows_0001/
Argo-Workflows_0002.zip -> Argo-Workflows_0002/
```

OBLIGATORIO:
```
Argo-Workflows_0001.zip --+
Argo-Workflows_0002.zip --+--> Download code/archivos/Argo-Workflows/
```

Nucleo Director:
```
find ROOT -maxdepth 1 -name '*_0001.zip'
dest=$ROOT/$name
for zip in $ROOT/${name}_*.zip
  unzip -tq
  unzip -oq -d dest
flatten packer prefix $dest/$name -> $dest
```

Script `scripts/extract_reconstruct.sh`.

Cadena S1 QUEUE S2 DOWNLOAD-lock S3 ZIP-TEST S4 RECONSTRUCT S5 SOURCE_COMMIT S6 INVENTORY S7 MISSING/EXTRA S8 SIZE S9 SHA S10 XRAY S11 EVIDENCE S12 GATE.

Download = packer lock. No clone suelto del paste. X-Ray vs source_commit del MANIFEST. No main. unzip extrae. Python hashea `scripts/xray_crosscheck.py`.

PASS extract solo si 0 MISSING 0 EXTRA 0 CHANGED. LLM no declara PASS.

## Tres raices

Download code = zips + `{slug}/` + bandeja Download N.
Desplegar = lote nuevo Desplegar N. Runtime Desplegar 2.
Refactoria = source/ intocable + new/.

## PASO 0 fuentes
Auditar agentes TAREA-1 YAIWES. Guia zip 404 = gap listed. No inventar.

## PASO 1 download lock
yml `5950933bcf567a34e197e96c59e845451124eb35`
py `bfc7634f500f6ded03b296ddfebc6dac35c56462`
run PASS 33134420445 job 98731080894
cmd `python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'`
lista 01-20 SearchOS ... Prefect. No rewrite packer.

## PASO 1b reconstruct + xray
`bash scripts/extract_reconstruct.sh "Download code/archivos"`
`python3 scripts/xray_crosscheck.py "Download code/archivos" audit work/source`
Workflows `assets/extract-downloaded-zips.yml` `assets/download-extract-xray.yml`

## PASO 2 bandeja
mkdir Download code + Download N. OP1 subset COPY a N. OP2 tree|fork DEST_ROOT. Cruzado SHA.

## PASO 3 copy live + Fables
COPY no rewrite. plugin I/O. JSON|prompt -> .py. rules|skill -> .yaml. UOOS 1-2 + ficha antes.

## PASO 4 action copy queue
checkout source + dest token dest. cola. map src/config/scripts/tests. 1 commit 1 push.

## PASO 5 estado nombre
original / process_ / done_ / ♾️_ / ✅_. Atomic COPY HASH DIFF VALIDATE RENAME.

## PASO 6 deploy tail
reception -> goals -> planner -> runner -> loop_bridge -> evidence -> DEPLOY. DRY_RUN default.

## PASO 7 estandares
copiar ADVANCED_ENGINEERING_STANDARD al prompt. EXTRACT_LITERAL gana.

## PASO 8 router
A maxbry123-commits Maxbry_123_tokens
B abc1tienda-web EXTERNAL_GH_B_TOKEN
C HOLD
OUT1 chat UOOS py|yaml. OUT2 dest create+push. OUT3 raiz A.
X-Ray docs EXTRACT_LITERAL luego council12.

## Tarea 3 destinos
canonical skills/wordflow-paso-v3/
viejos skills/wordflow-paso-control y wordflow-paso-full NO BORRAR hasta Director
copias Metodo de trabajo / Download code / Desplegar / Refactoria
parche Wordflow Code/Readme/Readme1/CABLE-PASO-V3.md

## STOP
per-part extract, auditar _0001 solo, packer rewrite, token claro, C write, guia inventada, validate FAIL.
