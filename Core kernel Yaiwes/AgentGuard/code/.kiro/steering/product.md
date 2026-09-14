---
inclusion: always
---

# Product Overview

AgentGuard is a command-line security tool that protects systems from dangerous commands executed by AI coding agents.

## Problem

AI coding agents like Claude Code and Cursor can execute shell commands autonomously. A single hallucination could wipe SSH keys, nuke a folder, or brick a dev environment. Frontier models have guardrails, but they're probabilistic—I wanted something deterministic.

## Solution

A `.gitignore`-style rules file that defines exactly what commands are allowed or blocked. Simple pattern matching, one rule per line, easy for anyone to read and modify.

## Target Users

- Developers using AI coding agents
- Teams onboarding junior developers to AI-assisted coding
- Non-technical folks learning to use coding agents

## Key Value Proposition

Deterministic security rules you control, not probabilistic LLM guardrails.
