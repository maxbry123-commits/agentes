#!/bin/bash
echo "Content-Type: application/json"
echo ""
echo "{\"status\":\"ok\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"uptime_s\":$(awk '{print int($1)}' /proc/uptime),\"hostname\":\"$(hostname)\",\"load_1m\":$(uptime | grep -oE 'load average: [0-9.]+' | awk '{print $3}')}"
