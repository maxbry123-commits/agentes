---
title: Maxbry Claude GitHub Backup MCP
emoji: 🔁
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.26.0
python_version: 3.12
app_file: app.py
hf_oauth: true
hf_oauth_expiration_minutes: 43200
suggested_hardware: zero-a10g
pinned: false
---

# Maxbry Claude GitHub Backup MCP

Independent backup path for **Claude Chat/Web**, not Claude Code.

```text
Claude Chat
   │ MCP + OAuth
   ▼
Hugging Face Space (this app)
   │ dedicated PAT stored only as Space Secret
   ▼
GitHub REST API
   ▼
maxbry123-commits/* repositories
```

## Why this exists

The primary connector uses GitHub's official remote MCP and OAuth. This backup deliberately does **not** call the hosted GitHub MCP endpoint, so an outage or write-permission regression in that path does not disable this one.

## Required Space Secret

Set exactly one GitHub credential in the Space **Settings → Variables and secrets**:

- `GITHUB_PERSONAL_ACCESS_TOKEN` = dedicated fine-grained PAT created for this backup MCP.

Never commit the PAT to this repository, a README, a workflow, or a Claude conversation.

## Optional Space variables

- `GITHUB_DEFAULT_OWNER=maxbry123-commits`
- `MCP_ALLOWED_HF_USERS=COMAND-CENTER-1`

The server rejects authenticated Hugging Face users other than those listed in `MCP_ALLOWED_HF_USERS`.

## Claude custom connector

After the Space is running, use:

- Name: `GitHub Backup HF`
- MCP URL: `https://comand-center-1-claude-github-mcp-backup.hf.space/mcp`
- Requires sign-in: **ON**
- OAuth Client ID: leave empty
- OAuth Client Secret: leave empty

The exact `*.hf.space` hostname must be verified after the Space is created; do not treat the example URL as certified until then.

## Verification order

1. `connection_status`
2. `list_repositories`
3. `get_file` on `agentes`, branch `claude-mcp-write-test`
4. `create_or_update_file` only under `claude-mcp-tests/`
5. `delete_file` only on `claude-mcp-tests/DELETE_ME.md`
6. Verify resulting commit SHAs from GitHub before using the connector on real work.

## Capability

Convenience tools cover repository listing, file read/write/delete, branch create/delete, issue creation, PR creation and repository deletion. `github_api` is the full REST fallback for operations not wrapped by a convenience tool. Effective authority is always limited by the dedicated PAT's GitHub permissions.
