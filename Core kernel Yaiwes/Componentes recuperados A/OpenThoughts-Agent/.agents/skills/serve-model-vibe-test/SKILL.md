---
name: serve-model-vibe-test
description: Stand up a PUBLIC, shareable inference endpoint for an HF/gs model on an Iris TPU so people on the internet can vibe-test it in a browser or via an OpenAI-compatible API. Use when asked to "serve a model for testing", "throw up a public endpoint", "let people play with model X", or to demo a checkpoint. Combines marin-serve (marin#6556) + a Pinggy tunnel from our endpoint bank.
---

# serve-model-vibe-test

Spin up a **public** endpoint for a HuggingFace repo or `gs://` checkpoint. `marin-serve` runs vLLM on a
single-host Iris TPU slice behind the controller proxy; a Pinggy tunnel makes its proxied port public at
`https://<id>.a.pinggy.link/proxy/serve.<ep>/`, with a dashboard and OpenAI-compatible API.

`scripts/inference/serve_public.py` wraps `marin-serve`, `hpc.pinggy_utils.PinggyTunnel`, and the Pinggy bank.

## ⚠️ Security — read first
The public URL is **unauthenticated**. Use it only for throwaway vibe testing; keep `--timeout-hours` short,
use an unused Pinggy pair, and tear it down when done.

## Prerequisites
- `marin-serve` available (marin#6556). `serve_public.py` invokes
  `~/Documents/marin/.venv/bin/python -m marin.inference.quick_serve_cli` by default. Override with
  `--marin-serve-bin` or `MARIN_SERVE_BIN`.
- **Run from the marin repo root (`~/Documents/marin`), not from this repo.** marin-serve bundles
  `Path.cwd()` as the worker workspace (`quick_serve_cli.py:227`) and the worker runs
  `uv sync --all-packages --extra tpu --extra vllm` against it. Only the marin workspace defines the
  `tpu`/`vllm` extras (on `marin-core`); any other CWD → `Extra 'tpu' is not defined in any project's
  'optional-dependencies' table` and the job dies before vLLM starts. `serve_public.py` resolves its
  own repo root via `parents[2]` for the `hpc` import, so invoke it by **absolute path** from the marin CWD.
- Iris controller access (the laptop's step-ca/GCP creds — same as `iris` CLI).
- `$DC_AGENT_SECRET_ENV` sourced (Pinggy uses your `~/.ssh` identity; SSH to `pro.pinggy.io:443`).
- Pinggy bank at `~/Documents/notes/ot-agent/pinggy_bank.md` (override `--pinggy-bank` / `PINGGY_BANK`).
- **Single-host TPU slices only** (`v6e-8`, `v6e-4`, `v5litepod-8`, …); multi-host is rejected.

## Pick an unused Pinggy pair
The bank has 10 pairs. Before launching, pick one that isn't already serving — a quick
probe (a free pair returns a Pinggy "tunnel not found"/503 or connection error; an
in-use one returns your model):
```bash
for i in 1 2 3; do u=$(sed -n "/## Pair $i$/,/pinggy.link/p" ~/Documents/notes/ot-agent/pinggy_bank.md | grep pinggy.link); \
  echo "pair $i: $u -> $(curl -s -o /dev/null -w '%{http_code}' --max-time 6 https://$u/ || echo down)"; done
```
Use a pair that shows `down`/`502`/`503` (free). Pass it as `--pair N`.

## Launch (the one-liner)
```bash
cd ~/Documents/marin                               # MUST be the marin repo — see Prerequisites
set -a; source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"; set +a
python -u ~/Documents/OpenThoughts-Agent/scripts/inference/serve_public.py <MODEL> --tpu <SLICE> [--region <R>] \
    [--chat-template <FILE-or-URL>] --pair <N> --timeout-hours 6
```
It launches marin-serve, waits for `READY — dashboard: http://127.0.0.1:<port>/proxy/serve.<ep>/`, opens the
Pinggy tunnel, and prints:
```
  dashboard : https://<id>.a.pinggy.link/proxy/serve.<ep>/
  OpenAI    : https://<id>.a.pinggy.link/proxy/serve.<ep>/v1
```
Keep the process running because it holds both tunnels. For unattended operation, use `tmux`, not
`nohup setsid …` on macOS:
```bash
tmux new-session -d -s serve-public \
  "source \"${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV first}\" && cd ~/Documents/marin && \
   python -u ~/Documents/OpenThoughts-Agent/scripts/inference/serve_public.py <MODEL> ... 2>&1 | tee /tmp/serve_public.log"
# then poll /tmp/serve_public.log (or `tmux attach -t serve-public`) for the "OpenAI :" line
```

## Worked example — the Delphi 9.7B SFT canary (marin#6545)
This is the reference model: `laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft`.
It needs its **own chat template** (the repo ships a plain Llama-3 one); use `delphi_v0.jinja2`.
marin-serve auto-derives the 4k context (malformed RoPE) and TP=2 (30 heads on a 4-chip slice).
```bash
# run from ~/Documents/marin (the bundled workspace); script is invoked by absolute path
cd ~/Documents/marin && source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV first}"
python -u ~/Documents/OpenThoughts-Agent/scripts/inference/serve_public.py \
    laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft \
    --tpu v6e-4 --region europe-west4 \
    --chat-template https://raw.githubusercontent.com/open-thoughts/OpenThoughts-Agent/ed4d6f483151f14d6d78cf732f04cd3c8ff5c606/chat_templates/delphi_v0.jinja2 \
    --pair 1 --timeout-hours 6
```
Verify once the public URL prints:
```bash
BASE=https://<id>.a.pinggy.link/proxy/serve.<ep>
# from the laptop you must force the real Pinggy edge IP (ISP DNS poisons *.a.pinggy.link); see Gotchas
curl "$BASE/v1/models"
curl "$BASE/v1/chat/completions" -H 'content-type: application/json' \
  -d '{"model":"laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft",
       "messages":[{"role":"user","content":"Give me a fun fact about otters."}]}'
```
(Base/midtrained checkpoints with no chat template auto-default the dashboard to completion mode — omit `--chat-template`.)

## Teardown
- Foreground: `Ctrl-C` (tears down the Pinggy tunnel and the marin-serve job it launched).
- Detached/other host: `iris job stop <job> --cluster marin` (the job name is in the log /
  `iris query`), then kill the `serve_public.py` PID. The slice also self-stops at `--timeout-hours`.

## Gotchas
- **Run from the marin repo or the build fails before vLLM starts.** `Path.cwd()` becomes the worker workspace;
  only marin defines the needed extras. Invoke `serve_public.py` by absolute path from `~/Documents/marin`.
- **Dead tunnel reported live (`ps` state `T`):** run `kill -CONT <ssh_pid> <loop_pid>`, then re-probe.
  `PinggyTunnel.start()` prevents this with detached stdin, `ssh -n`, and `setsid`; `serve_public.py` prints
  `LIVE ✓` only after a DNS-aware `/v1/models` HTTP 200 probe.
- **Cold compile**: first boot of a model can take tens of minutes; `--ready-timeout` (default 2700s) bounds the wait.
- **Don't use marin-serve `--no-wait`** for the public path — the local proxied port only exists while the launching process runs; `--no-wait` returns immediately and there's nothing to tunnel.
- **Pinggy pair collisions**: two jobs on the same pair clobber each other — always pick a free pair.
- **Single-host concurrency**: one slice = limited throughput; fine for a few testers, not a viral launch (that's inference-broker territory).
- The public URL carries the `/proxy/serve.<ep>/` base path (it's the controller proxy path), so the OpenAI base is `https://<id>.a.pinggy.link/proxy/serve.<ep>/v1`, not `/v1`.
- **Local DNS poisoning:** verify through the real edge with `dig @1.1.1.1` and `curl --resolve`, or use
  `1.1.1.1`/`8.8.8.8` DNS. See `.agents/projects/pinggy/pinggy.md`.
