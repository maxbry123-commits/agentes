# Contributing to OpenSwarm

A guide for all OpenSwarm contributors.

## Branches

There are two protected branches:

- **`main`**: the stable, production-ready branch. Every merge to `main` represents a versioned release. Never commit directly to it from any branch that is not **`dev`**.
- **`dev`**: the active development branch. All feature branches merge here first. This is where work-in-progress code lives and gets tested before release.

Never commit directly to either branch. Every change, no matter how small, gets its own branch and pull request.

### Naming format

```
yourname/type/short-description
```

All lowercase, hyphens between words. Keep it short but descriptive.

| Prefix | When to use | Example |
| --- | --- | --- |
| `feat/` | New feature | `haik/feat/add-dark-mode` |
| `fix/` | Bug fix | `arnav/fix/login-crash` |
| `refactor/` | Restructuring code without changing behavior | `cire/refactor/cleanup-auth` |
| `docs/` | Documentation only | `haik/docs/update-readme` |
| `chore/` | Build scripts, CI, dependencies, tooling | `arnav/chore/update-deps` |

### Creating a branch

```bash
git checkout dev
git pull
git checkout -b yourname/feat/my-feature
```

Always branch off of the latest `dev`.

## Commits

### Format

```
[yourname] type: short description in imperative mood
```

### Examples

```
[bob] feat: add user profile page
[bob] fix: prevent crash when token expires
[bob] refactor: split auth into separate module
[bob] docs: add setup instructions to README
[bob] chore: upgrade node to v22
```

### Rules

- Start with `[name] type:` prefix (same list as branches above).
- Use imperative mood. "add" not "added", "fix" not "fixed".
- One commit = one logical unit of work.

## The Workflow

### For day-to-day development

1. **Pull latest dev**
   ```bash
   git checkout dev && git pull
   ```
2. **Create a branch**
   ```bash
   git checkout -b yourname/feat/my-feature
   ```
3. **Do your work, commit as you go**
   ```bash
   git add .
   git commit -m "[yourname] feat: whatever you did"
   ```
4. **Push your branch**
   ```bash
   git push
   ```
5. **Open a Pull Request on GitHub**
   base: `dev`, compare: `yourname/feat/my-feature`.
6. **Wait for review and approval.**
7. **The maintainer merges it into `dev`** (branches are deleted automatically after merge).

### External Contributors

1. Fork the repo (creates your own copy).
2. Clone your fork.
3. Create a branch off of `dev` and do your work (same naming conventions).
4. Push to your fork.
5. Open a Pull Request from your fork to the main repo's `dev` branch.
6. Wait for review and approval.

## Pull Requests

### Title

Use the same format as commits:

```
[yourname] feat: add dark mode toggle
[yourname] fix: resolve crash on empty input
```

### Description

Write a short explanation of what the change does and why. Two to three sentences is enough. If the change is visual, include a screenshot.

### Scope

One logical change per PR. Do not bundle unrelated work. A bug fix and a new feature should be separate PRs, even if you noticed the bug while building the feature.

## Merging

All PRs into `dev` are merged using **squash and merge**. This takes all the commits in your PR and combines them into one clean commit on `dev`. This keeps the history readable even if your branch had many small or messy commits.

Only the maintainer (i.e. Eric) merges PRs. Do not merge your own work (unless ur Eric).

### Squash and Merge

When you have a branch with, say, 5 commits:

```
feat: start building login page
fix: typo in login form
feat: add password validation
fix: forgot to import useState
feat: finish login page styling
```

**Squash and merge** takes all 5 of those and combines them into a single commit when merging the PR:

```
feat: add login page (#12)
```

So `dev` gets one clean commit instead of messy work-in-progress history. The full commit history still exists on the PR page if anyone ever needs to look at it.

**How it works:** You don't do anything special. When you click the green "Merge pull request" button on a PR, there's a dropdown arrow next to it. Pick "Squash and merge" from that dropdown. GitHub then asks you to write the final squashed commit message before confirming.

**Does it happen by default?** No. GitHub defaults to a regular merge commit. But you can change this in repo settings:

1. Go to repo **Settings > General**.
2. Scroll to **Pull Requests**.
3. Uncheck "Allow merge commits".
4. Uncheck "Allow rebase merging".
5. Keep only **"Allow squash merging"** checked.

After that, squash and merge is the only option anyone sees. No dropdown to pick from, no way to accidentally do a regular merge.

*Note: this has already been set up in our repo settings, so we're good to go. If this ever needs to be modified, call Haik.*

## Releases

When `dev` has accumulated enough changes and is stable, the maintainer merges `dev` into `main` via a PR. Every merge to `main` represents a versioned release.

### Flow

```
feature branches  ->  PR into dev  ->  test and stabilize  ->  PR from dev into main  ->  tag a release
```

### Versioning

Releases use semantic versioning:

| Change type | Version bump | Example |
| --- | --- | --- |
| Bug fixes, plus modifications or additions to existing features | Patch | `v1.0.0` -> `v1.0.1` |
| Completely new features (backwards compatible) | Minor | `v1.0.0` -> `v1.1.0` |
| Breaking changes | Major | `v1.1.0` -> `v2.0.0` |

## Quick Reference

| Action | Command |
| --- | --- |
| Update your local dev | `git checkout dev && git pull` |
| Create a new branch | `git checkout -b yourname/type/description` |
| Stage all files | `git add .` |
| Commit | `git commit -m "[yourname] type: description"` |
| Push a new branch | `git push -u origin yourname/type/description` |
| Push subsequent commits | `git push` |
| See who wrote a line | `git blame filename` |
| See commit history | `git log --oneline` |
| See your current branch | `git branch` |
| Switch to an existing branch | `git checkout branch-name` |
