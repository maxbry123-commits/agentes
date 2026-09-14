---
sidebar_position: 8
title: Playbooks
---

# Playbooks

**Playbooks are deterministic attack chains the swarm can execute.** Where the
stigmergic scheduler lets the swarm improvise — reacting to findings as they
land — a playbook gives it a known-good, repeatable sequence for a specific job:
a bug-bounty sweep, external attack-surface mapping, a CI/CD security gate, an
internal-network pass, or a CTF solve.

Think of them as the difference between "explore this target" and "run this
proven procedure against this target." Playbooks make runs reproducible and
easy to drop into automation.

:::note Playbook vs. swarm mode
A **playbook** runs a fixed, known-good sequence — repeatable and predictable. A
**[scan mode](./modes.md)** (via `--mode`) instead steers the *improvising*
swarm toward an objective. Reach for a playbook when you want the same procedure
every time; reach for a swarm scan when you want the swarm to react to what it
finds.
:::

## Running a playbook

```bash
pentestswarm playbook run <name> --target <target>
```

For example:

```bash
pentestswarm playbook run bug-bounty --target example.com
```

## Bundled playbooks

The repo ships a set of playbooks under
[`playbooks/`](https://github.com/Armur-Ai/Pentest-Swarm-AI/tree/main/playbooks):

- `bug-bounty` — a bug-bounty-style sweep
- `external-asm` — external attack-surface mapping
- `ci-cd-security` — a security gate for CI/CD pipelines
- `internal-network` — an internal-network pass
- `ctf-solver` — CTF solving
- `api-security` — API-focused attacks
- `owasp-top10` — OWASP Top 10 coverage

Each is a YAML file — open one to see the exact chain it runs.

:::note Authoring is evolving
The playbook format and authoring workflow are still evolving. The bundled
playbooks are the best current reference for structure; dedicated authoring
docs are on the way. Ask in [Discord](https://discord.gg/6qtkhpW8tk) if you're
writing your own and want a hand.
:::
