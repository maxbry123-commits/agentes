---
name: wordflow-code-deploy-router
description: Paso a paso determinista download-zip-copy-plugin-xray-council-deploy. Trigger on Download N, Desplegar N, OUT1 OUT2 OUT3, Maxbry_123_tokens, extract COPY+SHA. No rewrite. No from-scratch packer.
metadata:
  type: workflow
  version: "0.3.0-pasos"
  status: EDIT_UNTIL_WIRED
  repo: maxbry123-commits/agentes
---

# Wordflow Code Deploy Router — PASOS

Contrato para AI. Ejecutar en orden. STOP si un gate falla. LLM no declara PASS.

## PREFLIGHT

```
READ skill
READ METODO_ZIP_COPY_DETERMINISTA
READ GUIA-DESPLIEGUE-ZIP-UNIVERSAL
READ PIPELINE/07 enchufe
READ PIPELINE/08 apply_push + determinista
READ PIPELINE/57 EXTRACT_LITERAL
READ GUIA_REGISTRO_PLUGINS
READ external_accounts.yaml
HASH assets download-chain == lock blobs
TOKEN_REF only env:Maxbry_123_tokens | env:EXTERNAL_GH_B_TOKEN | env:EXTERNAL_GH_C_TOKEN | env:HF_TOKEN
IF raw ghp_ THEN FAIL
```

## P01 DOWNLOAD

```
INPUT  = REPOS[] orden fijo (skill research-download-chain)
ACTION = GitHub Actions research-download-chain-final.yml
CMD    = python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
GATE   = grep -c '"status": "COMPLETE"' MANIFEST == 20
         AND every zip size <= 17000000 AND unzip -tq == 0
SKIP   = slug already COMPLETE
FORBID = rewrite packer, change SPLIT_TARGET/MAX_ZIP, add/remove repos
```

## P02 BANDEJA

```
MKDIR "Download code"
MKDIR "Download code/Download N"   # N = tarea en curso 1|2|3
SRC  = Download code/archivos/{slug}_NNNN.zip
```

### OP1 PARTIAL

```
EXTRACT selected paths only
COPY -> Download code/Download N/<mapped_path>
DO NOT rewrite bytes
```

### OP2 FULL

```
IF software_completo OR agente_completo:
  CREATE root on dest main
    OR fork then cable
  COPY tree SRC -> DEST_ROOT
CROSSCHECK source_repo vs dest:
  MISSING|EXTRA|SHA_MISMATCH -> FAIL
```

## P03 EXTRACT + PLUGIN

```
unzip -t ZIP
unzip -q ZIP -d .staging/slug
FILTER __MACOSX .DS_Store path-traversal
FOR each file:
  sha256(src_bytes)
  COPY to live_root   # copy, never overwrite-edit origin
  sha256(dst) == sha256(src) else FAIL
PLUGIN I/O mandatory on every new reusable file
  plugin_id, contrato, inputs[], outputs[], estado
IF payload is JSON or prompt DSL -> emit .py EXTRACT_LITERAL
IF rules or skill contract -> .yaml
FORBID rewrite, auto-fix, regenerate
FABLES = alias Enchufe Universal v2 + registro plugins
```

## P04 ACTIONS COPY QUEUE

```
checkout source path=source
checkout dest   path=target  token=env:TARGET_ALIAS
# TARGET_ALIAS maps:
#   A -> env:Maxbry_123_tokens
#   B -> env:EXTERNAL_GH_B_TOKEN
#   C -> env:EXTERNAL_GH_C_TOKEN
BUILD queue/files.txt OR QUEUE=(exact names)
FOR file in QUEUE:
  test -f source/$file else EXIT 1
  cp source/$file target/$mapped
MAP by responsibility:
  *.py app     -> src/
  *config*     -> config/
  *script*     -> scripts/
  *test*       -> tests/
  README/pyproject stay root
git add && one commit && one push
NO force-push
GITHUB_TOKEN of source repo does not cross dest — use dest secret
```

## P05 STATE + ATOMIC WRITE

```
IN Desplegar/Desplegar N:
  ANALYZE architecture per file
NAME is state, content untouched:
  file.yaml        = PENDIENTE
  process_file.yaml = EN_PROCESO
  done_file.yaml    = AUDITADO
IF rewrite required:
  READ original
  SHA256 original
  WRITE temp
  VALIDATE syntax+diff
  IF fail KEEP original
  ELSE atomic rename temp -> new
  original stays READ-ONLY
```

## P06 DEPLOY ENGINE

```
TAIL of Wordflow Code after evidence:
  reception.convert -> goals -> planner -> code_path_runner
  -> loop_bridge -> evidence -> DEPLOY
RUNTIME = python + yaml only
JSON allowed only as ficha/contrato already registered
DRY_RUN default
REAL only if GITHUB_DEPLOY_REAL=1
```

## P07 STANDARDS

```
LOAD programming standards from Desplegar lote (Desplegar 2 docs + PIPELINE ADVANCED_ENGINEERING_STANDARD)
APPLY as rules to generated/extracted code
EXTRACT_LITERAL still wins over "improve"
```

## P08 ROUTER A/B/C

```
REGISTRY:
  SOURCE_*  read
  WORK_*    process
  DEST_*    write
ACCOUNT A owner=maxbry123-commits token=env:Maxbry_123_tokens
ACCOUNT B owner=abc1tienda-web     token=env:EXTERNAL_GH_B_TOKEN
ACCOUNT C owner=HOLD               token=env:EXTERNAL_GH_C_TOKEN
          # STOP OUT2-C until Director sets owner
IF dest_repo missing AND OUT2: remote_op create_repo then apply_push
```

## P09 THREE OUTPUTS

```
OUT1 = chat UOOS parte1+parte2 as .py or .yaml
OUT2 = dest owner/repo from docs or ask chat; create if missing
OUT3 = same account A structured root + evidence.json
```

## P10 XRAY + COUNCIL12

```
audit_forensic on inbound docs
MD -> code = EXTRACT_LITERAL (PIPELINE/57)
THEN council12:
  12 goals in -> council -> 12 goals out
NO council PASS -> NO deploy
```

## GATES

```
PASS only if EvidenceGate shell/tests exit 0
LLM never prints PASS
```
