#!/bin/bash
# Auditoria completa del VPS
echo "=== AUDIT $(date -u +%FT%TZ) ==="
echo "[hostname]"; hostname
echo "[ip]"; hostname -I | tr -d ' \n'; echo
echo "[uptime]"; uptime
echo "[services]"; systemctl list-units --type=service --state=running --no-pager | head -20
echo "[disk]"; df -h
echo "[mem]"; free -h
echo "[repos]"; ls /opt/nct/repos/
echo "[github]"; ssh -T -o BatchMode=yes git@github.com 2>&1 | head -1
