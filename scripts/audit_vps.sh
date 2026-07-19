#!/bin/bash
# audit_vps.sh — Auditoría completa de estabilidad
echo "=========================================="
echo "FASE 1: INVENTARIO COMPLETO DE PROCESOS"
echo "=========================================="
echo ""
echo "--- TODOS LOS PROCESOS (con padre, usuario, puerto) ---"
ps -eo pid,ppid,user,etime,%mem,%cpu,rss,vsz,stat,comm --sort=-rss
echo ""
echo "--- PUERTOS EN USO ---"
ss -tlnpu 2>/dev/null | head -30
echo ""
echo "--- ÁRBOL DE PROCESOS (pstree) ---"
pstree -p 2>/dev/null | head -50
echo ""
echo "--- PROCESOS CON FD ABIERTOS > 50 ---"
for p in $(pgrep -v $PPID); do
    cnt=$(ls /proc/$p/fd 2>/dev/null | wc -l)
    if [ "$cnt" -gt "50" ]; then
        name=$(cat /proc/$p/comm 2>/dev/null)
        echo "PID $p ($name): $cnt fds"
    fi
done
echo ""
echo "=========================================="
echo "FASE 2: RECURSOS ACTUALES"
echo "=========================================="
echo ""
echo "--- MEMORIA ---"
free -h
echo ""
echo "--- SWAP ---"
swapon --show 2>/dev/null || echo "No swap"
echo ""
echo "--- DISCO ---"
df -h
echo ""
echo "--- LOAD AVERAGE ---"
uptime
echo ""
echo "--- RED (conexiones activas) ---"
ss -s
echo ""
echo "--- TOP 10 CONEXIONES ESTABLECIDAS ---"
ss -tn state established 2>/dev/null | head -11
echo ""
echo "=========================================="
echo "FASE 11: KERNEL - OOM y SYSLOG"
echo "=========================================="
echo ""
echo "--- OOM KILLER (últimos eventos) ---"
dmesg 2>/dev/null | grep -i -E "(oom|killed|memory)" | tail -20
echo ""
echo "--- JOURNALCTL OOM (últimas 2h) ---"
journalctl --since "2 hours ago" 2>/dev/null | grep -i -E "(oom|killed|memory)" | tail -20
echo ""
echo "--- SYSLOG (errores memoria) ---"
grep -i -E "(oom|killed|out of memory)" /var/log/syslog 2>/dev/null | tail -20
echo ""
echo "=========================================="
echo "FASE 10: DOCKER"
echo "=========================================="
echo ""
echo "--- CONTENEDORES ---"
docker ps -a 2>/dev/null || echo "Docker no accesible"
echo ""
echo "--- DOCKER STATS (snapshot) ---"
docker stats --no-stream 2>/dev/null || echo "No stats"
echo ""
echo "--- DOCKER LOGS (errores recientes) ---"
docker ps --format "{{.Names}}" 2>/dev/null | while read c; do
    echo "--- $c ---"
    docker logs --tail 10 "$c" 2>&1 | grep -i -E "(error|oom|killed|restart)" | head -5
done
