#!/bin/bash
# diag_ram.sh — Muestrea RAM cada 10s durante 5 min
PID=$(pgrep -f conector_chat | head -1)
echo "=== DIAGNOSTICO RAM - Orquestador PID $PID ==="
echo "Time | RSS (MB) | VmSize (MB) | Threads | FDs | Status"
for i in $(seq 1 30); do
    if [ -z "$PID" ] || ! kill -0 "$PID" 2>/dev/null; then
        PID=$(pgrep -f conector_chat | head -1)
        if [ -z "$PID" ]; then
            echo "$(date +%H:%M:%S) | PROCESO MUERTO"
            sleep 10
            continue
        fi
    fi
    RSS=$(ps -o rss= -p "$PID" 2>/dev/null | tr -d ' ')
    VSZ=$(ps -o vsz= -p "$PID" 2>/dev/null | tr -d ' ')
    THR=$(ls /proc/$PID/task/ 2>/dev/null | wc -l)
    FDS=$(ls /proc/$PID/fd/ 2>/dev/null | wc -l)
    ST=$(cat /proc/$PID/status 2>/dev/null | grep ^State | awk '{print $2}')
    echo "$(date +%H:%M:%S) | $(($RSS/1024)) MB | $(($VSZ/1024)) MB | $THR | $FDS | $ST"
    sleep 10
done
echo "=== FIN ==="
