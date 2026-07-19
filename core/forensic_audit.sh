#!/bin/bash
echo "==================================================="
echo "FASE 1: IDENTIFICAR PROCESO SOSPECHOSO"
echo "==================================================="
# El sospechoso: orquestador (conector_chat) o python3 con RSS alta
echo "--- TOP 10 PROCESOS POR RSS ---"
ps -eo pid,ppid,user,etime,%mem,%cpu,rss,vsz,comm --sort=-rss | head -10
echo ""
# Detalles del proceso principal sospechoso
PID=$(pgrep -f conector_chat | head -1)
if [ -z "$PID" ]; then
    # buscar python3 con mayor RAM
    PID=$(ps -eo pid,comm --sort=-rss | grep python3 | head -1 | awk '{print $1}')
fi
echo "--- PROCESO OBJETIVO: PID $PID ---"
if [ -d "/proc/$PID" ]; then
    echo "CMD:"
    cat /proc/$PID/cmdline | tr '\0' ' '; echo
    echo "CWD:"
    readlink /proc/$PID/cwd
    echo "EXE:"
    readlink /proc/$PID/exe
    echo "STATUS:"
    head -20 /proc/$PID/status
    echo "PPID:"
    cat /proc/$PID/status | grep PPid
    echo "PUERTO:"
    ss -tlnp 2>/dev/null | grep $PID
fi
echo ""
echo "==================================================="
echo "FASE 6: THREADS DEL PROCESO OBJETIVO"
echo "==================================================="
if [ -d "/proc/$PID/task" ]; then
    echo "Total threads: $(ls /proc/$PID/task/ | wc -l)"
    echo "--- DETALLES POR THREAD (top 20) ---"
    for t in $(ls /proc/$PID/task/ 2>/dev/null | head -20); do
        if [ -f "/proc/$PID/task/$t/status" ]; then
            name=$(grep "^Name:" /proc/$PID/task/$t/status | awk '{print $2}')
            state=$(grep "^State:" /proc/$PID/task/$t/status | awk '{print $2}')
            vms=$(grep "^VmSize:" /proc/$PID/task/$t/status | awk '{print $2}')
            rss=$(grep "^VmRSS:" /proc/$PID/task/$t/status | awk '{print $2}')
            echo "  TID $t ($name) state=$state vms=${vms}kB rss=${rss}kB"
        fi
    done
fi
echo ""
echo "==================================================="
echo "FASE 5: SOCKETS ABIERTOS POR EL PROCESO"
echo "==================================================="
if [ -d "/proc/$PID/net" ]; then
    cat /proc/$PID/net/tcp 2>/dev/null | head -10
fi
echo ""
echo "FDs ABIERTOS:"
ls -la /proc/$PID/fd/ 2>/dev/null | head -30
echo "Total FDs: $(ls /proc/$PID/fd/ 2>/dev/null | wc -l)"
echo ""
echo "==================================================="
echo "FASE 7: MEMORIA DETALLADA (/proc/PID/smaps)"
echo "==================================================="
if [ -f "/proc/$PID/smaps_rollup" ]; then
    cat /proc/$PID/smaps_rollup
fi
echo ""
echo "--- TOP 5 REGIONES DE MEMORIA ---"
if [ -f "/proc/$PID/smaps" ]; then
    grep -A 1 "^[0-9a-f]" /proc/$PID/smaps 2>/dev/null | head -30
fi
echo ""
echo "==================================================="
echo "FASE 4: ASYNC / TASKS / HEAP (tracemalloc)"
echo "==================================================="
# tracemalloc solo funciona si el proceso está instrumentado
# Verificamos si tiene _tracemalloc activo
if [ -d "/proc/$PID" ]; then
    echo "--- ¿tracemalloc activo? ---"
    ls /proc/$PID/task/$PID/syscall 2>/dev/null
    cat /proc/$PID/task/$PID/syscall 2>/dev/null
    echo ""
    # Intentar via gdb si está disponible
    which gdb 2>/dev/null && echo "gdb available" || echo "gdb no disponible"
fi
echo ""
echo "==================================================="
echo "FASE 13: KERNEL / OOM / SWAP"
echo "==================================================="
echo "--- SWAP ---"
swapon --show 2>/dev/null
free -h | grep -i swap
echo ""
echo "--- OOM KILLER (últimos 50 eventos) ---"
dmesg 2>/dev/null | grep -i -E "(oom|killed|memory)" | tail -50
echo ""
echo "--- Syslog OOM ---"
grep -i -E "(oom|killed|out of memory)" /var/log/syslog 2>/dev/null | tail -20
echo ""
echo "--- HugePages ---"
cat /proc/meminfo | grep -i huge
