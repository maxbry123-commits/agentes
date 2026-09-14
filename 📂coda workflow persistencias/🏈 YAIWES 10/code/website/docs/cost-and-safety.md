---
sidebar_position: 6
title: Cost & Safety
---

# Cost & Safety

An autonomous swarm is only useful if you can leave it running without watching
it. Pentest Swarm AI gives you four independent guardrails that make that safe:
a **spend cap** that never overspends, a **killswitch** that stops a run
gracefully, a **safe mode** that blocks destructive commands, and
**scope enforcement** that can't be bypassed. This page covers each, then how
they combine.

## Spend cap (`--budget <usd>`) {#spend-cap}

A **hard per-run USD cap** on LLM spend. Pass it on `scan`, or set it in the
launcher's **Spend cap** field.

```bash
pentestswarm scan target --scope target --swarm --budget 5
```

How it works:

- A watcher tracks the **live LLM cost meter** as the run proceeds. The moment
  cumulative spend reaches the cap, it **winds the campaign down gracefully** —
  it writes `CAMPAIGN_COMPLETE` so the **report still generates on the partial
  findings** already gathered. Nothing is left half-written; you get a report
  for what the swarm found before it hit the ceiling.
- The meter is priced at the **costliest model in the mix**. That means the cap
  errs toward stopping **slightly early** rather than late — so a run
  **never overspends** the number you set.
- `--budget 0` means **no cap**.
- Local providers (**Ollama**, **LM Studio**) have **no cost**, so the cap is
  n/a. In the launcher the field shows *"no cost — local model"* for them.

In the launcher the Spend cap field has a **minimum of \$2** on paid providers,
and you adjust it with **←/→**.

:::tip Worked example
```bash
pentestswarm scan target --scope target --swarm --budget 5
```
This run will stop and produce a report the instant cumulative LLM spend reaches
\$5 — and because the meter prices at the most expensive model in the routing
mix, actual spend lands at or just under \$5, never over.
:::

:::note Together AI stays cheap by default
The `together` provider runs in multi-model mode and keeps a typical run near
the ~\$1 single-model baseline, so a \$5 cap leaves comfortable headroom. See
[Providers](./providers.md#together-ai).
:::

## Killswitch

You can stop a running campaign at any time, and it always stops **gracefully** —
winding the swarm down and **still writing the report** on whatever it has found
so far.

- **Web dashboard** — a red **STOP** button. It `POST`s to `/api/stop`, which
  halts the run gracefully.
- **Terminal TUI** — press **`q`** or **`Ctrl-C`**.

Either way you get a clean shutdown and a report, not a truncated process. See
the [Dashboard](./dashboard.md) page for where the STOP button lives.

## Safe mode (`--safe-mode`)

Blocks **destructive command tokens** — `rm`, `DROP`, `kill`, `chmod`, and
similar — **before** they're executed. If the swarm's reasoning ever proposes a
command containing one, it's refused rather than run.

```bash
pentestswarm scan target --scope target --swarm --safe-mode
```

This is **required by programs that disallow risky automated actions** — many
bug-bounty programs forbid anything that could modify or damage the target.
Turn it on whenever the rules of engagement demand non-destructive testing.

## Scope enforcement (`--scope`) {#scope-enforcement}

`--scope` declares the **authorized scope** — CIDRs and/or domains,
comma-separated. It is enforced at **both** the tool layer **and** the executor,
so an in-scope constraint is **not bypassable** by an agent that "decides" to
reach further.

```bash
pentestswarm scan example.com --scope example.com,api.example.com,10.0.0.0/24 --swarm
```

- **Non-lab scans require a scope.** If you omit it, scope **defaults to the
  target itself**.
- Bundled labs don't need it — the lab *is* the scope.

:::danger Scope is a guardrail, not authorization
Scope enforcement stops the swarm from wandering off-target. It does **not**
grant you permission to test anything. You are still responsible for pointing
the swarm only at systems you're authorized to test. See
[Security & Responsible Use](./security.md).
:::

## Putting it together

These four controls are independent, and together they make an unattended run
safe:

- **`--scope`** bounds *where* the swarm can act — nowhere outside the authorized
  targets, enforced twice over.
- **`--safe-mode`** bounds *what* it can do — no destructive commands, ever.
- **`--budget`** bounds *how much* it can spend — a hard ceiling that stops the
  run and still delivers a report.
- **The killswitch** lets you end it *whenever you want* — cleanly, with a
  report.

A run launched with a correct scope, safe mode on, and a budget set is one you
can start and walk away from: it will stay on-target, avoid anything
destructive, stop itself before it costs more than you allowed, and hand you a
report either way.

```bash
export PENTESTSWARM_ORCHESTRATOR_API_KEY=your-key
pentestswarm scan example.com \
  --scope example.com \
  --safe-mode \
  --budget 10 \
  --mode bugbounty \
  --swarm --follow
```
