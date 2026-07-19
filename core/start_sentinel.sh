#!/bin/bash
pkill -9 -f sentinel_loop 2>/dev/null
sleep 1
cd /opt/orquestador-universal
PYTHONUNBUFFERED=1 setsid nohup python3 -u -m orchestrator.sentinel_loop < /dev/null > /tmp/sentinel.log 2>&1 &
echo "SENTINEL_STARTED PID=$(pgrep -f sentinel_loop | head -1)"
