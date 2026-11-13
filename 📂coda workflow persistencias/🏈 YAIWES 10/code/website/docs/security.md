---
sidebar_position: 11
title: Security & Responsible Use
---

# Security & Responsible Use

Pentest Swarm AI is an **offensive-security tool**. It exploits what it finds and
proves it. That power comes with responsibility.

:::danger Authorized use only
Pentest Swarm AI is designed **exclusively** for **authorized security
testing**, **bug bounty programs**, **CTF competitions**, and **educational
research**. You must obtain explicit **written permission** from the target
system's owner before running any scan against it.
:::

## Your legal responsibility

Unauthorized access to computer systems is illegal under the **Computer Fraud
and Abuse Act (CFAA)**, the **Computer Misuse Act**, and equivalent laws
worldwide. The authors and contributors of this project accept **no liability**
for misuse, damage, or any illegal activity conducted with this tool.

By using this software, you agree that **you are solely responsible** for
ensuring your use complies with all applicable laws and regulations. **Do not
use this tool against systems you do not own or have explicit authorization to
test.**

## Scope enforcement — and why it's not a substitute for authorization

Pentest Swarm AI enforces `--scope` as **defence in depth**: scope is checked at
the tool layer *and* again at the executor, so an in-scope constraint is not
bypassable by an agent. Cleanup is always registered before execution — SIGINT,
crashes, and budget exhaustion all trigger reverse-order cleanup.

Those guardrails reduce accidents. They do **not** grant you permission. You are
still responsible for pointing the swarm only at targets you're authorized to
test, and for setting a correct scope.

## The operational guardrails

Alongside scope, three run-time controls keep autonomous runs in bounds:

- **`--safe-mode`** blocks destructive command tokens (`rm`, `DROP`, `kill`,
  `chmod`, …) before execution — required by programs that forbid risky
  automated actions.
- **`--budget <usd>`** caps per-run LLM spend and winds the run down gracefully
  when reached.
- The **killswitch** (dashboard **STOP** button, or `q` / `Ctrl-C` in the
  terminal) ends a run cleanly at any time.

See **[Cost & Safety](./cost-and-safety.md)** for how these combine to make an
unattended run safe.

## Safe places to practice

Want to see the swarm work without touching anyone else's systems? Use the
**bundled labs** (`crapi`, `juiceshop`, `vampi`, `dvga`) — intentionally
vulnerable targets that spin up locally in Docker and tear down after. See the
[Quick Start](./quickstart.md#bundled-labs).

## Reporting a vulnerability *in* Pentest Swarm AI

Found a security issue in the tool itself (not a finding it produced against a
target)? Please report it privately — do **not** open a public GitHub issue.
Open a
[GitHub Security Advisory](https://github.com/Armur-Ai/Pentest-Swarm-AI/security/advisories/new)
or see the repo's `SECURITY.md` for details.
