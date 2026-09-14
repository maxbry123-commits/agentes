---
inclusion: always
---

# Project Structure

## Directory Layout

```
agentguard/
├── src/
│   ├── bin/                    # CLI executables
│   │   ├── agentguard.ts       # Main CLI entry point
│   │   ├── claude-hook.ts      # Claude Code PreToolUse hook
│   │   ├── bash-wrapper.ts     # Shell wrapper (future use)
│   │   └── wrappers/           # Shell wrapper scripts
│   ├── types.ts                # Core type definitions
│   ├── validator.ts            # Main validation orchestrator
│   ├── rule-engine.ts          # Rule matching and precedence
│   ├── rule-parser.ts          # Parse .agentguard files
│   ├── pattern-matcher.ts      # Glob pattern matching
│   ├── command-tokenizer.ts    # Shell command parsing
│   ├── audit-logger.ts         # Audit trail logging
│   ├── cli.ts                  # CLI implementation
│   └── index.ts                # Public API exports
├── dist/                       # Compiled output
├── .agentguard                 # Example rules file
├── .kiro/                      # Kiro steering docs
└── package.json
```

## Core Flow

```
User Command → CLI/Hook → Validator → Rule Engine → Allow/Block
                              ↓
                         Audit Logger
```

## Key Files

- `src/bin/claude-hook.ts` - Integration point for Claude Code
- `src/validator.ts` - Orchestrates the validation pipeline
- `src/rule-engine.ts` - Core matching logic
- `.agentguard` - User-defined rules file
