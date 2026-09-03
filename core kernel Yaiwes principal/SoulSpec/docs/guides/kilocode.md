---
sidebar_position: 7
title: Kilo Code + Soul Spec
description: Give Kilo Code a persistent AI persona using Soul Spec.
---

# Kilo Code + Soul Spec

[Kilo Code](https://github.com/kilocode/kilocode) is an AI coding agent that supports custom instructions via `.kilocode/rules/` directory. Soul Spec personas are compatible — install with one command and Kilo Code auto-discovers your persona.

Soul Spec gives Kilo Code a real identity. Install a soul, and the rule files are automatically placed in `.kilocode/rules/`, where Kilo Code auto-detects and loads them.

## Quick Start (2 minutes)

### Step 1: Install the CLI

```bash
npm install -g clawsouls
```

### Step 2: Install a soul

```bash
clawsouls install TomLeeLive/brad --use kilocode
```

This automatically creates `.kilocode/rules/clawsouls-soul.md`, `.kilocode/rules/clawsouls-identity.md`, `.kilocode/rules/clawsouls-style.md`, and `.kilocode/rules/clawsouls-agents.md` in your project.

### Step 3: Reload Kilo Code

Reload the Kilo Code extension:
- If using VS Code: Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) → "Developer: Reload Window"
- If using other editors: Refer to your editor's extension reload mechanism

Kilo Code will read the rule files from `.kilocode/rules/` and adopt the persona.

## Rules Directory Structure

After installation, your project will have:

```
my-project/
├── .kilocode/
│   └── rules/
│       ├── clawsouls-soul.md      ← Personality & tone
│       ├── clawsouls-identity.md  ← Agent identity
│       ├── clawsouls-style.md     ← Communication style
│       ├── clawsouls-agents.md    ← Workflow rules
│       └── ...                     (other rules)
├── src/
└── ...
```

Kilo Code auto-discovers all `.md` files in `.kilocode/rules/`. Add project-specific rules here alongside the persona files.

## Version Control

Commit `.kilocode/` to share personas with your team:

```bash
git add .kilocode/
git commit -m "chore: add clawsouls persona for kilo"
```

Team members will inherit the same persona when they reload Kilo Code.

## Switching Personas

To change personas, install a different soul:

```bash
clawsouls install clawsouls/surgical-coder --use kilocode
```

Then reload Kilo Code. The `.kilocode/rules/` files are updated automatically.

## File Mapping

| Soul Spec File | Kilo Code Location | Notes |
|---|---|---|
| `SOUL.md` | `.kilocode/rules/clawsouls-soul.md` | ✅ Personality & tone |
| `IDENTITY.md` | `.kilocode/rules/clawsouls-identity.md` | ✅ Agent identity |
| `STYLE.md` | `.kilocode/rules/clawsouls-style.md` | ✅ Communication style |
| `AGENTS.md` | `.kilocode/rules/clawsouls-agents.md` | ✅ Workflow rules |

## Tips

- **Project-specific personas.** Each project gets its own `.kilocode/rules/` structure.
- **Add custom rules.** Create additional `.md` files in `.kilocode/rules/` for coding standards or project guidelines.
- **Reload after install.** Always reload Kilo Code after running `clawsouls install --use kilocode`.
- **Git-friendly.** Commit `.kilocode/` to ensure team consistency.
- **Update easily.** Run `clawsouls install <owner/name> --use kilocode` to switch personas anytime.

## Related Guides

- [Cline + Soul Spec](./cline.md)
- [Cursor + Soul Spec](./cursor.md)
- [Windsurf + Soul Spec](./windsurf.md)
