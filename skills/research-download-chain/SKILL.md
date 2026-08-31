---
name: research-download-chain
description: 3 metodos GHA. Copiar. Descargar+extraer. Mover.
metadata:
  type: workflow
  version: "1.9.0"
---

# 3 instrucciones / 3 metodos / todo GHA

## 1. Copiar archivos

Usar este YAML:
`skills/research-download-chain/gha-copy-files.yml`

Hace `checkout@v4` + `cp -a` de los files que indiques. No Python. No LFS.

## 2. Descargar y extraer repos

No escribir packer.

1. GHA copia fiel el YAML ejemplo:
   `skills/research-download-chain/gha-download-extract.yml`
   a `.github/workflows/research-download-chain-final.yml`
2. GHA copia fiel el PY lock:
   `skills/research-download-chain/assets/FORENSIC-PASS-research_download_chain.py`
   a `scripts/research_download_chain.py`
3. Editar solo: lista origen en el PY + destino zip/extract en el YAML (`DEST` / `WORK`).
4. Dispatch el workflow vivo.

Sin nombres de repo origen en este skill. Origen = lista que se edita despues de copiar.

## 3. Mover archivo, lote o raiz

Usar este YAML:
`skills/research-download-chain/gha-move-files.yml`

GHA copia ese YAML a `.github/workflows/` y lo despacha.
Mismo repo: `cp -a` / `git mv` + push `main`.
Otro repo: segundo checkout `repository` + `secrets.GH_PAT` + `cp -a` + push dest `main`.
