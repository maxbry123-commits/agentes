#!/bin/bash
# Backup del arbol /opt/nct/memory
TS=$(date -u +%Y%m%d-%H%M%S)
DEST=/opt/nct/backups/memory-$TS.tar.gz
tar -czf "$DEST" -C /opt/nct memory 2>&1
ls -la "$DEST"
