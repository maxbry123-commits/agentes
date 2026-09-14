# 🔴 Autonomous Pentest Agent

A Claude-powered autonomous penetration testing framework that executes the full offensive security kill chain — from reconnaissance to root — against HackTheBox machines.

## Overview

This prototype combines two cybersecurity use cases into a single cohesive system:
1. **Autonomous CTF Solving** — Claude reasons through challenges with clear success criteria (flags)
2. **Automated Penetration Testing** — Full kill chain state machine: Recon → Enumeration → Exploitation → Privilege Escalation

Each phase is driven by a specialized Claude agent with phase-appropriate system prompts, tool access, and success criteria. A central orchestrator manages state transitions, context accumulation, and reporting.

## Architecture

```
┌───────────────���──────────────────────────────────────┐
│                 PHASE ORCHESTRATOR                    │
│   Kill chain state machine with phase transitions    │
└──────────────────────┬───────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐────────────┐
        ▼              ▼              ▼            ▼
   ┌─────────┐   ┌──────────┐   ┌─────────┐  ┌─────────┐
   │  RECON  │   │  ENUM    │   │ EXPLOIT │  │ PRIVESC │
   │  Agent  │   │  Agent   │   │  Agent  │  │  Agent  │
   └────┬────┘   └────┬─────┘   └────┬────┘  └────┬────┘
        │              │              │            │
        └──────────────┼──────────────┘────────────┘
                       ▼
              ┌─────────────────┐
              │  TOOL EXECUTOR  │  Sandboxed command runner
              │  Safety checks  │  Timeout enforcement
              │  Audit logging  │  Blocklist / confirmation
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ FINDINGS MEMORY │  Cross-phase context
              │ Hypothesis      │  Dead-end tracking
              │ tracking        │  Deduplication
              └────────┬────────┘
                       ▼
           ┌────────────────────┐
           │ VALIDATION ENGINE  │  Writeup-based scoring
           │ REPORT GENERATOR   │  Full attack narrative
           └────────────────────┘
```

## Key Features

- **Phase-Specialized Agents**: Each kill chain phase has a dedicated Claude agent with tailored prompts and tool access
- **Structured Reasoning**: Claude responds in structured JSON with explicit reasoning, enabling audit trails and debugging
- **Safety Guardrails**: Command blocklist, confirmation prompts, timeouts, and dry-run mode
- **Memory & Hypothesis Tracking**: Findings accumulate across phases; dead ends are tracked to prevent retry loops
- **Writeup-Based Validation**: Ground truth from published writeups enables automated scoring against known-correct attack paths
- **Multi-Machine Support**: Validated against HTB Shocker and Lame with YAML-based machine profiles

## Validated Targets

| Machine | OS | Difficulty | Key Techniques |
|---------|-----|-----------|----------------|
| **Shocker** | Linux | Easy | Shellshock (CVE-2014-6271), sudo perl privesc |
| **Lame** | Linux | Easy | Samba usermap_script (CVE-2007-2447), direct root |

## Quick Start

```bash
# Clone
git clone https://github.com/deltaRed1a/autonomous-pentest-agent.git
cd autonomous-pentest-agent

# Setup
python -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Dry run (no commands executed — validates logic + API)
python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip 10.10.14.1 --dry-run

# Live run with confirmation prompts (on Kali/Pwnbox with HTB VPN)
python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip YOUR_TUN0_IP
```

## Usage

```
python -m src.main [OPTIONS]

Required:
  --target, -t        Target IP address
  --machine, -m       Machine profile (shocker|lame)
  --attacker-ip, -a   Your IP on the HTB VPN (tun0)

Optional:
  --dry-run           Don't execute commands (test logic only)
  --no-confirm        Skip command confirmation prompts
  --max-commands      Max total commands (default: 50)
  --timeout           Per-command timeout in seconds (default: 120)
  --output-dir, -o    Report output directory (default: output/)
  --model             Anthropic model (default: claude-sonnet-4-20250514)
  --log-level         DEBUG|INFO|WARNING|ERROR (default: INFO)
```

## Project Structure

```
autonomous-pentest-agent/
├── src/
│   ├── main.py              # Entry point & CLI
│   ├── orchestrator.py      # Kill chain state machine
│   ├── state.py             # Phase/state data models
│   ├── agents/              # Phase-specific Claude agents
│   │   ├── recon.py         # Port scanning & service discovery
│   │   ├── enumeration.py   # Deep-dive service enumeration
│   │   ├── exploit.py       # Vulnerability ID & exploitation
│   │   └── privesc.py       # Privilege escalation
│   ├── tools/
│   │   └── executor.py      # Sandboxed command execution
│   ├── memory/
│   │   └── findings.py      # Cross-phase findings store
│   ├── reporting/
│   │   └── reporter.py      # Report generation
│   └── validation/
│       └── validator.py     # Writeup-based scoring
├── config/
│   ├── machines/            # Target machine profiles + ground truth
│   └── tools.yaml           # Available tool definitions
├── docs/
│   ├── design_doc.md        # Architecture & design decisions
│   └── final_report.md      # Results & analysis
├── tests/                   # Unit tests
├── requirements.txt
└── .env.example
```

## Technology Stack

- **Claude claude-sonnet-4-20250514** (Anthropic SDK) — Reasoning engine for all phase agents
- **Python 3.12+** — Framework and orchestration
- **Rich** — Terminal UI for live demo output
- **PyYAML** — Machine configs and ground truth
- **Pydantic** — Data validation
- **pytest** — Testing

## Safety & Ethics

This tool is designed for **authorized penetration testing only** against systems you have explicit permission to test (e.g., HackTheBox lab machines). The tool executor includes:
- Blocked command patterns (destructive operations)
- Optional confirmation prompts for every command
- Dry-run mode for safe testing
- Full audit logging of all commands and outputs
```
