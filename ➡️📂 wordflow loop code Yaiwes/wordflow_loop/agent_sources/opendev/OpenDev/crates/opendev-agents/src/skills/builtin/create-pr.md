---
name: create-pr
description: "Use when creating GitHub pull requests. Guides branch setup, PR description writing, and submission."
---

# Create Pull Request

## Overview
This skill provides guidance for creating well-structured GitHub pull requests.

## When to Use This Skill
- When the user asks to create a PR
- When the user references /create-pr
- When pushing changes and opening a pull request

## Instructions

### Step 1: Verify Branch State
- Ensure you are on a feature branch, not main/master
- Check that all changes are committed
- Verify the branch is pushed to the remote

### Step 2: Understand the Changes
- Run `git log main..HEAD` to see all commits
- Run `git diff main...HEAD` to see the full diff
- Identify the overall purpose of the changes

### Step 3: Write the PR Description
Use this format:
```
## Summary
- 1-3 bullet points describing the changes

## Test plan
- [ ] How to verify the changes work
```

### Step 4: Create the PR
- Use `gh pr create` with appropriate title and body
- Keep the title under 70 characters
- Use the body for details, not the title
- Set appropriate labels and reviewers if requested

## Common Mistakes
- Creating PRs against the wrong base branch
- Writing vague titles like "Fix bug" or "Update code"
- Forgetting to push the branch before creating the PR
- Not including a test plan
