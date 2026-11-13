# ✨ Agentics Template

A template to get started with [GitHub Agentic Workflows](https://githubnext.github.io/gh-aw/).

> [!WARNING]
> GitHub Agentic Workflows are a research demonstrator. This template is for experimental use only. Use at your own risk.

## Quick Setup

To use GitHub Agentic Workflows with Copilot, you need to configure a `COPILOT_GITHUB_TOKEN`. GitHub Actions provides a default `GITHUB_TOKEN` automatically, but it doesn't have the permissions needed for Copilot features.

### Setting Up Your Copilot Token

#### Step 1: Create the Token

- [ ] Go to [GitHub Settings → Personal Access Tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
- [ ] Configure the token:
   - **Token name**: "Copilot Agentic Workflows"
   - **Resource owner**: Your user account
   - **Repository access**: Choose "Public repositories" or select specific repos
   - **Permissions**:
     - **Account permissions** → **Copilot Requests**: Access ✅ (Required)
- [ ] Click **Generate token** and copy the token value

#### Step 2: Add Token to Your Repository

- [ ] Go to your repository → **Settings** → **Secrets and variables** → **Actions**
- [ ] Click **New repository secret**
- [ ] Enter the secret name: `COPILOT_GITHUB_TOKEN`
- [ ] Paste your token value
- [ ] Click **Add secret**

That's it! Your workflows can now use Copilot.

### Additional Tokens (Advanced)

For advanced workflows, you may need additional tokens:

| Token Name | When You Need It | Required For |
|------------|------------------|--------------|
| `GH_AW_GITHUB_TOKEN` | Cross-repo operations | Accessing other repositories, remote GitHub tools |
| `GH_AW_PROJECT_GITHUB_TOKEN` | GitHub Projects v2 | Creating/updating project boards |
| `GH_AW_AGENT_TOKEN` | Agent assignments | Assigning Copilot bots to issues/PRs |

<details>
<summary><b>Creating Cross-Repository Token</b></summary>

For workflows that need to access multiple repositories:

- [ ] Go to [GitHub Settings → Personal Access Tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
- [ ] Configure the token:
   - **Token name**: "Agentic Workflows Cross-Repo"
   - **Repository access**: "All repositories" or select specific repos
   - **Permissions**:
     - **Repository permissions**:
       - **Contents**: Read (minimum) or Read+Write (for creating PRs)
       - **Issues**: Read+Write (for issue operations)
       - **Pull requests**: Read+Write (for PR operations)
- [ ] Click **Generate token** and copy the token value
- [ ] Add to repository secrets as `GH_AW_GITHUB_TOKEN`

</details>

<details>
<summary><b>Creating Projects Token</b></summary>

For workflows that manage GitHub Projects:

**For User-owned Projects:**
- Use a [Classic PAT](https://github.com/settings/tokens/new) with `project` scope
- Fine-grained PATs do **not** work with user-owned Projects

**For Organization-owned Projects:**
- [ ] Go to [GitHub Settings → Personal Access Tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
- [ ] Configure the token:
   - **Token name**: "Agentic Workflows Projects"
   - **Repository access**: Select specific repos or "All repositories"
   - **Organization permissions** (must be explicitly granted):
     - **Organization access**: Grant to the target organization
     - **Projects**: Read+Write
- [ ] Click **Generate token** and copy the token value
- [ ] Add to repository secrets as `GH_AW_PROJECT_GITHUB_TOKEN`

</details>

<details>
<summary><b>Creating Agent Assignment Token</b></summary>

For workflows that assign Copilot bots to issues or pull requests:

- [ ] Go to [GitHub Settings → Personal Access Tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
- [ ] Configure the token:
   - **Token name**: "Agentic Workflows Agent"
   - **Repository access**: Select specific repos
   - **Permissions**:
     - **Repository permissions**:
       - **Actions**: Write
       - **Contents**: Write
       - **Issues**: Write
       - **Pull requests**: Write
- [ ] Click **Generate token** and copy the token value
- [ ] Add to repository secrets as `GH_AW_AGENT_TOKEN`

</details>

## Debugging Workflows

When your agentic workflows need debugging or optimization:

- **Quick automated fixes**: Comment `/q` in any issue or PR to automatically optimize workflows
- **Interactive debugging**: In GitHub Copilot Chat, select `debug-agentic-workflow` from the agents dropdown for guided troubleshooting

See [AGENTS.md](AGENTS.md) for comprehensive debugging guides and examples.

## Learn More

- [GitHub Agentic Workflows Documentation](https://githubnext.github.io/gh-aw/)
- [Token Configuration Reference](https://github.com/githubnext/gh-aw/blob/main/docs/src/content/docs/reference/tokens.md)
