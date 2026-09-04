---
sidebar_position: 9
title: pi Coding Agent + Soul Spec
description: Use Soul Spec personas with the pi AI coding agent.
---

# pi Coding Agent + Soul Spec

[pi](https://github.com/earendil-works/pi) (by Earendil Works) is an AI coding agent that reads agent configuration from `AGENTS.md` in the current or parent directories. Soul Spec personas integrate seamlessly — install and the persona is merged into your project's `AGENTS.md`.

Soul Spec gives pi a real identity. Install a soul, and the persona is merged into your project's `AGENTS.md` inside special clawsouls markers, preserving any existing agent configuration.

## Quick Start (2 minutes)

### Step 1: Install the CLI

```bash
npm install -g clawsouls
```

### Step 2: Install a soul

```bash
clawsouls install TomLeeLive/brad --use pi
```

This automatically merges the Soul Spec persona into your project's `AGENTS.md` file. If no `AGENTS.md` exists, one is created.

### Step 3: Run pi and reload

In your pi session or shell:

```bash
/reload
```

This reloads the agent with the new persona from `AGENTS.md`.

## AGENTS.md Structure

After installation, your `AGENTS.md` contains:

```markdown
# Agent Configuration

<!-- clawsouls:start -->
# Brad — Developer

You are Brad. A pragmatic developer...

## Principles
- [Core behaviors from SOUL.md]

## Communication Style
- [Style from STYLE.md]
<!-- clawsouls:end -->

# Your Custom Sections

Any existing content outside the clawsouls markers is preserved.
```

The soul is wrapped in `<!-- clawsouls:start -->` and `<!-- clawsouls:end -->` markers. This allows you to:
- Keep existing `AGENTS.md` sections untouched
- Update the persona by running `clawsouls install` again
- Manually edit sections outside the markers

## Installation Location

The persona is merged into `AGENTS.md` at your project root:

```
my-project/
├── AGENTS.md          ← Persona merged here
├── src/
└── ...
```

pi discovers `AGENTS.md` automatically from the current directory or parent directories when you run `/reload`.

## Switching Personas

To change personas, run install again with a different soul:

```bash
clawsouls install clawsouls/surgical-coder --use pi
```

Then reload pi in your session:

```bash
/reload
```

The `AGENTS.md` is updated automatically — the clawsouls section is replaced with the new persona, and your custom sections are preserved.

## File Mapping

| Soul Spec File | Merged Into | Notes |
|---|---|---|
| `SOUL.md` | `AGENTS.md` | ✅ Personality & tone |
| `IDENTITY.md` | `AGENTS.md` | ✅ Merged into persona section |
| `STYLE.md` | `AGENTS.md` | ✅ Communication style |
| `AGENTS.md` | `AGENTS.md` | ✅ Workflow rules |
| Other files | — | ⏭️ Not merged (pi uses AGENTS.md only) |

## Version Control

Commit `AGENTS.md` to share personas with your team:

```bash
git add AGENTS.md
git commit -m "chore: update persona with clawsouls"
```

Team members will inherit the same persona when they run `/reload`.

## Directory Discovery

pi searches for `AGENTS.md` in the following order:

1. Current working directory: `./AGENTS.md`
2. Parent directories: `../AGENTS.md`, `../../AGENTS.md`, etc.
3. First match is used

This allows you to:
- **Project-level personas:** Place `AGENTS.md` at project root
- **Workspace-level personas:** Place in parent directory for multiple projects

## Tips

- **Reload after install.** Always run `/reload` after installing a new soul.
- **Preserve custom sections.** Add your own agent configuration outside the clawsouls markers.
- **Update easily.** Run `clawsouls install <owner/name> --use pi` to switch personas anytime.
- **Git-friendly.** Commit `AGENTS.md` to ensure team consistency.
- **Manual editing.** You can edit sections outside the markers without affecting persona updates.

## Editing AGENTS.md

If you need to add custom agent configuration:

1. **Add sections outside the markers:**
   ```markdown
   <!-- clawsouls:start -->
   [Auto-managed persona section]
   <!-- clawsouls:end -->
   
   ## Custom Workflow
   - My custom rules here
   - They won't be overwritten by updates
   ```

2. **Update persona:** Run `clawsouls install` again — only the clawsouls section updates.

3. **Reload:** Run `/reload` in pi.

4. **Your custom sections remain unchanged.**

## Related Guides

- [Codex + Soul Spec](./codex.md)
- [OpenClaw + Soul Spec](./openclaw.md)
- [Hermes Agent + Soul Spec](./hermes.md)
