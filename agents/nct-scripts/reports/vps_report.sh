#!/bin/bash
# vps_report.sh — Reporte HTML del estado del VPS
cat > /opt/nct/reports/vps_status.html <<'HTML'
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>NCT VPS Report</title>
<style>body{background:#000;color:#fff;font-family:monospace;padding:20px}
h1{color:#2563eb}h2{color:#fff;border-bottom:1px solid #2563eb}
.ok{color:#0f0}.fail{color:#f55}</style></head><body>
HTML
echo "<h1>NCT VPS Status Report</h1>" >> /opt/nct/reports/vps_status.html
echo "<p>Generated: $(date -u +%FT%TZ) UTC</p>" >> /opt/nct/reports/vps_status.html

echo "<h2>Servicios</h2><ul>" >> /opt/nct/reports/vps_status.html
for s in ssh openclaw litellm fail2ban; do
    st=$(systemctl is-active $s 2>/dev/null)
    if [ "$st" = "active" ]; then
        echo "<li class=ok>$s: OK</li>" >> /opt/nct/reports/vps_status.html
    else
        echo "<li class=fail>$s: FAIL ($st)</li>" >> /opt/nct/reports/vps_status.html
    fi
done
echo "</ul>" >> /opt/nct/reports/vps_status.html

echo "<h2>Repos</h2><p>Total: $(ls -d /opt/nct/repos/*/ 2>/dev/null | grep -vE '/(repos_index|repos_inventory)' | wc -l)</p>" >> /opt/nct/reports/vps_status.html

echo "<h2>Skill Router</h2>" >> /opt/nct/reports/vps_status.html
echo "<p>Registry: $([ -f /opt/nct/skills/registry/skill_registry.json ] && echo 'OK' || echo 'FAIL')</p>" >> /opt/nct/reports/vps_status.html

echo "</body></html>" >> /opt/nct/reports/vps_status.html
echo "[report] /opt/nct/reports/vps_status.html"
