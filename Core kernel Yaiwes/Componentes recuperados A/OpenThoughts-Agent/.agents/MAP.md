# `.agents/` — what's in here

A map of this directory. `CLAUDE.md` (repo root) is the thin index that ties it together; this file just says what each piece *is*.

| Entry | What it is |
|---|---|
| **`skills/`** | **Specific actions**, one folder per task, each with a `SKILL.md`. Invocable by name (via the Skill tool) or dispatched to a subagent. Named by prefix: `launch:` / `cleanup:` / `monitor:` / `analyze:` / `crud:` / `code:` / `build:`. This is the "how to *do* X" library (~44 skills). |
| **`projects/`** | **How to use each codebase/dependency** — what it is + its facts & gotchas, one folder per repo (`ot-agent`, `marin`, `marinskyrl`, `harbor`, `vllm`, `levanter`, `llama-factory`, `axolotl`, `daytona`, …). The "what *is* this codebase" reference. |
| **`ops/`** | **Machine/cluster particulars** — access, paths, env/container maps, gotchas, one folder per target: `leonardo`, `iris`, `tacc`, `jupiter`, `torch`, `local` (this Mac), `all` (cross-cluster), `experiments` (the tracker workspace), `data` (dataset trackers), `empireai`, `marenostrum`. The "how to operate *on this machine*" reference. |
| **`secret.md`** | Untracked, gitignored — privileged values (tokens, pinggy bank, secrets-file path). Referenced by name from skills/ops; never committed. |
| **`settings.local.json`** | Local agent settings for this project. |
| **`scheduled_tasks.lock`** | Lock file for scheduled tasks (crons/loops). |
| **`worktrees/`** | Transient git worktrees used for isolated agent work (auto-cleaned). |

**Rule of thumb:** doing a task → **skills/**; understanding a codebase → **projects/**; operating on a cluster → **ops/**.
