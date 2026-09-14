#!/usr/bin/env bash
# Contrato Director: partes {slug}_NNNN.zip -> UNA carpeta {slug}/
set -euo pipefail
ROOT="${1:-Download code/archivos}"
test -d "$ROOT"
mapfile -t bases < <(find "$ROOT" -maxdepth 1 -type f -name '*_0001.zip' | sed 's/_0001\.zip$//' | sort)
if [ "${#bases[@]}" -eq 0 ]; then echo "ERROR: no *_0001.zip in $ROOT"; exit 1; fi
for repo in "${bases[@]}"; do
  name="$(basename "$repo")"
  dest="$ROOT/$name"
  echo "GROUP $name DEST $dest"
  rm -rf "$dest"
  mkdir -p "$dest"
  shopt -s nullglob
  parts=("$ROOT/${name}"_*.zip)
  [ "${#parts[@]}" -gt 0 ] || { echo FAIL no parts; exit 1; }
  IFS=$'\n' parts_sorted=($(printf '%s\n' "${parts[@]}" | sort))
  for zip in "${parts_sorted[@]}"; do
    echo "Testing $zip"
    unzip -tq "$zip"
    echo "Extracting $zip -> $dest"
    unzip -oq "$zip" -d "$dest"
  done
  if [ -d "$dest/$name" ]; then
    inner="$dest/.__inner_$name"
    mv "$dest/$name" "$inner"
    find "$inner" -mindepth 1 -maxdepth 1 -exec mv {} "$dest"/ \;
    rm -rf "$inner"
  fi
  count="$(find "$dest" -type f | wc -l)"
  [ "$count" -gt 0 ] || { echo FAIL zero files; exit 1; }
  echo "PASS EXTRACT $name ($count files)"
done
