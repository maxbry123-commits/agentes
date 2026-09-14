---
sidebar_position: 5
title: CLI Reference
---

# CLI Reference

Everything Pentest Swarm AI does is available from the `pentestswarm` binary.
There are two ways in: **`run`** (the interactive front door) and **`scan`**
(the scriptable engine underneath it). Everything else — health checks, the
toolchain installer, the MCP and API servers, playbooks — hangs off the same
binary as subcommands.

## `run` vs `scan`

- **`pentestswarm run`** is the **front door**: an interactive TUI launcher.
  Pick your provider and paste a key in the UI, choose a target or a bundled
  lab, set a spend cap, choose your live view, and launch — **no flags to
  remember**. It runs readiness checks for you and then calls `scan` under the
  hood.
- **`pentestswarm scan …`** is the **engine**: fully flag-driven and
  scriptable, so it drops straight into CI, cron, or a shell script. `run` is
  just a friendly wrapper around it.

Use `run` when you're driving it by hand; use `scan` when you're automating.

:::tip Where to go deeper
This page is the flag-level reference. For the concepts behind the flags see
**[Scan Modes](./modes.md)** (`--mode`), **[Providers](./providers.md)**
(`--provider`), **[Cost & Safety](./cost-and-safety.md)** (`--budget`,
`--safe-mode`, `--scope`), **[Live Views](./dashboard.md)** (`--tui`,
`--follow`), and **[Configuration](./configuration.md)** (`init`, `doctor`,
`install-tools`).
:::

## Commands

### `pentestswarm run`

⭐ Interactive TUI launcher — the recommended starting point. Walks you through
provider + key, target or bundled lab, scan mode, spend cap, live-view choice,
and readiness checks, then launches the swarm. It also opens the
**[web dashboard](./dashboard.md)** on `localhost:7777` immediately, so it's
ready the moment you launch.

```bash
pentestswarm run
```

### `pentestswarm scan <target>`

Run a scan against a target. This is the engine every other entry point drives.

```bash
export PENTESTSWARM_ORCHESTRATOR_API_KEY=your-key
pentestswarm scan example.com --scope example.com --swarm --follow
```

#### Key flags

| Flag | What it does |
|------|--------------|
| `--scope <scope>` | Authorized scope — CIDRs / domains, comma-separated. Enforced at the tool layer **and** the executor; **not bypassable**. Non-lab scans require it (defaults to the target itself if omitted). See [Cost & Safety](./cost-and-safety.md#scope-enforcement). |
| `--swarm` | Enable the stigmergic swarm scheduler (dozens of agents working concurrently) instead of a linear pass. |
| `--tui` | Full-screen terminal live view — boxed panels, sparklines, risk + spend meters, the stigmergic blackboard. See [Live Views](./dashboard.md). |
| `--follow` | Stream progress to the terminal as plain log lines (good for CI). |
| `--mode <mode>` | Engagement type: `manual` · `bugbounty` · `ctf` · `asm`. See [Scan Modes](./modes.md). |
| `--budget <usd>` | Hard per-run USD spend cap; the swarm winds down gracefully when it's reached. `0` = no cap. See [Cost & Safety](./cost-and-safety.md#spend-cap). |
| `--safe-mode` | Block destructive command tokens (`rm`, `DROP`, `kill`, `chmod`, …) before execution. |
| `--active-scan` | Toggle active exploitation tools. On by default except in `asm` mode; `--active-scan=true` forces them back on in ASM. |
| `--provider <name>` | LLM provider: `together` · `claude` · `openai` · `gemini` · `orcarouter` · `ollama` · `lmstudio`. See [Providers](./providers.md). |
| `--lab` / `--lab-target <lab>` | Attack a bundled, intentionally-vulnerable lab (`crapi`, `juiceshop`, `vampi`, `dvga`) that spins up and tears down in Docker. |
| `--dry-run` | Plan the run and show what the swarm *would* do without executing tools or spending on the LLM. |
| `--estimate` | Print a cost/scope estimate for the run and exit. |

A typical scriptable run:

```bash
export PENTESTSWARM_ORCHESTRATOR_API_KEY=your-key
pentestswarm scan example.com \
  --scope example.com \
  --mode bugbounty \
  --provider together \
  --budget 5 \
  --safe-mode \
  --swarm --follow
```

### `pentestswarm scan --tui`

Run with the **full-screen live dashboard** in your terminal — boxed panels for
the swarm cluster, findings, telemetry sparklines, and risk + spend meters, plus
the animated stigmergic blackboard.

```bash
pentestswarm scan <target> --scope <target> --swarm --tui
```

See **[Live Views / Dashboard](./dashboard.md)** for everything the web and
terminal views show.

### `pentestswarm scan --lab --lab-target <lab>`

Attack a bundled, intentionally-vulnerable lab that spins up, gets attacked, and
tears down — no setup, no external target, no scope flag needed. Requires
Docker.

```bash
pentestswarm scan --lab --lab-target crapi --provider ollama --swarm --tui
```

Labs: `crapi`, `juiceshop`, `vampi`, `dvga`.

### `pentestswarm doctor`

System health check — verifies Go, Docker, installed recon tools, and provider
configuration, and tells you what (if anything) to fix. See
[Configuration](./configuration.md).

```bash
pentestswarm doctor
```

### `pentestswarm init`

Write a starter `config.yaml` you can edit — orchestrator provider/model/key and
optional per-agent overrides. See [Configuration](./configuration.md).

```bash
pentestswarm init
```

### `pentestswarm install-tools`

Fetch the recon / exploit toolchain (subfinder, httpx, nuclei, naabu, katana,
dnsx, gau, nmap, …) so the swarm has real tools to operate.

```bash
pentestswarm install-tools
```

### `pentestswarm playbook run <name> --target <t>`

Run a deterministic attack chain (a playbook) against a target. See
[Playbooks](./playbooks.md).

```bash
pentestswarm playbook run bug-bounty --target example.com
```

### `pentestswarm mcp serve`

Start the MCP (Model Context Protocol) server so Claude Desktop, Cursor, and
other MCP clients can drive the swarm as a tool.

```bash
pentestswarm mcp serve
```

### `pentestswarm serve`

Start the API server together with the web dashboard.

```bash
pentestswarm serve
```

### `pentestswarm docs`

Open the documentation site in your browser.

```bash
pentestswarm docs
```

### `pentestswarm upgrade`

Update the binary in place to the latest release.

```bash
pentestswarm upgrade
```

### `pentestswarm version`

Print the installed version.

```bash
pentestswarm version
```

## Quick tour

```bash
pentestswarm run                                        # ⭐ Interactive TUI — no flags
pentestswarm scan <target> --scope <scope> --swarm      # Scriptable swarm scan
pentestswarm scan <target> --scope <scope> --tui        # Full-screen live dashboard
pentestswarm scan --lab --lab-target crapi              # Attack a bundled lab
pentestswarm scan <target> --scope <scope> --budget 5   # With a hard spend cap
pentestswarm playbook run <name> --target <t>           # Run a playbook
pentestswarm init                                       # Write a starter config
pentestswarm doctor                                     # Health check
pentestswarm install-tools                              # Fetch the toolchain
pentestswarm mcp serve                                  # MCP server (Claude / Cursor)
pentestswarm serve                                      # API server + dashboard
pentestswarm docs                                       # Open the docs site
pentestswarm upgrade                                    # Update in place
pentestswarm version                                    # Print version
```
