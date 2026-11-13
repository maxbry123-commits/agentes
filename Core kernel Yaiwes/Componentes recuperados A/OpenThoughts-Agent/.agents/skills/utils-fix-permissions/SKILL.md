---
name: utils-fix-permissions
description: >-
  Fix file permissions on a directory tree on an HPC cluster (Leonardo, Jupiter,
  TACC, etc.) so other users can read your shared data, conda envs, or work
  directories. Runs `scripts/permissions/fix_permissions.sh <dir>` over SSH on
  the target cluster — sets directories to 755, files to 644, then restores
  execute bits on bin/ entries, ELF binaries, and shebang scripts, and ensures
  all ancestor directories are traversable (o+x). Use when another user reports
  "Permission denied" reading your files, after creating a new conda env or
  shared data dir, or when a cross-user pipeline can't access your checkpoint/
  eval/trace outputs.
---

# utils-fix-permissions

Set shared-readable permissions on an HPC directory tree.

## When to use

- Another user reports **"Permission denied"**.
- A shared conda env or data directory needs read access.
- A cross-user pipeline cannot read checkpoint, eval, or trace output.
- `rsync` or `scp` preserved 600/700 permissions.

## What it does

`scripts/permissions/fix_permissions.sh <dir>` performs these passes:

| Pass | Action |
|---|---|
| 0 | Ensure all **ancestor directories** up to `/` are traversable (`o+x`) — only touches dirs you own |
| 1 | Set all **directories** to `755` (`rwxr-xr-x`) |
| 2 | Set all **files** to `644` (`rw-r--r--`) |
| 3 | Restore `755` on executables in **`bin/`** directories |
| 4 | Restore `755` on **ELF binaries** (detected by `\x7f ELF` magic header) |
| 5 | Restore `755` on **shell scripts with shebang** (`#!`) |

Files remain owner-writable; collaborators receive read and execute.

## How to invoke

SSH to the target cluster and run the script from the repo root:

```bash
# Leonardo example
ssh Leonardo 'cd $WORK/OpenThoughts-Agent && bash scripts/permissions/fix_permissions.sh /leonardo_work/AIFAC_5C0_290/bfeuer00'

# TACC example (large tree — run on a compute node if login node is loaded)
ssh TACCVista 'cd $SCRATCH/OpenThoughts-Agent && bash scripts/permissions/fix_permissions.sh $SCRATCH/eval_jobs'

# Jupiter example
ssh Jupiter 'cd $DCFT && bash scripts/permissions/fix_permissions.sh /p/home/../../public'
```

### Large directories

For big trees, use an interactive compute node:

```bash
# TACC
ssh TACCVista 'srun -p gh-dev -N 1 -n 1 -t 08:00:00 --account=CCR24067 bash -c "cd $SCRATCH/OpenThoughts-Agent && bash scripts/permissions/fix_permissions.sh $SCRATCH/miniconda3"'

# Leonardo (idev or sbatch)
ssh Leonardo 'srun -p boost --account=AIFAC_5C0_290 --time=08:00:00 -N 1 bash -c "cd $WORK/OpenThoughts-Agent && bash scripts/permissions/fix_permissions.sh $WORK"'
```

## Gotchas

- Use `chmod -R g+w <dir>` when shared editing is required.
- Rerun after `pip install` for a shared conda environment.
- Pass 0 changes only owned NFS directories.
- Safe to rerun; it is idempotent.
