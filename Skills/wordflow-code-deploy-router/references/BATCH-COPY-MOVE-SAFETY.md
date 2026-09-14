# Batch Copy + Move Safety Contract

Purpose: deterministic file operations for Luna and any execution agent. Default behavior is fail-closed, preserve source bytes, and verify before commit/push.

## Non-negotiable shell safety

```bash
set -euo pipefail
IFS=$'\n\t'
```

Rules:
- Quote every path variable: `"$SRC"`, `"$DST"`.
- Use `--` before pathname operands when the command supports it, so names beginning with `-` are not parsed as options.
- Never use `for f in $(find ...)`, `ls | ...`, or newline-only queues for arbitrary filenames.
- For generated lists, prefer NUL-delimited records (`find -print0`, `read -d ''`, `xargs -0`, `rsync --from0`).
- Reject absolute destination paths, `..` traversal, and destinations outside the declared target root.
- Preserve symlinks by default. Do not dereference a symlink that resolves outside the source root.
- If destination exists with identical SHA256: SKIP as idempotent. If SHA differs: FAIL unless an explicit overwrite gate is approved.
- Never use `rm -rf` as part of a move until destination verification has passed.

## Decision table

| Need | Preferred method | Notes |
|---|---|---|
| Small exact list, explicit mapping | Bash array + `cp --` | Best for 1-50 named files and custom destination names. |
| Recursive tree or many files | `rsync -a` | Handles dotfiles, dirs and symlinks; supports dry-run and itemized changes. |
| Matching files selected by rule | `find ... -print0` + loop/`-exec` | Safe for spaces/newlines and filenames beginning with `-`. |
| Full local tree when rsync unavailable | `tar` stream | Preserves tree including dotfiles; verify manifest after extraction. |
| Partial repo checkout before copy | `actions/checkout` sparse checkout | Reduces downloaded surface before local copy. |
| Tracked rename/move inside one repo | `git mv --` | Then verify `git status`, diff and commit. |
| Local filesystem move | `mv -T --` for one exact path | `-T` prevents accidental nesting when destination becomes a directory. |
| Cross-repo remote move | COPY -> VERIFY -> COMMIT/PUSH DEST -> DELETE SOURCE -> COMMIT/PUSH SOURCE | There is no single atomic cross-repo move. |
| Few remote text files through API | Contents API create/update then delete | Operations must be serial; update uses current blob SHA. |

## Method A — controlled queue + cp

Use when the set is explicitly known and mapping may change the destination path.

```bash
SRC_ROOT="source"
DST_ROOT="target"
mkdir -p -- "$DST_ROOT"

QUEUE=(
  "README.md|README.md"
  "src/app.py|src/app.py"
  "config/settings.yaml|config/settings.yaml"
)

for entry in "${QUEUE[@]}"; do
  src_rel=${entry%%|*}
  dst_rel=${entry#*|}
  src="$SRC_ROOT/$src_rel"
  dst="$DST_ROOT/$dst_rel"

  test -f "$src" || { echo "MISSING_SOURCE $src"; exit 1; }
  mkdir -p -- "$(dirname -- "$dst")"

  if test -e "$dst"; then
    src_sha=$(sha256sum -- "$src" | awk '{print $1}')
    dst_sha=$(sha256sum -- "$dst" | awk '{print $1}')
    test "$src_sha" = "$dst_sha" && { echo "SKIP_IDENTICAL $dst"; continue; }
    test "${OVERWRITE:-0}" = 1 || { echo "COLLISION $dst"; exit 1; }
  fi

  cp -- "$src" "$dst"
  test "$(sha256sum -- "$src" | awk '{print $1}')" = "$(sha256sum -- "$dst" | awk '{print $1}')" || exit 1
done
```

For executable bits or symlinks that must be preserved, use `cp -a --` rather than plain `cp`.

## Method B — find + NUL-safe copy

Use for rule-selected files.

```bash
SRC_ROOT="source"
DST_ROOT="target"

while IFS= read -r -d '' src; do
  rel=${src#"$SRC_ROOT"/}
  dst="$DST_ROOT/$rel"
  mkdir -p -- "$(dirname -- "$dst")"
  cp -a -- "$src" "$dst"
done < <(find "$SRC_ROOT" -type f -print0)
```

For a flat destination and no per-file mapping:

```bash
find "$SRC_ROOT" -type f -name '*.py' -exec cp -t "$DST_ROOT" -- {} +
```

## Method C — rsync tree copy

Preferred for larger trees.

Preflight only:

```bash
rsync -ain --checksum -- "$SRC_ROOT/" "$DST_ROOT/"
```

Real copy:

```bash
rsync -ai --checksum -- "$SRC_ROOT/" "$DST_ROOT/"
```

Do not add `--delete` unless the declared operation is an exact mirror and deletion was explicitly approved.

For a manifest-selected set, use `--files-from`; when arbitrary filenames are possible, build the list NUL-delimited and use `--from0`.

## Method D — tar stream fallback

Use when copying a full local tree and `rsync` is unavailable.

```bash
mkdir -p -- "$DST_ROOT"
tar -C "$SRC_ROOT" -cf - . | tar -C "$DST_ROOT" -xf -
```

This includes dotfiles because `.` is archived, unlike shell glob `*`.

## Method E — sparse checkout before copy

Use GitHub Actions checkout with explicit `repository`, `path`, and a destination-scoped token for a private secondary repository. Limit the source surface with sparse checkout when only a subset is needed.

Example shape:

```yaml
- uses: actions/checkout@v7
  with:
    path: source

- uses: actions/checkout@v7
  with:
    repository: OWNER/TARGET
    token: ${{ secrets.TARGET_REPO_TOKEN }}
    path: target
```

For a secondary private repository, do not assume `${{ github.token }}` can access it.

## Moving files safely

### Same repository, tracked file

```bash
git mv -- "old/path/file.py" "new/path/file.py"
git status --short
git diff --cached --check
```

If destination directories do not exist, create them first.

### Local filesystem, one exact path

```bash
mkdir -p -- "$(dirname -- "$DST")"
mv -T -- "$SRC" "$DST"
```

Use `-T` when available to prevent a race/ambiguity where an existing destination directory causes the source to be nested unexpectedly.

### Cross-filesystem or high-assurance move

Treat as copy + verify + delete:

```bash
cp -a -- "$SRC" "$DST_TMP"
# Verify type, size, symlink target or SHA256 as applicable.
mv -T -- "$DST_TMP" "$DST"
rm -- "$SRC"
```

For a directory tree, use `rsync -a` to a staging directory, verify the complete manifest, atomically rename staging into place when possible, and only then remove source.

### Cross-repository Git move

A cross-repo move is never one blind `mv`:
1. Checkout source and destination side by side.
2. Copy using one of Methods A-D.
3. Verify destination count + SHA256/type manifest.
4. Commit and push destination.
5. Confirm destination commit exists remotely.
6. Delete source paths.
7. Commit and push source deletion.
8. Record both commit SHAs in evidence.

If any step before 5 fails, source stays untouched.

### GitHub Contents API move

The API has create/update and delete operations, not a single move operation. Execute serially:
1. GET source and capture content/blob SHA.
2. PUT destination with the exact source content.
3. GET destination and verify bytes/content hash.
4. DELETE source using its current SHA.
5. Never run PUT destination and DELETE source in parallel.

For many files, binaries, symlinks, or full trees, prefer checkout + Git instead of the Contents API.

## Manifest and verification gate

Before the operation, generate an expected manifest sorted deterministically. At minimum record:
- `src_rel`
- `dst_rel`
- type (`file`, `symlink`, `dir` when needed)
- size
- SHA256 for regular files
- symlink target for symlinks

After operation:
- Expected count == destination count for the declared scope.
- Every regular file SHA256 matches.
- Every symlink target matches and remains inside policy.
- No unexpected destination files were created in the declared scope.
- `git diff --check` passes.
- `git status --short` is reviewed before `git add`.

Only after these checks may the agent commit/push or declare the batch complete.

## Luna / agent anti-error rules

1. First classify operation as COPY, MOVE_SAME_REPO, MOVE_CROSS_REPO, MIRROR, or API_TRANSFER.
2. Choose exactly one primary method from the decision table; fallback only when a capability is unavailable.
3. Run dry-run when the selected tool supports it (`rsync -n`, manifest preview, or Git diff preview).
4. Never infer destination by string concatenation without validating the resulting path is under `DST_ROOT`.
5. Never overwrite a different destination silently.
6. Never delete source before destination verification and, for cross-repo operations, remote push verification.
7. Never use `GITHUB_TOKEN` as proof of cross-repo write access.
8. Never expose token values in logs, files, URLs, commit messages, or evidence.
9. A failed hash/count/path gate means FAIL and preserve source.
10. LLM text is not evidence. Evidence = command exit status + manifest + hash/type checks + Git commit SHA when applicable.
