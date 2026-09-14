---
inclusion: always
---

# Security Policies

## Core Philosophy
This is a security tool. Every decision should prioritize safety over convenience.

## Fail-Safe Design
- When uncertain, BLOCK the command
- Default deny, explicit allow
- No network calls during validation (can't be intercepted/spoofed)
- All validation happens locally

## Rule Precedence
1. Explicit blocks (`!pattern`) take highest priority
2. Explicit allows (`+pattern`) override default behavior
3. More specific patterns override less specific ones
4. First matching rule wins within same specificity

## Input Handling
- Never trust command input blindly
- Handle shell escaping properly
- Consider command chaining (`&&`, `||`, `;`)
- Handle pipes and redirects

## Audit Trail
- Log every decision (allow/block)
- Include timestamp, command, matching rule
- Never log sensitive data (passwords, tokens)

## Hook Security
- Hook receives JSON from Claude Code - validate structure
- Exit codes are the only communication channel (0=allow, 2=block)
- Don't leak information in error messages to the agent
