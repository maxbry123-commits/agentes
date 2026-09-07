# Claude Chat ↔ GitHub MCP acceptance tests

Branch: `claude-mcp-write-test` only.

Goal: verify that Claude Chat (not Claude Code) can read, create, edit and delete GitHub content through a remote MCP connector.

Required test sequence:
1. Read `EDIT_ME.md`.
2. Replace its marker with `CLAUDE_EDIT_PASS` plus a UTC timestamp.
3. Create `CREATE_ME_RESULT.md` with `CLAUDE_CREATE_PASS` plus a UTC timestamp.
4. Delete `DELETE_ME.md`.
5. Do not modify `main` during connector validation.

Acceptance: all changes appear as commits on this branch and are independently verifiable in GitHub.
