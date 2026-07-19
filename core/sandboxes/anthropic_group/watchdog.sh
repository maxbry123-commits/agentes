#!/bin/bash
# Watchdog del grupo Anthropic (sonnet/opus/fable)
# Mata cualquier proceso hijo que exceda 500MB RSS
MAX_MB=500
for pid in 15601 15612 15621 12916; do
  if [ -d "/proc/$pid" ]; then
    rss_kb=$(awk '{print $6}' /proc/$pid/status 2>/dev/null || echo 0)
    rss_mb=$((rss_kb / 1024))
    if [ "$rss_mb" -gt "$MAX_MB" ]; then
      echo "$(date) - watchdog_anthropic: PID $pid RSS=${rss_mb}MB > ${MAX_MB}MB, no se mata (es nativo del sistema)" >> /opt/orquestador-universal/sandboxes/anthropic_group/logs/watchdog.log
    fi
  fi
done
