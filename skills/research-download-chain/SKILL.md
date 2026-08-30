---
name: research-download-chain
description: Reproduce the exact GitHub Actions chain that downloaded 20 OS research and orchestration repos into Download code/archivos. Trigger on research-download-chain, FROMTED PASO 1 sources, 20 repos zip split, RESEARCH_DOWNLOAD_MANIFEST, or Wordflow download PASS run 33134420445. Lock to forensic blobs. Do not rewrite the packer.
metadata:
  type: workflow
  version: "1.0.0"
  pass_run_id: "33134420445"
  pass_job_id: "98731080894"
  pass_sha: "f53145e2f86f6f948c4697a06bf1f3b707a71d5b"
  workflow_blob: "5950933bcf567a34e197e96c59e845451124eb35"
  script_blob: "bfc7634f500f6ded03b296ddfebc6dac35c56462"
---

# Research Download Chain

## Overview

Skill de ejecución determinista del Wordflow PASS que materializó 20 repos OS en `Download code/archivos/`. Fuente de verdad = copias byte-identical en `assets/`. Este SKILL.md orquesta. Si hay divergencia, gana el source en `assets/`.

## INPUT BLOCK (leer literal)

1. Usar JSON playbook + enlaces GitHub Actions + code fuente + rutas.
2. Crear skill primero en sandbox.
3. Copiar al repo `maxbry123-commits/agentes`.
4. Método de trabajo va adjunto dentro del skill.
5. Confirmar archivo 100% y entregar enlace.

## Fuente de verdad LOCK

Leer siempre antes de ejecutar

- `assets/FORENSIC-PASS-research-download-chain-final.yml` (git blob `5950933bcf567a34e197e96c59e845451124eb35`)
- `assets/FORENSIC-PASS-research_download_chain.py` (git blob `bfc7634f500f6ded03b296ddfebc6dac35c56462`)
- `references/RESEARCH-DOWNLOAD-CHAIN-AI-PLAYBOOK.json`
- `references/METODO-DE-TRABAJO.md`

Preflight obligatorio. Calcular git-blob SHA1 = sha1 of `blob {len}\\0{bytes}` de ambos assets. Si no igualan los blobs del lock, STOP.

## Prueba GitHub Actions PASS

- Repo https://github.com/maxbry123-commits/agentes
- Workflow file `.github/workflows/research-download-chain-final.yml`
- Script `scripts/research_download_chain.py`
- SHA checkout PASS `f53145e2f86f6f948c4697a06bf1f3b707a71d5b`
- Run `33134420445` conclusion success
- Job `98731080894` conclusion success
- Job URL https://github.com/maxbry123-commits/agentes/actions/runs/33134420445/job/98731080894
- Run URL https://github.com/maxbry123-commits/agentes/actions/runs/33134420445
- Ventana UTC 2026-08-28T01:57:19Z to 2026-08-28T02:00:43Z
- Steps PASS. Checkout v4. Execute deterministic download chain. Final safety audit.

NO usar como source el YAML inline histórico ni HEAD `research-download-chain.yml` (checkout@v6 / group writer). Esos no son el job PASS.

## Rutas LOCK

- DEST = `Download code/archivos`
- WORK = `_work/research-download`
- SRC = `_work/research-download/src`
- PACK = `_work/research-download/pack`
- MANIFEST = `Download code/archivos/RESEARCH_DOWNLOAD_MANIFEST.jsonl`
- ZIP pattern = `{slug}_{part:04d}.zip`

## Constantes LOCK

- SPLIT_TARGET = 12000000
- MAX_ZIP = 17000000
- BATCH_LIMIT = 90 * 1024 * 1024
- CHUNK = 8 * 1024 * 1024
- batch_no inicial = 0
- checkout = actions/checkout@v4 fetch-depth 1
- concurrency group = `research-download-chain-final` cancel-in-progress false

## Ejecución (no reimplementar)

1. Depositar assets en rutas canónicas del repo si faltan.
2. Correr EXACTO

```bash
set -euo pipefail
python3 scripts/research_download_chain.py 'Download code/archivos' '_work/research-download'
```

3. El py hace el loop 01..20 en orden fijo. Skip si manifest tiene slug + status COMPLETE. Clone `--depth 1 --no-tags`. Strip `.git`. Stage. Chunk files mayores que CHUNK. `zip -q -r -9 -y`. Si zip mayor que SPLIT_TARGET usar `zipsplit -n 12000000`. Reject part mayor que MAX_ZIP. `unzip -tq`. Batch 90MiB luego commit/push.

4. Commit message template

`build(download): research queue batch {label} ({n} bytes)`

Labels `000`..`00N` y cierre `{batch_no:03d}-final`. Push = fetch origin main + rebase + push, retry 1..3, sleep attempt*2.

5. Audit YAML. PASS solo si todo true.

```bash
set -euo pipefail
test -f 'Download code/archivos/RESEARCH_DOWNLOAD_MANIFEST.jsonl'
count=$(grep -c '"status": "COMPLETE"' 'Download code/archivos/RESEARCH_DOWNLOAD_MANIFEST.jsonl' || true)
test "$count" -eq 20
find 'Download code/archivos' -type f -name '*.zip' -print0 | while IFS= read -r -d '' f; do
  size=$(stat -c '%s' "$f")
  test "$size" -le $((17*1000*1000))
  unzip -tq "$f"
done
echo 'AUDIT PASS: 20/20 repositories; all ZIP files valid and within safety limit.'
```

LLM nunca declara PASS. PASS = EvidenceGate de los tests de arriba.

## 20 repos LOCK (orden)

01 SearchOS https://github.com/antins-labs/SearchOS.git
02 SearXNG https://github.com/searxng/searxng.git
03 OpenDeepResearch https://github.com/langchain-ai/open_deep_research.git
04 GPT-Researcher https://github.com/assafelovic/gpt-researcher.git
05 STORM https://github.com/stanford-oval/storm.git
06 Shandu https://github.com/jolovicdev/shandu.git
07 Vane https://github.com/ItzCrazyKns/Vane.git
08 Haystack https://github.com/deepset-ai/haystack.git
09 Crawl4AI https://github.com/unclecode/crawl4ai.git
10 Perplexica https://github.com/cognitive-builder/Perplexica.git
11 Dagu https://github.com/dagucloud/dagu.git
12 Conductor https://github.com/conductor-oss/conductor.git
13 Temporal https://github.com/temporalio/temporal.git
14 Argo-Workflows https://github.com/argoproj/argo-workflows.git
15 Kestra https://github.com/kestra-io/kestra.git
16 LangGraph https://github.com/langchain-ai/langgraph.git
17 Hatchet https://github.com/hatchet-dev/hatchet.git
18 Windmill https://github.com/windmill-labs/windmill.git
19 Dagster https://github.com/dagster-io/dagster.git
20 Prefect https://github.com/PrefectHQ/prefect.git

## Prohibido

- Reescribir packer / partition binary-search
- ZIP_LIMIT único
- batch_no=1
- Añadir o quitar repos
- Cambiar DEST/WORK
- Paralelizar el loop
- Filtrar files del clone
- Declarar PASS sin audit shell exit 0

## Método

Aplicar `references/METODO-DE-TRABAJO.md` en cada salida. Sandbox-first. Input-checklist. Forensic closure. No from-scratch.

## NOTA ADDENDUM (no reescribe packer ni constantes LOCK)

Archivo >100MB en git push = GH001. El packer LOCK ya lo evita: si size>CHUNK (8MiB) parte a `nombre.chunks/nombre.part-NNNN`. En EXTRACT no recomponer el original. Dejar .chunks. Si un file extraído queda >CHUNK, aplicar la misma partición del packer antes de git add.

LFS en EXTRACT: el clone puede traer puntero `version https://git-lfs.github.com/spec/v1` + `.gitattributes filter=lfs`. Eso no está en el packer. Solución permitida (no es tercer paso de descarga): GIT_LFS_SKIP_SMUDGE=1 GIT_LFS_SKIP_PUSH=1; git lfs uninstall; borrar líneas filter=lfs del .gitattributes; push --no-verify. El puntero queda texto. Prohibido git lfs track / migrate / smudge.

## CHECKLIST PRE-RUN (comparar code vs skill antes de dispatch)

- [ ] Packer no reescrito. CHUNK=8MiB SPLIT_TARGET=12e6 MAX_ZIP=17e6 BATCH=90MiB.
- [ ] Paso 1 DEST = Download code/archivos. ZIP pattern slug_0001.zip.
- [ ] Paso 2 EXTRACT = raíz exacta. No recomponer files >CHUNK.
- [ ] YAML env GIT_LFS_SKIP_SMUDGE=1 y GIT_LFS_SKIP_PUSH=1.
- [ ] checkout lfs: false. git lfs uninstall en job.
- [ ] push --no-verify. No filter=lfs en .gitattributes que se commitea.
- [ ] Ningún file staged size>=100MiB (find -size +99M).
- [ ] Diff packer LOCK = vacío. Si no vacío STOP.
- [ ] Solo entonces workflow_dispatch.
