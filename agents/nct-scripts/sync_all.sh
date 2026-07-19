#!/bin/bash
# Sincroniza todos los repos
set +e
for r in /opt/nct/repos/*/; do
  if [ -d "$r/.git" ]; then
    cd "$r"
    name=$(basename "$r")
    echo "=== $name ==="
    git fetch --all 2>&1 | tail -1
    git pull 2>&1 | tail -1
  fi
done
