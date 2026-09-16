# Project Safety Policy

`Intent-LED-mul-agent` is a copied project that may be modified, but it is not a
git repository. The research-agent workflow therefore treats it as a mutable
copy with explicit guardrails.

Default policy after the user confirmed this is a backed-up copy:

- Use `topics/intent_led_virat.json` as the source of edit permissions.
- High exploration mode is allowed for this copied project.
- Plan before broad rewrites.
- Keep `dry_run_first: true` for long or risky commands.
- Keep `backup_required: true`.
- Avoid modifying protected baseline outputs, checkpoints, raw data, or external
  `../MID-main` processed data unless there is a specific reason.
- Keep each patch small, with `max_files_per_patch: 8`.
- Run debug or smoke configs before any full training run.

Allowed paths are intentionally focused on code and config:

- `models/*`
- `trainer/*`
- `data/dataloader_virat.py`
- `cfg/virat/*`
- `utils/*`
- `main_led_nba.py`
- `visualize_virat_prediction.py`
- `work.md`

Protected paths:

- `results/checkpoints/*`
- `results/led_virat/baseline_original/*`
- `results/fig/*`
- `../MID-main/*`
- `data/raw/*`
- `__pycache__/*`
