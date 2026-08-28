---
name: wordflow-code-deploy-router
description: Cablea download-chain, Download code, Refactoria, Desplegar y Wordflow Code. Trigger on Maxbry_123_tokens, UOOS salida, apply-push, X-Ray docs-to-code, council12, Desplegar N. No rewrite source. Copy+hash only.
metadata:
  type: workflow
  version: "0.2.0-tarea2"
  status: SANDBOX_TAREA2_GAPS_LOCKED
  repo: maxbry123-commits/agentes
---

# Wordflow Code Deploy Router

## GAP LOCK (Tarea 2)

1. Desplegar 1 = inbox PLAN_01 + cable. Docs runtime = Desplegar 2 + PIPELINE/07 + PIPELINE/08 + UOOS. No duplicar lote 2.
2. Download 1 = tarea en curso. Download 2/3 = inbox vacio listo. Zips = Download code/archivos.
3. Maxbry_123_tokens = secret A umbrella. Check workflow WARN si falta. No PAT en repo.
4. Cuenta C owner = HOLD. No inventar username. Token ref env:EXTERNAL_GH_C_TOKEN listo.
5. Fables = alias de Enchufe Universal v2 + GUIA_REGISTRO_PLUGINS. Path Fables no existe.
6. OUT3 LOCK = cuenta A raiz organizada + evidence.json. HF no es OUT3 (usa HF_TOKEN aparte).

## INPUT BLOCK

Leer references/MINI-PROMPT-TAREA2.md (solo enlaces). Ejecutar en orden P1 download -> P2 Download N -> P3 extract COPY+SHA -> P4 plugin I/O -> P5 X-Ray+council12 -> P6 code_path_runner -> P7 DEPLOY TAIL OUT1|OUT2|OUT3.

## Cables

hot path https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py
deploy https://github.com/maxbry123-commits/agentes/blob/main/extensions/github_deploy/apply_push.py
accounts https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/connectors/external_accounts.yaml
download skill https://github.com/maxbry123-commits/agentes/tree/main/skills/research-download-chain

## Token

secrets new https://github.com/maxbry123-commits/agentes/settings/secrets/actions/new
Name Maxbry_123_tokens. B=EXTERNAL_GH_B_TOKEN C=EXTERNAL_GH_C_TOKEN. Nunca ghp_ en chat.

## 3 salidas

OUT1 chat UOOS py/yaml. OUT2 dest account+repo (create_repo si falta). OUT3 A structured root + evidence. REAL solo GITHUB_DEPLOY_REAL=1.

## Prohibido

Reescribir packer. Editar componente registrado. Force-push. Inventar owner C. Declarar PASS verbal.
