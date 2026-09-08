# Dedicated GitHub PAT for Claude MCP B

Create a **new fine-grained personal access token**. Do not reuse GPT/automation credentials.

## Identity and repository scope

- Resource owner: `maxbry123-commits`
- Repository access: **All repositories**
- Expiration: choose a finite rotation period you are comfortable maintaining (90 days is a practical default)

## Repository permissions

For the intentionally broad capability requested for this backup MCP:

- **Administration: Read and write** — includes repository settings and permits repository deletion.
- **Contents: Read and write** — files, commits through Contents API, refs where applicable.
- **Workflows: Read and write** — required when modifying files under `.github/workflows/`.
- **Actions: Read and write** — manage/read Actions endpoints exposed through the generic GitHub API fallback.
- **Issues: Read and write**
- **Pull requests: Read and write**
- **Commit statuses: Read and write**
- **Metadata: Read-only** (GitHub grants this automatically for fine-grained PATs).

Other specialized GitHub features remain governed by their own fine-grained permission. Because this server exposes a generic `github_api` tool, add a specialized permission later only if a real call returns an `X-Accepted-GitHub-Permissions` requirement that is not in this baseline.

## Secret name

Store the PAT only in the Hugging Face Space as:

`GITHUB_PERSONAL_ACCESS_TOKEN`

Do not store this PAT as a plaintext GitHub repository variable, in code, or in Claude's prompt.

## Rotation rule

This token is dedicated to Claude MCP B. Revoking or rotating it must not affect the official Claude→GitHub OAuth connector or the existing GPT GitHub connection.
