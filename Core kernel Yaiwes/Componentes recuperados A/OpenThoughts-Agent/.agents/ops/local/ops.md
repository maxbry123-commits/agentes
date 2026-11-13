# Local (this Mac) — ops

Control machine for launches, uploads, Supabase queries, code edits, and analysis; clusters do GPU work. Use commit → push → `git pull` on clusters (see `.agents/projects/marinskyrl/marinskyrl.md`).

## System and disk

- macOS 26.5.1 (25F80), Apple M4 Max (`Mac16,5`), arm64; 14 CPU cores (10P + 4E), 36 GB unified RAM.
- No local NVIDIA GPU: CUDA/training/vLLM runs on clusters; MPS is only for tiny smoke tests.
- 926 GB APFS. Check `df -h /System/Volumes/Data` `Avail`; do not compute free space from sealed `/` `Size`.
- Prunable: `~/Documents/experiments/traces` (per-experiment only after HF upload), `~/.cache/huggingface` (safe `rm -rf`), `~/Library/Caches`. Prune HF cache toward ~50 GB free. Do not pull large weights or traces locally.

## Tools and environments

- Homebrew 5.1.14 at `/opt/homebrew`; load-bearing tools: `gh`, `git-lfs`, `step`, `gcloud-cli`, `kubernetes-cli`, `helm`, `k3d`, `tectonic`, `coreutils`.
- conda 25.5.1 base: `/Users/benjaminfeuer/miniconda3` (Python 3.13.5, torch 2.8.0; do not train there).
- Canonical OT-Agent/Harbor/SkyRL env: `otagent` (Python 3.12.12, torch 2.9.0). Use:
  ```
  /Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
  ```
- Other envs: `harbor`, `llama-factory`, `marin`, `oumi`, `ajudge`, `marvis`, `abb`, `openreview`, `sweagent`, `tokviz-rt`. Use `otagent` unless task-specific; see `.agents/projects/ajudge/` for `ajudge`.
- Syntax/lint: use IDE MCP `mcp__ide__getDiagnostics`, not `python -m py_compile`/`flake8`.

## Local codebases (`/Users/benjaminfeuer/Documents/`)

All are editable-installed in their relevant env. Edit locally, commit, push, then `git pull` on cluster; never patch clusters.

- `OpenThoughts-Agent/`: launcher/orchestration; `penfever/working`, `open-thoughts/OpenThoughts-Agent`; `.agents/projects/ot-agent/`.
- `harbor/`: agent framework; `main` (`penfever/working` retired); `marin` is `marin-community/harbor`; `.agents/projects/harbor/`.
- `MarinSkyRL/`: RL framework; `penfever/working` = `marin-community/MarinSkyRL`; `.agents/projects/marinskyrl/`.
- `vllm/`: `mlfoundations/vllm` fork on `feuer/dcp-gqa-lse-fix`; cluster builds use committed fork/SIF, never rsync or hand-patch; some envs use vanilla vLLM. `.agents/projects/vllm/`.

## Other local paths and secrets

Use absolute `/Users/benjaminfeuer/Documents/` paths; bare `agent_logs/`, `experiments/`, and `notes/` resolve against the checkout.

- `/Users/benjaminfeuer/Documents/agent_logs/`: dated `YYYY-MM-DD_<topic>.md` investigation logs; use after diagnosing genuine FAILED jobs.
- `experiments/`: per-series trackers; `.agents/ops/experiments/ops.md`.
- `notes/`: knowledge base; `.agents/` mirrors some contents.
- Secrets: `.agents/secret.md` (untracked/gitignored) names paths, inventory, and loading. Set `$DC_AGENT_SECRET_ENV`, then:
  ```bash
  set -a; source "$DC_AGENT_SECRET_ENV"; set +a
  ```
- Credentials: `HF_TOKEN`; `DAYTONA_API_KEY`, `DAYTONA_B_KEY`, `DAYTONA_DATA_API_KEY`, `DAYTONA_RL_API_KEY`; `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`; `WANDB_API_KEY`; `OPENAI_API_KEY`; `LAION_ENDPOINT`, `LAION_BUCKET_NAME`, `LAION_ACCESS_KEY`, `LAION_SECRET_KEY`; `MARIN_HMAC_ACCESS_ID`, `MARIN_HMAC_SECRET`, `MARIN_PREFIX`; `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`; `DOCKER_USER_ID`, `DOCKER_TOKEN`; `PINGGY_API_KEY`, `PINGGY_IDENTITY_FILE`; `MODAL_PROFILE`; `TOGETHER_API_KEY`; `VAST_API_KEY`; `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`; `SSH_KEY`. Reference values by name only.

## SSH aliases

`Jupiter`, `Leonardo`, `perlmutter`, `torch`, `TACCVista`, `ALCFPolaris`, `OLCFFrontier`, `TUDCapella`, `EmpireAI_Alpha1`, `OumiLambdaSLURM`, `OracleCloud`, `hegde-lambda-{1,2}`. Active cron scope: Jupiter + Leonardo. Access/preambles: `.agents/ops/<cluster>/`; Leonardo `step ssh certificate` expires ~12h; `.agents/ops/leonardo/ops.md`.
