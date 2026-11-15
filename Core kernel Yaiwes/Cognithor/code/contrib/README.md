# contrib/

Community-contributed integrations, experimental features, and third-party extensions for Cognithor.

## What belongs here

- Channel integrations not yet promoted to core (e.g., new messaging platforms)
- LLM provider adapters in early development
- Experimental tools and MCP handlers
- Community skill packs
- Utility scripts for specific workflows

## What does NOT belong here

- Core PGE components (planner, gatekeeper, executor) — these live in `src/cognithor/core/`
- Stable channel implementations — these live in `src/cognithor/channels/`
- Security-critical code — must go through core review first

## Maintenance policy

Modules in `contrib/` are **not covered by the core test suite** and carry no maintenance guarantees. They may:

- Break between versions without notice
- Have incomplete test coverage
- Depend on third-party services that change independently
- Use experimental APIs that are subject to change

Use at your own risk.

## How to contribute

1. Create a subdirectory: `contrib/your-module-name/`
2. Include a `README.md` explaining what it does, how to install, and how to use
3. Include at least basic tests in a `tests/` subdirectory
4. Add a file-level docstring to every Python file:
   ```python
   """
   CONTRIB MODULE — Community-maintained. Not covered by core CI.
   See contrib/README.md for details.
   """
   ```
5. Open a PR targeting the `main` branch

## Promotion to core

To propose a contrib module for promotion to `src/cognithor/`:

1. Open a GitHub issue with:
   - Description of the module and its value
   - Test coverage report (minimum 80% for promotion)
   - Benchmark results if performance-relevant
   - List of external dependencies added
2. A core maintainer will review architecture fit, security implications, and test quality
3. If approved, the module is moved to `src/cognithor/` and added to the core test suite

## Current modules

*No community modules yet. Be the first to contribute!*

## License

All contributions must be compatible with Cognithor's [Apache 2.0 license](../LICENSE). By submitting code to `contrib/`, you agree that your contribution is licensed under Apache 2.0.
