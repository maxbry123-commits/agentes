## HF Uploads + Long-Running Login-Node Commands

### Always `hf upload`, never `hf upload-large-folder`

Use sequential, three-argument `hf upload`; `hf upload-large-folder` deadlocks on HF Hub LFS rate limiting, and `huggingface-cli upload-large-folder` is a deprecation stub.

```bash
# Folder-to-repo-root
hf upload <repo> <local-folder> . --repo-type=model

# Single file
hf upload <repo> <local-file> <path-in-repo> --repo-type=model
```

### Always `tmux`, never `nohup` / `disown`

For long-running login-node commands, use detached `tmux`; Leonardo kills `nohup`/`disown` processes at ~100 s.

```bash
# Detached, named, output mirrored to a log via tee
tmux new-session -d -s <session_name> \
    "source ~/secrets.env && <command> 2>&1 | tee -a <log_path>"

# Inspect live:
tmux attach -t <session_name>     # Ctrl-b d to detach
tmux ls | grep <session_name>     # liveness check

# Kill:
tmux kill-session -t <session_name>
```

---

## HF org / target / credentials

### Default to PUBLIC uploads; `laion/` is the canonical target
- Default to public for RL/SFT/trace uploads; use private only for sensitive weights/data. `laion/` private quota is exhausted. `--private` is a no-value flag: create public with `create_repo(..., private=False)`, then upload.
- Use `laion/` for non-trivial model uploads. Ignore stale `hub_model_id: mlfoundations-dev/...` in `train_config` templates.

### Persistent 429 on the LFS batch endpoint = org storage quota, NOT rate-limiting
A 429 on `.../<repo>.git/info/lfs/objects/batch` that never clears is the target org being **out of storage** — HF masks the 403 quota error as 429. **Diagnose:** abort and run `hf upload <repo> <dir> . --repo-type=model` once — it surfaces the real error within seconds (e.g. `403 Forbidden: You have exceeded your public storage space`). Switch destination to `laion/`.

### `create_repo` 403 under `laion/` = org-membership role, NOT the token
A `403 "You don't have the rights to create a model under the namespace laion"` is an org-role issue. A laion admin must bump `read → write`; token reissue does not help. `read` can push to existing repos but cannot create them. Workarounds: role bump, pre-create with a write-capable account, or publish to `penfever/` then re-home.

Diagnostic (otagent python): `from huggingface_hub import whoami; [print(o['roleInOrg']) for o in whoami(token=…)['orgs'] if o['name']=='laion']`

### secrets.env paths
See `.agents/secret.md` — the `DC_AGENT_SECRET_ENV` section has the local-vs-cluster paths, the key inventory, and the `set -a; source "$DC_AGENT_SECRET_ENV"; set +a` load snippet.
