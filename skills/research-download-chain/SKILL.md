---
name: research-download-chain
description: 3 instrucciones. GHA copia lock. AI edita lista+destino. GHA mueve raiz.
metadata:
  type: workflow
  version: "1.8.1"
---

# 3 instrucciones

## 1. Copiar archivo (cableo YAML copy)

Ejemplo lock:
- `skills/research-download-chain/assets/FORENSIC-PASS-research-download-chain-final.yml`
- `skills/research-download-chain/assets/FORENSIC-PASS-research_download_chain.py`

Destino vivo:
- `.github/workflows/research-download-chain-final.yml`
- `scripts/research_download_chain.py`

YAML: `skills/research-download-chain/gha-copy-skill-example.yml`  
GHA: `actions/checkout@v4` + `cp -a` + commit/push `main`. `lfs: false`.

## 2. No escribir packer

GHA copia el code exacto del lock. AI/agente solo edita `REPOS` y el destino argv del PY. Descarga y extraccion = ese PY copiado. No packer nuevo.

## 3. Mover archivo o raiz (cableo YAML move)

YAML: `skills/research-download-chain/gha-move-root-or-files.yml`  
Mismo repo: un checkout + `cp -a`/`git mv` + push `main`.  
Otro repo: checkout origen + checkout destino `repository` + `token: ${{ secrets.GH_PAT }}` + `cp -a` + push dest `main`.
