---
sidebar_position: 1
slug: /
title: Introduction
---

# Pentest Swarm AI

**The open-source XBOW alternative — but built on a real swarm.**

Pentest Swarm AI is a self-hosted, autonomous offensive-security tool. Tools
like XBOW proved AI can top the bug-bounty leaderboards — but XBOW is a
**closed, hosted SaaS**: your targets, your findings, and the model all run on
someone else's cloud, at their price. Pentest Swarm AI is the alternative you
run yourself, and it is *more* powerful where it counts — because it is built
on **concurrency and a real swarm** instead of one agent grinding down a fixed
checklist.

## What makes it a *swarm* (and not a pipeline)

Most "multi-agent" pentesting tools are really a single planner LLM dispatching
to specialists in a fixed order — recon → classify → exploit → report. That is
a **pipeline**, not a swarm.

Pentest Swarm AI is built on three swarm-intelligence primitives:

- **Stigmergy** — agents coordinate by reading and writing findings on a shared
  blackboard, not by a central planner. A finding's *pheromone weight* biases
  other agents toward it and decays over time, so stale paths die naturally.
- **Emergence** — attack chains appear that no single agent planned. A recon
  finding wakes the classifier; a high-severity classification wakes the
  exploit agent; exploit results feed back onto the board and wake the report
  agent. The order isn't prescribed — it emerges from the blackboard state.
- **Decentralization** — each agent runs its own *trigger predicate*. Add a new
  agent with its own predicate and it joins the swarm without anyone rewriting
  the orchestrator.

The practical payoff: **dozens of agents work your target concurrently.** A
1,000-subdomain scope gets worked in parallel — finding vulnerabilities at
machine speed. And unlike a scanner that flags thousands of unverified
"maybes," the swarm **exploits what it finds and proves it** with captured
evidence, then writes the report.

## Who it's for

- **Pentesters** who want to cover a whole scope overnight.
- **Bug bounty hunters** racing to first-blood on a fresh target.
- **Red teamers** who need breadth, fast.
- **Security researchers** experimenting with autonomous offense.

## Safe to leave running

Autonomy is only useful if it's safe to walk away from. Every run is bounded by
four independent guardrails: a hard **spend cap** (`--budget`) that stops before
it overspends and still writes the report, a graceful **killswitch** (a STOP
button in the dashboard, `q`/`Ctrl-C` in the terminal), a **safe mode** that
blocks destructive commands, and **scope enforcement** that can't be bypassed.
See [Cost & Safety](./cost-and-safety.md).

## See it work

Two live views come up as the swarm runs — a **web dashboard on
`localhost:7777`** and a full-screen **terminal TUI** — with a growing attack
graph, a threat gauge, a detection timeline, and a polished end-of-run report of
the proven attack chains. See [Live Views](./dashboard.md).

## Shape the engagement

A **[scan mode](./modes.md)** tells the swarm what kind of job it's on —
`manual` (broad coverage), `bugbounty` (reportable, deduped, severity-ranked),
`ctf` (foothold → privesc → flags), or `asm` (non-intrusive surface mapping).

## Bring your own model

Pentest Swarm AI is the **harness, not the model.** Run it on Claude, anything
OpenAI-compatible (including **Together AI**'s hosted Llama / Qwen / DeepSeek),
first-party Gemini, or a fully local **Ollama / LM Studio** — air-gapped, with
zero API cost and not one byte of your data leaving your box. The model does the
reasoning; the swarm gives it hands: real tools, coordination, scope safety, and
evidence-backed reports. See [Providers](./providers.md).

## Get started

Ready to run it? Head to the **[Quick Start](./quickstart.md)** — one command to
install, one to run.

:::caution Authorized use only
Pentest Swarm AI is for **authorized security testing**, bug bounty, CTF, and
research only. You must have explicit written permission for any target you
scan. See the [Security & Responsible Use](./security.md) page.
:::
