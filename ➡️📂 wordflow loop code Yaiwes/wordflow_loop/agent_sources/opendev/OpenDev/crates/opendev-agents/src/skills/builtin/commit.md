---
name: commit
description: "Use when creating git commits. Guides conventional commit format, message quality, and staging best practices."
---

# Git Commit

## Overview
This skill provides guidance for creating high-quality git commits using conventional commit format.

## When to Use This Skill
- When the user asks to commit changes
- When creating commits as part of a workflow
- When the user references /commit

## Instructions

### Step 1: Review Changes
Run `git status` and `git diff --staged` to understand what will be committed.
If nothing is staged, identify which files should be added.

### Step 2: Stage Appropriate Files
- Prefer staging specific files by name rather than `git add -A`
- Never stage sensitive files (.env, credentials, API keys)
- Never stage large binary files unless explicitly requested

### Step 3: Write the Commit Message
Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code restructuring
- `docs:` for documentation changes
- `test:` for test additions/changes
- `chore:` for maintenance tasks

The message should:
- Be concise (under 72 characters for the subject line)
- Focus on "why" not "what"
- Use imperative mood ("Add feature" not "Added feature")

### Step 4: Create the Commit
Use a heredoc for multi-line messages to preserve formatting.

## Common Mistakes
- Committing all files without reviewing what changed
- Writing vague messages like "fix stuff" or "update code"
- Including sensitive files in the commit
- Amending previous commits when a new commit is more appropriate
