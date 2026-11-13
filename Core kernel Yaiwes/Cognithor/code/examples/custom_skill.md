---
name: code-review
trigger_keywords: [Code-Review, Review, Codequalität, Code prüfen, Pull Request]
tools_required: [read_file, list_directory, analyze_code]
category: coding
priority: 5
description: "Performs structured code review on a file or directory"
enabled: true
---
# Code Review

## When to Apply
When the user asks for a code review, quality check, or wants feedback on
their code. Typical triggers: "Review this file", "Check the code quality",
"What can I improve in src/...".

## Prerequisites
- A file path or directory to review
- Optional: specific focus areas (security, performance, readability)

## Steps
1. **Identify target** — Ask which file or directory to review if not specified.
2. **Read the code** — Use `read_file` to load the target. For directories,
   use `list_directory` first, then read key files.
3. **Analyze** — Use `analyze_code` for automated metrics (complexity,
   duplication, style). Note any issues.
4. **Review manually** — Check for:
   - Security: injection, hardcoded credentials, path traversal
   - Performance: unnecessary loops, missing caching, N+1 queries
   - Readability: naming, function length, comments
   - Architecture: coupling, single responsibility, error handling
5. **Summarize** — Present findings grouped by severity
   (critical, warning, suggestion) with line references.

## Output Format
```
## Code Review: {filename}

### Critical
- Line 42: SQL injection via string concatenation

### Warnings
- Line 15-30: Function too long (87 lines), consider splitting
- Line 55: Bare except clause catches SystemExit

### Suggestions
- Line 8: Consider using `pathlib.Path` instead of `os.path`
- Missing type hints on public API functions

### Metrics
- Cyclomatic complexity: 12 (moderate)
- Lines of code: 234
```

## Known Pitfalls
- Do not modify files during review — this is a read-only operation.
- For large directories, focus on the most important files first.
- Be constructive — frame suggestions positively.

## Quality Criteria
- All critical issues identified
- Specific line references provided
- Actionable suggestions (not vague "improve this")
