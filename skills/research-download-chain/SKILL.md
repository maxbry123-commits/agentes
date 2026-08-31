---
name: research-download-chain
description: 3 metodos GHA. Copiar. Descargar+extraer. Mover.
metadata:
  type: workflow
  version: "1.9.1"
---

# 3 instrucciones / 3 metodos / todo GHA

## 1. Copiar archivos

YAML:
`skills/research-download-chain/gha-copy-files.yml`

`checkout@v4` + `cp -a`. No Python. No LFS.

## 2. Descargar y extraer repos

No escribir packer. Usar el lock que ya existia.

YAML:
`skills/research-download-chain/assets/FORENSIC-PASS-research-download-chain-final.yml`

PY:
`skills/research-download-chain/assets/FORENSIC-PASS-research_download_chain.py`

GHA copia esos 2 files a:
- `.github/workflows/research-download-chain-final.yml`
- `scripts/research_download_chain.py`

Luego editar solo lista origen + destino argv. Dispatch el workflow vivo.

## 3. Mover archivo, lote o raiz

YAML:
`skills/research-download-chain/gha-move-files.yml`

Mismo repo: `cp -a` / `git mv` + push `main`.
Otro repo: checkout dest `repository` + `secrets.GH_PAT` + `cp -a` + push dest `main`.
