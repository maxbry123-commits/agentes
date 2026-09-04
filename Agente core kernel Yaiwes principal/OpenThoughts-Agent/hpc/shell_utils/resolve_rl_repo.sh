#!/bin/bash
# ==============================================================================
# RL Training Repo Directory Resolution
# ==============================================================================
# The RL training repo (skyrl-train + examples/terminal_bench entrypoints) was
# historically always cloned to a directory literally named "SkyRL". Its
# contents may now be replaced by MarinSkyRL while keeping the directory NAME
# "SkyRL" (to satisfy hardcoded paths), and future setups may instead name the
# dir "MarinSkyRL". This helper lets the dotenv files + setup_rl_env.sh consume
# either, while staying byte-identical for existing SkyRL-only deployments.
#
# NOTE: this resolves a FILESYSTEM PATH only. The Python import name
# (skyrl_train) does NOT change with the outer directory name and is unaffected.
#
# Usage:
#   source /path/to/hpc/shell_utils/resolve_rl_repo.sh
#   export SKYRL_HOME="$(resolve_rl_repo_dir "$DCFT")"
#
# Precedence:
#   (a) explicit $RL_REPO_DIR override (full path) if set — honored verbatim;
#   (b) probe <parent> for SkyRL then MarinSkyRL, return first that exists;
#   (c) fall back to <parent>/SkyRL (the historical literal) for byte-identical
#       back-compat when neither candidate exists yet.
# ==============================================================================

resolve_rl_repo_dir() {
    local parent="$1"
    if [[ -n "${RL_REPO_DIR:-}" ]]; then
        echo "$RL_REPO_DIR"
        return 0
    fi
    local name
    for name in SkyRL MarinSkyRL; do
        if [[ -d "$parent/$name" ]]; then
            echo "$parent/$name"
            return 0
        fi
    done
    echo "$parent/SkyRL"
}
