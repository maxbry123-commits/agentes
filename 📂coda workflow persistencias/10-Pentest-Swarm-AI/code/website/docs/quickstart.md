---
sidebar_position: 2
title: Quick Start
---

# Quick Start

**One command to install. One command to run.** No API key, no cloud, and no
bill to get started — a bundled lab plus a local model will find a real vuln for
free.

## 1 · Install (pick one)

```bash
# npm (Node ≥ 16) — the quickest path
npm install -g @armurai/pentestswarm

# any macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/Armur-Ai/Pentest-Swarm-AI/main/scripts/install.sh | sh

# Homebrew
brew install Armur-Ai/tap/pentestswarm

# Go toolchain
go install github.com/Armur-Ai/Pentest-Swarm-AI/cmd/pentestswarm@latest

# Docker
docker run --rm ghcr.io/armur-ai/pentestswarm:latest --help
```

Verify the binary is on your `PATH`:

```bash
pentestswarm --version
```

If the command isn't found right after an `npm -g` install, see
[Troubleshooting](./troubleshooting.md#command-not-found-after-npm--g).

## 2 · Run it

```bash
pentestswarm run
```

That's it. `run` opens the **interactive TUI launcher** — no flags to memorize.
Step through it in the terminal:

1. **Pick your AI provider** and paste a key right in the UI — Together AI
   (first-class multi-model: Llama / Qwen / DeepSeek routed by task), Claude,
   OpenAI, Gemini, OrcaRouter, or fully local **Ollama / LM Studio** (no key at
   all). See [Providers](./providers.md).
2. **Point it at a target** — a URL you're authorized to test, or a **bundled
   vulnerable lab** that spins up, gets attacked, and tears down after.
3. **Pick a scan mode** — `manual`, `bugbounty`, `ctf`, or `asm`. See
   [Scan Modes](./modes.md).
4. **Set a spend cap** — the **Spend cap** field is a hard per-run USD ceiling
   (minimum \$2 on paid providers, ←/→ to adjust; *"no cost — local model"* for
   Ollama / LM Studio). See [Cost & Safety](./cost-and-safety.md).
5. **Choose your live view** — a **web dashboard on `localhost:7777`** *and/or*
   a full-screen **terminal TUI** with live charts, a swarm-topology diagram,
   and a graded findings stream. Both, by default. See
   [Live Views](./dashboard.md).
6. **Launch** and watch the swarm work at machine speed.

A readiness check runs right inside the launcher (Go, Docker, tools, provider).
It never blocks — anything missing shows up as a note you can fix or ignore.

## Bundled labs

Don't have an authorized target handy? Pick a bundled, intentionally-vulnerable
lab. Each spins up in Docker, gets attacked, and tears down automatically — safe
and legal, zero setup:

| Lab | `--lab-target` | What it is |
|-----|----------------|------------|
| crAPI | `crapi` | Completely Ridiculous API — OWASP API Top 10 |
| Juice Shop | `juiceshop` | OWASP's modern web-app playground |
| VAmPI | `vampi` | Vulnerable REST API |
| DVGA | `dvga` | Damn Vulnerable GraphQL Application |

Running a lab requires Docker. That's the only thing Docker is needed for — see
[Troubleshooting](./troubleshooting.md).

## Prefer flags? (scripting / CI)

`run` just wraps `scan`, so everything is scriptable too:

```bash
# watch it find a real vuln in ~2 min — bundled lab, local model, no key
pentestswarm scan --lab --lab-target crapi --provider ollama --swarm --tui

# a real target, cloud model for max quality
export PENTESTSWARM_ORCHESTRATOR_API_KEY=your-key-here
pentestswarm scan <authorized-target> --scope <target> --swarm --follow
```

See the full [CLI reference](./cli.md) for every command and flag.

## Next steps

- **[Scan Modes](./modes.md)** — steer the swarm for bug bounty, CTF, or ASM.
- **[Cost & Safety](./cost-and-safety.md)** — spend caps, killswitch, safe mode,
  and scope: everything you need to leave a run unattended.
- **[Live Views / Dashboard](./dashboard.md)** — the `localhost:7777` dashboard
  and the terminal TUI.
- **[Configuration](./configuration.md)** — pin providers, models, and per-agent
  overrides in `config.yaml`.

:::tip Docs from the terminal
Run `pentestswarm docs` any time to open this documentation site in your
browser.
:::
