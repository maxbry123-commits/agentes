---
inclusion: fileMatch
fileMatchPattern: "**/*.ts"
---

# TypeScript Standards

## Type Safety
- Strict mode enabled - no `any` types unless absolutely necessary
- Prefer `unknown` over `any` for unknown types
- Use discriminated unions for state management
- Export types from `types.ts`

## Patterns
- Pure functions where possible
- No side effects in validation logic
- Dependency injection for testability
- Early returns over nested conditionals

## Error Handling
- Use typed errors with specific error classes
- Never swallow errors silently
- Log errors with context for debugging
- Fail-safe: when in doubt, block the command

## Naming
- `camelCase` for functions and variables
- `PascalCase` for types, interfaces, classes
- `SCREAMING_SNAKE_CASE` for constants
- Descriptive names over abbreviations

## Imports
- Use ES module imports
- Group imports: external, internal, types
- Avoid circular dependencies
