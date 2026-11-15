---
sidebar_position: 6
title: Cline + Soul Spec
description: Give Cline a persistent AI persona using Soul Spec.
---

# Cline + Soul Spec

[Cline](https://github.com/cline/cline) is an open-source AI coding agent for VS Code. It supports custom instructions via `.clinerules/` directory, where Cline automatically loads all `.md` rule files.

Soul Spec gives Cline a real persona. Install a soul, and the rule files are automatically written to `.clinerules/`, giving your agent a consistent identity.

## Quick Start (2 minutes)

### Step 1: Install the CLI

```bash
npm install -g clawsouls
```

### Step 2: Install a soul

```bash
clawsouls install TomLeeLive/brad --use cline
```

This automatically creates `.clinerules/clawsouls-soul.md`, `.clinerules/clawsouls-identity.md`, `.clinerules/clawsouls-style.md`, and `.clinerules/clawsouls-agents.md` in your project.

### Step 3: Reload Cline

In VS Code, reload the Cline extension:
- Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
- Run "Developer: Reload Window"

Cline will read the rule files from `.clinerules/` and adopt the persona.

## Rule Files Structure

After installation, your project will have:

```
my-project/
├── .clinerules/
│   ├── clawsouls-soul.md      ← Personality & tone
│   ├── clawsouls-identity.md  ← Agent identity
│   ├── clawsouls-style.md     ← Communication style
│   ├── clawsouls-agents.md    ← Workflow rules
│   └── ...                     (other rules)
├── src/
└── ...
```

Cline auto-discovers and loads all `.md` files in `.clinerules/`. You can also add project-specific rules here alongside the persona files.

## Git-Friendly Setup

Commit `.clinerules/` to share personas with your team:

```bash
git add .clinerules/
git commit -m "chore: add clawsouls persona"
```

Team members will inherit the same persona when they reload Cline.

## Switching Personas

To change personas, run install again with a different soul:

```bash
clawsouls install clawsouls/ellie --use cline
```

Then reload Cline in VS Code. The `.clinerules/` files are updated automatically.

## Tips

- **Project-specific personas.** Each project gets its own `.clinerules/`.
- **Add project rules.** Create additional `.md` files in `.clinerules/` for coding standards, guidelines, etc.
- **Reload after install.** Always reload the Cline extension after running `clawsouls install --use cline`.
- **Version control.** Commit `.clinerules/` to git to ensure team consistency.

## Related Guides

- [Cursor + Soul Spec](./cursor.md)
- [Windsurf + Soul Spec](./windsurf.md)
- [Hermes Agent + Soul Spec](./hermes.md)
