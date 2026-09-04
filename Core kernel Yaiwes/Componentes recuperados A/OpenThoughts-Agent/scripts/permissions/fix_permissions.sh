#!/bin/bash
# fix_permissions.sh - Set safe shared-readable permissions on a directory tree
#
# Makes all files readable by everyone, writable only by owner, and preserves
# execute permissions where needed:
# - bin/ directories (scripts and binaries)
# - ELF executables (detected by file header)
# - Shell scripts with shebang
#
# SECRET FILES (keys.env, secrets.env) are ALWAYS locked to 600 and EXCLUDED from
# every read/exec/group-write pass — they are never made world- or group-readable.
# This prevents a transient world-readable window on a live secrets file during
# the chmod passes (a shared-filesystem exposure).
#
# With --group-write (-w), also grants group write (g+w) on dirs + files so a
# collaborator sharing the unix group can write outputs (e.g. eval_jobs, data).
# Secret files still stay 600 (never group-writable).
#
# Usage: ./fix_permissions.sh [--group-write|-w] /path/to/directory

set -u

GROUP_WRITE=0
TARGET_DIR=""
for arg in "$@"; do
    case "$arg" in
        --group-write|-w) GROUP_WRITE=1 ;;
        -*) echo "Unknown option: $arg"; echo "Usage: $0 [--group-write|-w] <target_directory>"; exit 1 ;;
        *)  TARGET_DIR="$arg" ;;
    esac
done

if [[ -z "${TARGET_DIR:-}" ]]; then
    echo "Usage: $0 [--group-write|-w] <target_directory>"
    echo "Example: $0 ./miniconda3"
    echo "         $0 --group-write /scratch/.../eval_jobs   # also grant group write"
    exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: '$TARGET_DIR' is not a directory"
    exit 1
fi

# Secret files: ALWAYS 600, excluded from all other passes (read/exec/group-write).
SECRET_NAMES=( keys.env secrets.env )
# find expr to EXCLUDE secrets from a -type f pass:  ! -name keys.env ! -name secrets.env
SECRET_EXCL=()
for _n in "${SECRET_NAMES[@]}"; do SECRET_EXCL+=( ! -name "$_n" ); done
# find expr to MATCH secrets for the lock step:  \( -name keys.env -o -name secrets.env \)
SECRET_MATCH=( '(' )
_first=1
for _n in "${SECRET_NAMES[@]}"; do
    [[ $_first -eq 0 ]] && SECRET_MATCH+=( -o )
    SECRET_MATCH+=( -name "$_n" ); _first=0
done
SECRET_MATCH+=( ')' )

echo "Fixing permissions for: $TARGET_DIR (group_write=$GROUP_WRITE)"

# Ensure all ancestor directories up to / are traversable (o+x).
# Without this, other users can't reach the target even if it's 755.
echo "  [0/5] Ensuring parent directories are traversable (o+x)..."
_dir="$TARGET_DIR"
while [[ "$_dir" != "/" ]]; do
    _dir="$(dirname "$_dir")"
    # Only fix dirs owned by us — don't touch system dirs
    if [[ -O "$_dir" ]]; then
        _perms=$(stat -c '%a' "$_dir" 2>/dev/null || stat -f '%Lp' "$_dir" 2>/dev/null)
        if [[ $(( 0$_perms & 0005 )) -eq 0 ]]; then
            echo "    Setting $_dir to 755 (was $_perms)"
            chmod 755 "$_dir"
        fi
    fi
done

echo "  [1/5] Setting directories to 755 (rwxr-xr-x)..."
find "$TARGET_DIR" -type d -exec chmod 755 {} +

echo "  [2/5] Setting files to 644 (rw-r--r--), excluding secret files..."
find "$TARGET_DIR" -type f "${SECRET_EXCL[@]}" -exec chmod 644 {} +

echo "  [3/5] Setting executables in bin/ to 755 (rwxr-xr-x)..."
find "$TARGET_DIR" -type f -path "*/bin/*" "${SECRET_EXCL[@]}" -exec chmod 755 {} +

echo "  [4/5] Setting ELF binaries to 755 (rwxr-xr-x)..."
# Find ELF executables by checking file header (first 4 bytes = 0x7f ELF)
find "$TARGET_DIR" -type f "${SECRET_EXCL[@]}" -exec sh -c '
    for f; do
        # Check if file starts with ELF magic bytes
        if head -c 4 "$f" 2>/dev/null | grep -q "^.ELF"; then
            chmod 755 "$f"
        fi
    done
' _ {} +

echo "  [5/5] Setting shell scripts with shebang to 755..."
# Find files starting with #! (shebang)
find "$TARGET_DIR" -type f "${SECRET_EXCL[@]}" -exec sh -c '
    for f; do
        if head -c 2 "$f" 2>/dev/null | grep -q "^#!"; then
            chmod 755 "$f"
        fi
    done
' _ {} +

if [[ $GROUP_WRITE -eq 1 ]]; then
    echo "  [6/6] Granting group write (g+w) on dirs + files (secrets excluded)..."
    find "$TARGET_DIR" -type d -exec chmod g+w {} +
    find "$TARGET_DIR" -type f "${SECRET_EXCL[@]}" -exec chmod g+w {} +
fi

# ALWAYS lock secret files to 600, LAST, so no earlier pass can leave them exposed.
echo "  [secrets] Locking ${SECRET_NAMES[*]} to 600 (owner-only)..."
find "$TARGET_DIR" -type f "${SECRET_MATCH[@]}" -exec chmod 600 {} +

echo "Done."
