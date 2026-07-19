#!/bin/bash
# watchdog.sh — Reinicia servicios caidos automaticamente
set +e
LOG=/opt/nct/logs/watchdog.log
mkdir -p /opt/nct/logs

for s in openclaw litellm open-webui; do
    case $s in
        open-webui)
            pgrep -fa 'open-webui serve' > /dev/null && continue
            echo "$(date -u +%FT%TZ) open-webui DOWN, restarting..." >> $LOG
            nohup /opt/nct/apps/open-webui/venv/bin/open-webui serve --host 0.0.0.0 --port 8080 > /opt/nct/logs/open-webui.log 2>&1 &
            ;;
        *)
            st=$(systemctl is-active $s 2>/dev/null)
            if [ "$st" != "active" ]; then
                echo "$(date -u +%FT%TZ) $s DOWN ($st), restarting..." >> $LOG
                systemctl restart $s
            fi
            ;;
    esac
done
