# CABLE Desplegar 1 -> Wordflow Code deploy

No reescribe hot path. Plugin/cable only.

## Sources (no copiar body aqui)
- https://github.com/maxbry123-commits/agentes/tree/main/Desplegar/Desplegar%202
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/07_ENCHUFE_UNIVERSAL_v2.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/08_DESPLIEGUE_DETERMINISTA_v2.md
- https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/08_DESPLIEGUE_APPLY_PUSH.md
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/github_deploy/apply_push.py
- https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py

## Tokens (solo refs)
- env:Maxbry_123_tokens  cuenta A
- env:EXTERNAL_GH_B_TOKEN  cuenta B abc1tienda-web
- env:EXTERNAL_GH_C_TOKEN  cuenta C HOLD owner
- env:HF_TOKEN

Secrets UI https://github.com/maxbry123-commits/agentes/settings/secrets/actions/new

## Salidas
OUT1 chat UOOS. OUT2 dest repo (create si falta). OUT3 raiz A + evidence.
REAL = GITHUB_DEPLOY_REAL=1.
