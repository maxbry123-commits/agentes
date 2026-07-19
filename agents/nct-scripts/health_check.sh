#!/bin/bash
echo "=== HEALTH CHECK $(date -u +%FT%TZ) ==="
echo "[sshd]"; systemctl is-active sshd
echo "[openclaw]"; systemctl is-active openclaw
echo "[litellm]"; systemctl is-active litellm
echo "[open-webui]"; pgrep -fa 'open-webui serve' > /dev/null && echo running || echo STOPPED
echo "[fail2ban]"; systemctl is-active fail2ban
echo "[disk]"; df -h / | tail -1
echo "[mem]"; free -h | head -2
