# Mumwelt (Marin corpus) — facts & gotchas

Offline-queryable mirror of Marin activity: GitHub issues/PRs/comments, Discord, W&B run metadata and final numbers, weekly summaries, and searchable code indexes. Results are searchable by keyword and meaning and carry citable URLs.

## Skills

`mum skills install` installs three skills under `~/.agents/skills/`:

- **`mumwelt`** — default for broad, ambiguous, or multi-part research. It decomposes the question across the corpus and reports a cited synthesis.
- **`mumwelt-code`** — the lightweight first choice for a single implementation lookup. It searches embedding-backed code lanes for `main` and in-flight branches; treat only `main` as current behavior.
- **`mumwelt-publish`** — publishes a finished cited answer as a rendered private gist.

The old `marin-research` and `marin-publish` skill directories are retired. `mumwelt` supersedes the former; `mumwelt-publish` supersedes the latter.

## Install / update

```bash
uv tool install --reinstall git+https://github.com/Open-Athena/mumwelt.git
mum skills install
rm -rf ~/.agents/skills/marin-research ~/.agents/skills/marin-publish
mum refresh
```

The uv-managed executable is normally `~/.local/bin/mum` (use that absolute path when the shell does not include it on `PATH`). Do not rely on the former `otagent`-conda installation.

`mum refresh` updates both the corpus and the code indexes. The corpus currently has separate prose and code embeddings; ordinary search shows code lanes separately, while `--source code` gives code the full result budget.

## Commands

- `mum status` — corpus chunk count and age, summaries coverage, and server build age/size.
- `mum refresh` — update corpus, summaries, and code indexes.
- `mum search "<query>" [--source github,discord,wandb,narrative,code] [--kind run,issue,pr,comment,message,section,branch-symbol] [-k N] [--json]` — fused keyword and semantic retrieval. Without `--source code`, output includes separately ranked `code · main` and `code · in-flight branches` lanes.
- `mum search "<subject>" --source code -k 30` — deliberate implementation search. Cite `main` for current behavior; cite a branch only as in-flight work.
- `mum run <project>/<run>` or `mum run <wandb URL>` — run metadata, final summary numbers, and config.
- `mum show <url-or-ref>` — expand a search hit.
- `mum summaries list | show latest | links YYYY-MM-DD` — orient on recent activity before broad research.

## Freshness policy (from the skills)

If the mirror is missing, refresh. If it is **over one day old**, refresh before relying on it. Within one day, use it as-is; ask before refreshing only when the question is time-sensitive. Honor an explicit request not to repull. `MARIN_MAX_AGE_DAYS` configures the threshold.

## The big gotcha: `mum run` resolves configs by run name and can 404 for executor-launched or crashed runs

- `mum run <proj>/<run>` queries config by display name. It works cleanly for script-launched runs whose W&B name equals the run id. It can fail for marin-executor-launched runs, whose selected-cell label appears only in derived eval runs, and for crashed runs without a finalized config export.
- When it fails, use `mum search "<run-id>" --source wandb` and `mum show <run-url>`: indexed snippets still expose configuration fields. For the authoritative resolved config of an executor run, use GCS `.executor_info`.
- W&B per-step history is not mirrored; only final summary numbers are available.

## Naming note (W&B run ids vs. cell labels)

A Marin run id can be a selected-cell label rather than a literal W&B training-run name. Search the run family to locate the actual training run before concluding the data is absent.
