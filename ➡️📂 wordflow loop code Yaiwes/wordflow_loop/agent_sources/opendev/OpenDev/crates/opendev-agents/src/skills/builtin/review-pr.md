---
name: review-pr
description: "Use when reviewing pull requests. Guides thorough code review with security, correctness, and style checks."
---

# Review Pull Request

## Overview
This skill provides a structured approach to reviewing pull requests for correctness, security, and code quality.

## When to Use This Skill
- When the user asks to review a PR
- When the user references /review-pr
- When analyzing code changes for approval

## Instructions

### Step 1: Understand the Context
- Read the PR title and description
- Check which files are changed and the scope of changes
- Identify the purpose: bug fix, feature, refactor, etc.

### Step 2: Review for Correctness
- Does the code do what the PR description claims?
- Are there edge cases not handled?
- Are error paths properly managed?
- Do tests cover the changes?

### Step 3: Review for Security
- Are there any hardcoded secrets or credentials?
- Is user input properly validated and sanitized?
- Are there SQL injection, XSS, or path traversal risks?
- Are permissions and access controls correct?

### Step 4: Review for Quality
- Is the code readable and well-structured?
- Are variable and function names descriptive?
- Is there unnecessary complexity?
- Are there performance concerns?

### Step 5: Provide Feedback
- Be specific about what needs to change and why
- Distinguish between blocking issues and suggestions
- Acknowledge good patterns and improvements

## Common Mistakes
- Rubber-stamping without thorough review
- Focusing only on style while missing logic bugs
- Not testing the changes locally when feasible
- Being overly nitpicky on non-issues
