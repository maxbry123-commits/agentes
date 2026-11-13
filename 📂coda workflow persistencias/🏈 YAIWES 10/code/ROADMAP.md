# Roadmap

Where Pentest Swarm AI is headed. This is the public, high-level view — the
major capabilities we're building and the order we expect to ship them. Dates
are intentionally omitted; we ship when it's real and tested. Follow the
[GitHub Project board](https://github.com/orgs/Armur-Ai/projects/1) for live
status, and join the [Discord](https://discord.gg/6qtkhpW8tk) to shape it.

> Legend — **shipped**: in `main`, tested · **in progress**: actively being
> built · **next**: committed, not started · **planned**: on the map.

---

## 1. The Adaptive Swarm — runtime reaction to discoveries  ·  *next*

The swarm reacts to what it finds *as it finds it*. An identifier, token, or
object reference surfaced by one agent becomes shared state the whole swarm can
act on — turning a single leaked detail into cross-user and cross-endpoint
attacks that nobody scripted. This is the headline capability that separates a
swarm from a checklist: emergent attack chains, composed at runtime.

## 2. Self-Correcting Attacks — closed-loop replanning  ·  *in progress*

Attacks that heal themselves. When a step fails — the wrong content type, a
missing token, an unexpected response — the swarm reads the failure and adjusts
the next attempt instead of dead-ending. A first, bounded version ships today;
the full closed loop is next.

## 3. On-Demand Specialist Agents — dynamic sub-agents  ·  *planned*

The swarm spins up purpose-built agents at runtime — a session-holder to keep
an authenticated context, a fuzzer for a newly discovered parameter, a
chain-builder for a specific API — and retires them when the work is done.
Specialization without a fixed roster.

## 4. Attack Playbook Library — verified, expanding coverage  ·  *in progress*

A growing library of verified, reproducible attack chains across the OWASP API
& Web Top 10 — broken object-level authorization (BOLA/IDOR), broken
authentication, mass assignment, injection (SQL/NoSQL/command), SSRF, excessive
data exposure, and more. Each is confirmed against a live target and executed
end-to-end with evidence. (BOLA, NoSQL injection, and excessive data exposure
are live today.)

Backing this: a growing set of **bundled practice targets** you can attack with
one command (`--lab`, or pick one in `pentestswarm run`) — crAPI and Juice Shop
today, with VAmPI, DVGA, WebGoat and more on deck. We run the swarm against each
to find where it falls short and harden it, and you get safe, legal targets to
try it on yourself.

## 5. Live Mission Control — real-time visibility  ·  *next*

Watch the swarm work: agents activating, the pheromone graph shifting, findings
streaming in, attack chains drawn as they form — plus polished, shareable
reports. Understand *why* the swarm did what it did, not just what it found.

## 6. Benchmark-Proven — transparent, public scores  ·  *planned*

Published results on the recognised agentic-security benchmarks (Cybench,
AutoPenBench, CVE-Bench, and the XBOW validation set) with a fully transparent
methodology — the mode, the budget, the failures. Credibility through numbers,
not adjectives.

## 7. Tool & Platform Ecosystem — plug into your stack  ·  *in progress*

Deeper reach through the tools teams already use — Burp Suite, ZAP, Metasploit,
sqlmap and more via a clean adapter and MCP layer — plus first-class CI/CD
integration and a GitHub Action, so the swarm runs where your security work
already lives.

## 8. Continuous Attack-Surface Monitoring — always-on  ·  *planned*

Point the swarm at a scope once and let it watch: scheduled re-scans, diffing
run-over-run, and alerts when the attack surface changes or a new exposure
appears. From one-shot engagement to continuous coverage.

---

*Provider-agnostic and local-first throughout: run against frontier models or
fully local/air-gapped, your data never leaving your environment. A fine-tuned,
purpose-built Pentest Swarm model rides on top of this work.*

Have an opinion on the order, or a capability you need sooner? Open an issue or
say hi in [Discord](https://discord.gg/6qtkhpW8tk).
