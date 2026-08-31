---
name: research-download-chain
description: 3 metodos GHA. Copiar. Descargar+extraer. Mover. Group unico.
metadata:
  type: workflow
  version: "1.9.2"
---

# 3 instrucciones / 3 metodos / todo GHA

## 1. Copiar archivos

YAML: `skills/research-download-chain/gha-copy-files.yml`
`checkout@v4` + `cp -a`. No Python. No LFS.

## 2. Descargar y extraer repos

No escribir packer. Lock:
- `skills/research-download-chain/assets/FORENSIC-PASS-research-download-chain-final.yml`
- `skills/research-download-chain/assets/FORENSIC-PASS-research_download_chain.py`

GHA copia a `.github/workflows/` + `scripts/`. Editar solo lista + destino argv.

`concurrency.group` SIEMPRE el mismo string:
`research-download-chain-final`

Ese nombre es el turno, no el destino. En un mismo repo, todos los YAML usan ese group: uno corre, el otro espera. Entre repos distintos el group no cruza.

## 3. Mover archivo, lote o raiz

YAML: `skills/research-download-chain/gha-move-files.yml`
Mismo repo: `cp -a` / `git mv`. Otro repo: `secrets.GH_PAT` + `cp -a`.
Mismo `concurrency.group: research-download-chain-final`.
