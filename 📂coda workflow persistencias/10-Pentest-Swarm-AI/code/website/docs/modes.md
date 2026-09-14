---
sidebar_position: 4
title: Scan Modes
---

# Scan Modes

A **mode** tells the swarm what kind of engagement you're running. It shapes the
**objective** the agents pursue (recon, exploitation, and reporting all follow
the objective), and for ASM it also switches off active exploitation so the run
stays a pure surface map.

Pick one in the interactive launcher (`pentestswarm run` → **Scan mode**) or with
`--mode` on `scan`:

```bash
pentestswarm scan example.com --scope example.com --mode bugbounty --swarm
```

## The modes

| Mode | What it does | Use it when |
|------|--------------|-------------|
| **`manual`** (default) | General pentest — find and prove all vulnerabilities across the surface. | You want broad coverage of a target. |
| **`bugbounty`** | Steers toward **reportable** findings: prove exploitability with evidence, prioritize by severity, and avoid duplicates. | You're hunting on a bug-bounty program and need submission-ready results. |
| **`ctf`** | Goal-driven: gain an **initial foothold → escalate privileges → capture flags** (`flag{...}`, user & root flags). | You're solving a CTF box or a boot-to-root challenge. |
| **`asm`** | **Attack-surface mapping only** — enumerate hosts, endpoints, technologies and exposures, with **active exploitation turned off**. | You want a non-intrusive inventory / continuous monitoring of what's exposed. |

## How a mode changes the run

- **Objective steering.** Each mode sets a default objective the swarm pursues
  (for example, CTF mode pursues foothold → privesc → flags). Because the whole
  swarm — recon, classification, exploitation, reporting — is guided by the
  objective, the mode meaningfully changes what the agents go after.
- **ASM is recon-only.** `asm` turns off the active attack tools (the
  dalfox / sqlmap / nikto / ffuf class of probes) so it maps the surface without
  exploiting anything. It's the safe choice for inventory and monitoring.

## Overriding the objective

A mode only fills in the **default** objective. If you pass your own
`--objective`, it always wins — the mode's other behavior (like ASM's
recon-only toggle) still applies:

```bash
# custom objective, still recon-only because of asm
pentestswarm scan example.com --scope example.com --mode asm \
  --objective "inventory all subdomains and exposed admin panels"
```

You can also force active scanning back on in ASM if you really want it:

```bash
pentestswarm scan example.com --scope example.com --mode asm --active-scan=true
```

:::tip
Not sure which to pick? `manual` is the right default for most targets. Reach
for `bugbounty` when you need clean, deduped, severity-ranked results to submit,
`ctf` for capture-the-flag boxes, and `asm` when you must not touch the target.
:::
