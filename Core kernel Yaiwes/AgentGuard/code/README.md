# AgentGuard

[![CI](https://github.com/krishkumar/agentguard/workflows/CI/badge.svg)](https://github.com/krishkumar/agentguard/actions)
[![npm version](https://badge.fury.io/js/ai-agentguard.svg)](https://www.npmjs.com/package/ai-agentguard)
[![npm downloads](https://img.shields.io/npm/dm/ai-agentguard.svg)](https://www.npmjs.com/package/ai-agentguard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/node/v/ai-agentguard.svg)](https://nodejs.org/)

**Work safely with agents like Claude Code, Cursor, Kiro CLI.**

AI coding agents are powerful, but with great power comes `rm -rf /`.

I've been recommending tools like Claude Code and Cursor to junior devs and non-technical folks lately. These agents can execute shell commands autonomously, which is useful. But it also means a single hallucination could wipe their SSH keys, nuke a folder, or brick a meticulously created dev environment.

Frontier models do come with guardrails, but I wanted control over project-specific no-nos too - like pushing to master or running that one script that drops the staging database.

An LLM deciding whether a command is "safe" is probabilistic. I wanted something classical: a system where I define exactly what's allowed and what's blocked, with no ambiguity. 

Inspired by `.gitignore`: simple pattern matching, one rule per line, easy for anyone to read and modify.

> Built with [Kiro](https://kiro.dev) for the Kiroween Hackathon 2025

## Highlights

- Deterministic rules, not probabilistic LLM guardrails
- `.gitignore`-style syntax anyone can read
- Recursive command unwrapping (catches `sudo bash -c "rm -rf /"`)
- Catastrophic path detection (blocks `rm -rf /`, `rm -rf ~`, etc.)
- Zero latency - all validation is local

### Supported Agents

| Agent | Status | Install Command |
|-------|--------|-----------------|
| Claude Code | ✅ Supported | `agentguard install claude` |
| Cursor | ✅ Supported | `agentguard install cursor` |
| Kiro CLI | ✅ Supported | `agentguard install kiro` |
| OpenCode | ✅ Supported | `agentguard install opencode` |
| Windsurf | 🔜 Coming soon | - |

## Install

```bash
npm install -g ai-agentguard
```

Or from source:

```bash
git clone https://github.com/krishkumar/agentguard
cd agentguard
npm install && npm run build
npm link
```

## Quick Start

```bash
agentguard init           # Creates .agentguard with sensible defaults
agentguard install claude # Registers the Claude Code hook
agentguard install cursor # Registers the Cursor hook
agentguard install kiro   # Registers the Kiro CLI hook
agentguard install opencode # Registers the OpenCode plugin
```

That's it. Every shell command Claude tries to run now goes through AgentGuard first.

## What it does

AgentGuard intercepts shell commands before they execute and validates them against a simple rules file. If a command matches a block pattern, it gets stopped. If it's allowed, it runs normally.

### Recursive Command Unwrapping

AgentGuard doesn't just look at the surface command - it recursively unwraps nested command wrappers to find what's actually being executed. This catches attempts to hide dangerous commands behind innocent-looking wrappers:

```bash
# All of these get unwrapped to detect the underlying "rm" command:
sudo rm -rf /                    # → rm -rf /
bash -c "rm -rf /"               # → rm -rf /
sudo env PATH=/bin bash -c "rm -rf /"  # → rm -rf /
find / -exec rm -rf {} \;        # → rm (with dynamic args)
xargs rm -rf                     # → rm (with dynamic args)
```

**Supported wrappers:**
- **Passthrough**: `sudo`, `doas`, `env`, `nice`, `nohup`, `timeout`, `time`, `watch`, `strace`, `ltrace`, `ionice`, `chroot`, `runuser`, `su`
- **Shell -c**: `bash`, `sh`, `zsh`, `dash`, `fish`, `ksh`, `csh`, `tcsh`
- **Dynamic executors**: `xargs`, `parallel`, `find -exec`, `find -delete`

Here's what a standard block looks like in practice:

```
> run nuketown.sh

⏺ Bash(./nuketown.sh)
  ⎿  Error: PreToolUse:Bash hook error: [node ./dist/bin/claude-hook.js]: 🚫
     AgentGuard BLOCKED: ./nuketown.sh
     Rule: *nuketown*
     Reason: Blocked by rule: *nuketown*
```

The agent tried to run the command. AgentGuard caught it. Nothing bad happened.

## The rules file

You create a `.agentguard` file in your project root with patterns for commands you want to block:

```bash
# The obvious dangerous stuff
!rm -rf /
!rm -rf /*
!rm -rf ~
!rm -rf ~/*
!mkfs*
!dd if=* of=/dev/*
!shred*

# Don't let agents read my secrets
!cat ~/.ssh/*
!cat ~/.aws/*
!cat */.env

# Block that sketchy script I use for demos
!*nuketown*
```

The syntax is deliberately simple. `!` means block, `*` is a wildcard. That's basically it.

## How it works with AI Agents

### Claude Code

Claude Code has a hook system that lets you intercept tool calls before they run. AgentGuard registers a `PreToolUse` hook that receives every Bash command as JSON, validates it against your rules, and returns exit code 0 (allow) or 2 (block).

### Cursor

Cursor also supports the same `PreToolUse` hook system as Claude Code. AgentGuard registers a hook that intercepts Bash commands, validates them against your rules, and returns the appropriate exit code to allow or block execution.

### Kiro CLI

Kiro CLI also supports hooks through its agent configuration system. AgentGuard registers a `PreToolUse` hook that intercepts `execute_bash` commands, validates them against your rules, and returns the appropriate exit code.

### OpenCode

OpenCode supports plugins through its plugin system. AgentGuard creates a plugin that uses the `tool.execute.before` hook to intercept bash commands, validates them against your rules, and throws an error to block execution if needed.

## Commands

```bash
agentguard init             # Create .agentguard with sensible defaults
agentguard install claude   # Register the Claude Code hook
agentguard install cursor   # Register the Cursor hook
agentguard install kiro     # Register the Kiro CLI hook
agentguard install opencode # Register the OpenCode plugin
agentguard uninstall claude # Remove the Claude Code hook
agentguard uninstall cursor # Remove the Cursor hook
agentguard uninstall kiro   # Remove the Kiro CLI hook
agentguard uninstall opencode # Remove the OpenCode plugin
agentguard check "rm -rf /" # Test if a command would be blocked
```

## Roadmap

AgentGuard now supports Claude Code, Cursor, and Kiro CLI through their respective hook systems. Future integrations planned:

- Windsurf
- Other agentic tools as they add hook APIs

The core validation logic is agent-agnostic, so adding new integrations is mostly about figuring out each tool's interception mechanism.

## Limitations & Security Model

AgentGuard is **defense-in-depth**, not a complete sandbox.

### What AgentGuard Does

- Blocks dangerous shell commands before execution
- Scans for catastrophic paths (`/`, `~`, `/home`) anywhere in arguments
- Unwraps wrapper commands (`sudo`, `bash -c`) to find the real command
- Analyzes script contents before execution (Python, Node, Shell)
- Provides project-specific rules versioned with your code

### What AgentGuard Does NOT Do

- **Full sandboxing** - Use Docker/containers for true isolation
- **Binary inspection** - Cannot analyze compiled executables
- **Network blocking** - Does not prevent data exfiltration
- **Complete bypass prevention** - A determined attacker can work around pattern matching

### Why Use AgentGuard?

Many developers run AI agents with `--dangerously-skip-permissions` or habitually auto-accept prompts. AgentGuard catches the common footguns - accidental `rm -rf /`, leaked credentials, that one script that drops staging - even when permission prompts are bypassed.

For critical systems, combine AgentGuard with containerization. This tool handles the everyday "oh no what did it just run" moments; Docker handles the adversarial edge cases.

## References

### Official Hook Documentation

- **Claude Code**: [Hooks Documentation](https://code.claude.com/docs/en/hooks)
- **Cursor**: [Agent Hooks Documentation](https://cursor.com/docs/agent/hooks)
- **Kiro CLI**: [Hooks Documentation](https://kiro.dev/docs/cli/hooks/)

## Built with

This project was built using [Kiro](https://kiro.dev) for the Kiroween Hackathon. The rule engine, CLI, and Claude Code integration were all developed with Kiro's assistance.

---

MIT License
