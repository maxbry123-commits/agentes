# Autonomous Pentest Agent — Design Document

## Architecture
The system is a Claude-powered autonomous penetration testing agent that models the
pentest workflow as a **kill chain state machine** with four phases: Recon → Enumeration
→ Exploitation → Privilege Escalation. Each phase is driven by a specialized Claude agent
with phase-appropriate system prompts, tool access, and success criteria.

## Key Design Decisions

**1. Phase-Based State Machine (vs. Single Monolithic Agent)**
Each kill chain phase has distinct goals, tools, and reasoning patterns. Separate agents
with focused prompts outperform a single agent trying to manage the full lifecycle.
The orchestrator handles transitions and context passing.

**2. Structured JSON Communication (vs. Free-Form Text)**
Claude responds with structured JSON containing reasoning, commands, findings, and
hypotheses. This enables reliable parsing, state updates, and audit logging while
preserving Claude's reasoning transparency.

**3. Findings Memory Store (vs. Stateless Prompts)**
A dedicated memory layer accumulates findings across phases, tracks hypotheses, and
records dead ends. This prevents the agent from repeating failed approaches and enables
cross-phase reasoning (e.g., exploit phase uses enumeration findings).

**4. Safety-First Tool Executor**
All commands pass through a sandboxed executor with: blocked command patterns (rm -rf /),
confirmation prompts for sensitive operations, per-command timeouts, and full audit logging.
Dry-run mode enables safe testing.

**5. Writeup-Based Validation**
Ground truth from published writeups is encoded in YAML configs. A validation engine
scores the agent's performance against known-correct attack paths, providing quantifiable
metrics for capability assessment.

## Technology Stack
- **Claude claude-sonnet-4-20250514** via Anthropic SDK — reasoning engine
- **Python 3.11+** — framework and tool orchestration
- **Rich** — terminal UI for demo recording
- **YAML** — machine configs and ground truth
- **subprocess** — sandboxed command execution