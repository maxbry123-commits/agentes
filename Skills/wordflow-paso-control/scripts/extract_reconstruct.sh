#!/usr/bin/env bash
# Extrae todas las partes {slug}_NNNN.zip en UNA carpeta hermana:
#   Download code/archivos/{slug}/
# No auditar fragmentos.
set -euo pipefail
ROOT="${1:-Download code/archivos}"
test -d "$ROOT"
shopt -s nullglob
zips=("$ROOT"/*.zip)
if [ "${#zips[@]}" -eq 0 ]; then
  echo "ERROR: no ZIP files found in $ROOT"
  exit 1
fi
declare -A SLUGS=()
for zip in "${zips[@]}"; do
  base="$(basename "$zip" .zip)"
  slug="${base%_*}"
  SLUGS["$slug"]=1
done
for slug in $(printf '%s\n' "${!SLUGS[@]}" | sort); do
  dest="$ROOT/$slug"
  echo "========================================"
  echo "RECONSTRUCT SLUG: $slug"
  echo "DEST: $dest"
  echo "========================================"
  rm -rf "$dest"
  tmp="$(mktemp -d)"
  parts=("$ROOT/${slug}_"*.zip)
  if [ "${#parts[@]}" -eq 0 ]; then
    echo "FAIL: no parts for $slug"
    exit 1
  fi
  IFS=$'\n' parts_sorted=($(printf '%s\n' "${parts[@]}" | sort))
  for zip in "${parts_sorted[@]}"; do
    echo "ZIP: $zip"
    unzip -tq "$zip"
    unzip -q "$zip" -d "$tmp"
  done
  mkdir -p "$dest"
  if [ -d "$tmp/$slug" ]; then
    cp -a "$tmp/$slug"/. "$dest"/
  else
    cp -a "$tmp"/. "$dest"/
  fi
  rm -rf "$tmp"
  count="$(find "$dest" -type f | wc -l)"
  if [ "$count" -eq 0 ]; then
    echo "FAIL: $slug extracted zero files"
    exit 1
  fi
  echo "PASS EXTRACT: $slug ($count files)"
done
