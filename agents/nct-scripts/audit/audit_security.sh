#!/bin/bash
# audit_security.sh — Auditoría de seguridad
echo "=== Audit Security $(date -u +%FT%TZ) ==="
echo
echo "--- fail2ban ---"
systemctl is-active fail2ban
echo
echo "--- ssh config ---"
grep -E "^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|Port)" /etc/ssh/sshd_config 2>/dev/null | head -10
echo
echo "--- secretos con permisos 600 ---"
INCORRECTOS=$(find /opt/nct/secrets -type f ! -perm 600 2>/dev/null | wc -l)
echo "  archivos con permisos != 600: $INCORRECTOS"
echo
echo "--- keys en logs (debe ser 0) ---"
LOGS_LEAKS=$(grep -rE "csk-[a-z0-9]{30,}|gsk_[a-zA-Z0-9]{30,}" /var/log/ /opt/nct/logs/ 2>/dev/null | wc -l)
echo "  keys filtradas en logs: $LOGS_LEAKS"
echo
echo "=== FIN ==="
