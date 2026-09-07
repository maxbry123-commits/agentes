# Claude Chat GitHub connector plan

Target surface: Claude Chat / claude.ai / mobile (not Claude Code).

Primary route:
- Official GitHub remote MCP: https://api.githubcopilot.com/mcp/
- Auth: OAuth / Claude Github MCP Connector GitHub App
- Desired installation scope: All repositories on maxbry123-commits

Independent fallback routes:
1. Composio remote MCP: https://connect.composio.dev/mcp (managed OAuth; GitHub tools include create/update/delete file).
2. Zapier MCP for GitHub: generate a private MCP URL in Zapier; enable GitHub actions including Create or Update File, Create Branch, Delete Branch and other required write actions.
3. Pipedream MCP / GitHub integration can be used as a fourth reserve if needed; its GitHub OAuth account can execute GitHub API actions and custom code.

Credential policy:
- Do not reuse the ChatGPT/GPT connector credential in Claude.
- Primary official route should use OAuth and does not require a PAT.
- If a PAT fallback is required, create a separate fine-grained PAT dedicated to Claude and grant only the permissions required by that fallback.

Acceptance tests live in this directory and must run only on branch `claude-mcp-write-test` until validated.
