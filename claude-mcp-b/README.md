---
title: Maxbry Claude GitHub Backup MCP
emoji: 🔁
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
hf_oauth: false
pinned: false
---

# Maxbry Claude GitHub Backup MCP

Independent backup path for **Claude Chat/Web**, not Claude Code.

```text
Claude Chat
   │ MCP (no HF sign-in)
   ▼
Hugging Face Docker Space (this app)
   │ dedicated GitHub PAT stored only as Space Secret
   ▼
GitHub REST API
   ▼
maxbry123-commits/* repositories
```

## Required Space Secret

Set exactly one GitHub credential in the Space **Settings → Variables and secrets**:

- `GITHUB_PERSONAL_ACCESS_TOKEN` = dedicated GitHub PAT for this backup MCP.

Never commit the PAT to this repository, a README, a workflow, or a Claude conversation.

## Optional Space variable

- `GITHUB_DEFAULT_OWNER=maxbry123-commits`

## Claude custom connector

Use:

- Name: `GitHub Backup HF`
- MCP URL: `https://comand-center-1-claude-github-mcp-backup.hf.space/mcp`
- Requires sign-in: **OFF**

## Verification order

1. `connection_status`
2. `list_repositories`
3. `get_file` on `agentes`, branch `claude-mcp-write-test`
4. `create_or_update_file` only under `claude-mcp-tests/`
5. `delete_file` only on `claude-mcp-tests/DELETE_ME.md`
6. Verify resulting commit SHAs from GitHub before using the connector on real work.

## Capability

Convenience tools cover repository listing, file read/write/delete, branch create/delete, issue creation, PR creation and repository deletion. `github_api` is the full REST fallback for operations not wrapped by a convenience tool. Effective authority is limited by the GitHub PAT stored in the Space secret.
