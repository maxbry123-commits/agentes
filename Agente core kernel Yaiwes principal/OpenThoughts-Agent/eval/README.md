# eval/

Listener-driven evaluation pipeline for OpenThoughts-Agent. The core
loop: pick (model × dataset × scaffold), serve the model with vLLM
inside SLURM, run trials through Harbor + Daytona, upload results to
Supabase + HuggingFace.

## Quickstart

1. Pick or create a cluster config:

   ```bash
   cp eval/clusters/example.yaml ~/.local/eval-cluster.yaml
   $EDITOR ~/.local/eval-cluster.yaml          # fill in placeholders
   cp hpc/dotenv/example.env ~/.local/eval.env
   $EDITOR ~/.local/eval.env                   # fill in TODO secrets
   source ~/.local/eval.env
   ```

2. Fire a single-model dry-run to confirm the surface is wired up:

   ```bash
   echo "Qwen/Qwen3-32B" > /tmp/dry.txt
   python eval/unified_eval_listener.py \
     --cluster-config ~/.local/eval-cluster.yaml \
     --preset v2 --priority-file /tmp/dry.txt \
     --once --dry-run
   ```
   Per-model serve config now comes from the shared registry
   `eval/configs/model_configs.yaml` BY DEFAULT (the cluster yaml's
   `hardware_profile:` selects the per-cluster recipe; `name@profile` standalones
   express intrinsic per-cluster divergence). `--baseline-model-configs` is a
   deprecated optional override (emits a DeprecationWarning).

3. Read [`docs/EVAL_GUIDE.md`](../docs/EVAL_GUIDE.md) for full fire templates,
   the failure-modes catalog, and recovery procedures.

## Five firing categories

- **Cat 1 — Reg eval**: terminus-2 on `v2 / swebench / tb2`. Default
  preset, default harbor config, default agent.
- **Cat 2 — OOD presets**: `aider / bfcl / medagentbench / gaia /
  financeagent / swebench_full`. Same listener, different presets,
  `dcagent_eval_config_no_override.yaml`.
- **Cat 3 — Preferred-harness reproduction**: paper-author scaffolds
  (swe-agent / openhands / mini-swe-agent / aider) with installed-agent
  CLIs talking to the served model via Pinggy SSH tunnels. See
  [`docs/PREFERRED_HARNESS_REPRODUCTION.md`](../docs/PREFERRED_HARNESS_REPRODUCTION.md).
- **Cat 4 — Yaml flip-restore**: temporarily strip Pattern A/B/C
  parsers from a model's registry entry to fire it on terminus-2
  (Pattern D), then restore.
- **Cat 5 — Per-model serving config**: edit the shared registry
  `configs/model_configs.yaml` to add a new tp/dp,
  parser, chat-template, or extra_args entry for a model (a `name@<profile>`
  standalone / `variants:` block for per-cluster divergence).

## Layout

```
eval/
├── unified_eval_listener.py    # daemon / one-shot SLURM submitter
├── jupiter/eval_harbor.sbatch  # Jupiter (GH200) per-cluster sbatch: vLLM serve + harbor run + DB upload
├── leonardo/eval_harbor.sbatch # Leonardo (x86_64) per-cluster fork of the above
├── build_vllm_cmd.sh           # consumes EVAL_VLLM_* env from listener
├── check_progress.py           # progress + result dashboard
├── snapshot_download.py        # pre-download HF caches
├── configs/                    # model_configs.yaml registry (default) + scaffold harbor yamls
├── clusters/                   # one yaml per SLURM cluster
└── lists/                      # priority files (one HF model per line)
```

Reference docs (centralized under `/docs`):
[`docs/EVAL_GUIDE.md`](../docs/EVAL_GUIDE.md),
[`docs/PREFERRED_HARNESS_REPRODUCTION.md`](../docs/PREFERRED_HARNESS_REPRODUCTION.md),
[`docs/RESUME_HANDOFF.md`](../docs/RESUME_HANDOFF.md).

## Help

```bash
python eval/unified_eval_listener.py --help
```
