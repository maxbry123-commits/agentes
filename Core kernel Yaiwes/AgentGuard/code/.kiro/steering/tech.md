---
inclusion: always
---

# Tech Stack

## Language & Runtime
- **TypeScript** - Strict mode enabled
- **Node.js 18+** - ES modules

## Build
- **tsc** - TypeScript compiler
- **npm scripts** - Build, test, dev workflows

## Testing
- **Jest** - Unit and integration tests
- **ts-jest** - TypeScript support

## Key Dependencies
- Minimal dependencies by design
- No external runtime dependencies for validation logic
- Fast startup time is critical (hook is called for every command)

## Project Structure
```
src/
├── bin/           # CLI entry points
│   ├── agentguard.ts    # Main CLI
│   └── claude-hook.ts   # Claude Code hook
├── validator.ts   # Main validation orchestrator
├── rule-engine.ts # Rule matching logic
├── pattern-matcher.ts   # Glob pattern matching
├── command-tokenizer.ts # Shell command parsing
└── cli.ts         # CLI implementation
```
