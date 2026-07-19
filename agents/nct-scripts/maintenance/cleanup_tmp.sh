#!/bin/bash
# cleanup_tmp.sh — Limpieza de temporales
echo "=== Cleanup $(date -u +%FT%TZ) ==="
# Borrar /tmp/ con más de 7 días
find /tmp -type f -mtime +7 -delete 2>/dev/null
echo "tmp: OK"
# Backup del estado de servicios
systemctl is-active openclaw litellm open-webui 2>&1 > /opt/nct/reports/services_state.txt
echo "services state saved"
echo "=== FIN ==="
