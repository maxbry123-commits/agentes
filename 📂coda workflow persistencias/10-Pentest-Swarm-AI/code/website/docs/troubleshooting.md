---
sidebar_position: 10
title: Troubleshooting
---

# Troubleshooting

Quick fixes for the issues people hit most. When in doubt, start with the
built-in health check:

```bash
pentestswarm doctor
```

It verifies Go, Docker, installed tools, and provider config, and tells you
exactly what to fix.

## `command not found` after `npm -g`

The binary installed, but the directory npm puts global binaries in isn't on
your `PATH` for the current shell — this is very common with **nvm**, which uses
a **per-Node-version** global bin directory.

Try, in order:

1. Refresh your shell's command lookup:

   ```bash
   hash -r
   ```

2. If you use nvm and recently switched Node versions, reinstall under the
   **active** version:

   ```bash
   npm install -g @armurai/pentestswarm
   ```

3. Confirm where it landed and that the directory is on your `PATH`:

   ```bash
   npm bin -g
   which pentestswarm
   ```

## Missing recon tools

If the swarm reports it can't find `nuclei`, `httpx`, `nmap`, or the other recon
tools, install the toolchain:

```bash
pentestswarm install-tools
```

Then re-run `pentestswarm doctor` to confirm they're detected.

## Docker errors

Docker is only required for the **bundled labs** (`--lab` /
`--lab-target`), which spin up a vulnerable target in a container. If you're
scanning a real target you don't need Docker at all. If you *are* running a lab,
make sure the Docker daemon is running and you can `docker ps` without errors.

## Dashboard port 7777 is busy

The web dashboard defaults to `localhost:7777`. If that port is already in use,
Pentest Swarm **falls back automatically** to `7778`, then `7799`, then `8899` —
no action needed. Watch the launcher / log output for the actual URL it settled
on. See [Live Views](./dashboard.md).

## The run cost more than I expected

Set a hard cap with `--budget <usd>` (or the launcher's **Spend cap** field).
The swarm winds down gracefully and still writes a report the moment cumulative
spend reaches the cap, and because the meter prices at the costliest model in
the mix, it **never overspends**. Local providers (Ollama / LM Studio) have no
cost at all. See [Cost & Safety](./cost-and-safety.md).

## How do I stop a run?

Click the red **STOP** button in the web dashboard, or press **`q`** /
**`Ctrl-C`** in the terminal. Either way it stops **gracefully** and still writes
the report. See [Cost & Safety](./cost-and-safety.md#killswitch).

## Still stuck?

Run `pentestswarm doctor`, then bring the output to
[Discord](https://discord.gg/6qtkhpW8tk) or open an issue on
[GitHub](https://github.com/Armur-Ai/Pentest-Swarm-AI/issues).
