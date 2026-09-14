---
sidebar_position: 7
title: Live Views / Dashboard
---

# Live Views / Dashboard

A swarm run is not a black box. Pentest Swarm AI gives you two live views into
the campaign as it happens — a **web dashboard** in your browser and a
full-screen **terminal TUI** — and by default it runs **both** at once.

You choose which in the launcher's **Live view** setting (web + terminal, web
only, terminal only, or off), or with `--tui` on `scan`.

## Web dashboard — `localhost:7777`

The web dashboard runs on **`localhost:7777`**. If that port is busy it falls
back automatically to **7778**, then **7799**, then **8899** — watch the
launcher output for the URL it settled on.

It starts **as soon as `pentestswarm run` opens** — so the page is up and ready
before you launch. It's **empty until you launch a campaign**, then it fills in
live.

What it shows:

- **Live progress console** — a phase bar, the current activity, and running
  counters, so you always know what stage the swarm is in and what it's doing
  right now.
- **Attack graph** — a graph that **grows as endpoints and findings are
  discovered**, including the exploit **probe fan-out** mesh (the parallel
  probes agents launch against a candidate).
- **Severity ring** — findings broken down by severity at a glance.
- **Threat gauge** — a **0–100 risk score** for the target.
- **Detection timeline** — **stacked severity over time**, so you can see how
  and when the picture worsened.
- **Inline finding detail** — **click a finding** to expand its full detail.
- **End-of-run report** — a polished report at the end, with the **proven attack
  chains** the swarm demonstrated.

The dashboard is also where the **killswitch** lives: a red **STOP** button that
halts the run gracefully and still writes the report. See
[Cost & Safety](./cost-and-safety.md#killswitch).

:::tip Start it standalone
`pentestswarm serve` starts the API server together with the web dashboard on
its own — handy if you want the dashboard up independently of the launcher.
:::

## Terminal TUI (`--tui`)

The full-screen terminal TUI is for when you'd rather stay in the terminal. Add
`--tui` to a `scan` (the launcher's **Live view** includes it by default):

```bash
pentestswarm scan <target> --scope <target> --swarm --tui
```

It renders boxed panels:

- **Swarm cluster** — the agents and their state.
- **Findings** — the graded findings stream.
- **Telemetry** — sparklines and activity bars.
- **Risk + spend meters** — the live risk score and the running cost against
  your [budget](./cost-and-safety.md#spend-cap).
- **Stigmergic blackboard** — the animated shared board the agents coordinate
  through.

Stop the TUI (and the run) with **`q`** or **`Ctrl-C`** — it winds down
gracefully and writes the report.

## Running both together

By default the launcher's **Live view** is **web + terminal**, so you get the
browser dashboard and the terminal TUI simultaneously. The options are:

- **web + terminal** (default)
- **web only**
- **terminal only**
- **off**

Pick whichever suits how you're working — the underlying campaign is identical
regardless of which views are on.
