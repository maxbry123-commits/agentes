#!/bin/bash
# FASE 2: Eliminar SOLO procesos: temporales, duplicados, huérfanos, zombie, crash-loop
# KILL -9 con verificación previa
echo "=== FASE 2: LIMPIEZA DE PROCESOS NO AUTORIZADOS ==="
echo ""

killed=0
kept=0

# Helper: matar proceso si existe, no es servicio del sistema, y no es de sistema
kill_safe() {
    local pattern=$1
    local reason=$2
    PIDS=$(pgrep -f "$pattern" 2>/dev/null)
    for p in $PIDS; do
        # Verificar que NO es un servicio del sistema (PPID=1 + nombre conocido)
        cmd=$(cat /proc/$p/comm 2>/dev/null)
        ppid=$(awk '/^PPid:/{print $2}' /proc/$p/status 2>/dev/null)
        user=$(awk '/^Uid:/{print $2}' /proc/$p/status 2>/dev/null)
        # No matar: systemd, init, sshd, dockerd, containerd, fail2ban, cron, rsyslogd, dbus, polkitd, systemd-journal, networkd, resolved, login, getty, agetty
        case "$cmd" in
            systemd|init|sshd|dockerd|containerd|fail2ban-server|cron|rsyslogd|dbus-daemon|polkitd|systemd-journal|systemd-network|systemd-resolve|systemd-logind|systemd-udevd|systemd-timesyn|login|agetty|getty|ModemManager|multipathd|nginx|node|claude|openclaw|chrome|chrome-headless|litellm|uvicorn|next-server|main|java|postgres|mysql|redis|mongod|docker-proxy)
                # NO matar, son servicios legítimos
                ;;
            *)
                # Matar solo si user=root y no es nuestro orquestador
                if [ "$user" = "0" ]; then
                    # No matar: conector_chat, sentinel_loop (los míos de testing)
                    cmdline=$(cat /proc/$p/cmdline 2>/dev/null | tr '\0' ' ')
                    case "$cmdline" in
                        *conector_chat*|*sentinel_loop*)
                            # Lo dejo
                            ;;
                        *)
                            # Matar
                            kill -9 $p 2>/dev/null && echo "  KILLED PID $p ($cmd) - $reason" && killed=$((killed+1))
                            ;;
                    esac
                fi
                ;;
        esac
    done
}

# 1. Scripts temporales propios
echo "[1/12] Eliminando scripts temporales de testing..."
kill_safe "diag_ram.sh" "script de diagnóstico temporal"
kill_safe "forensic_audit" "script forense temporal"
kill_safe "audit_vps" "script auditoría temporal"
kill_safe "node_audit" "script node temporal"
kill_safe "quick_audit" "script auditoría temporal"
kill_safe "start_sentinel" "script watchdog testing"
kill_safe "fase1_pausa" "script ya ejecutado"
kill_safe "fase2_limpieza" "este mismo script"
echo ""

# 2. Procesos python3 genéricos sin propósito claro (no son los del sistema)
echo "[2/12] Eliminando python3 huérfanos..."
# los python3 legítimos: 75810, 75826, 75827, 1956752, 1956969, 2001442 (openclaw), 82196, 82184
# Los que mato: cualquier python3 que sea nuestro/testing
kill_safe "test_post.py" "script de test"
kill_safe "test_apis" "script de test"
echo ""

# 3. Procesos con muchos fd abiertos que sean míos
echo "[3/12] Verificando fd leaks..."
for p in $(ls /proc/ 2>/dev/null | grep -E "^[0-9]+$"); do
    fd_count=$(ls /proc/$p/fd 2>/dev/null | wc -l)
    if [ "$fd_count" -gt "100" ]; then
        cmd=$(cat /proc/$p/comm 2>/dev/null)
        cmdline=$(cat /proc/$p/cmdline 2>/dev/null | tr '\0' ' ' | head -c 200)
        echo "  HIGH-FD PID $p ($cmd) $fd_count fds: $cmdline"
    fi
done
echo ""

# 4. Procesos duplicados
echo "[4/12] Buscando duplicados..."
# python3 con mismo cmdline
python_cmds=$(ps -eo pid,cmd --no-headers | grep python3 | awk '{$1=""; print $0}' | sort | uniq -c | sort -rn | head -5)
echo "$python_cmds"
echo ""

# 5. Procesos zombie
echo "[5/12] Buscando zombies..."
ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print "  ZOMBIE PID "$1" PPID "$2" "$4}'
echo ""

# 6. Procesos en crash loop (etime muy bajo + restart_count alto)
echo "[6/12] Buscando crash loops..."
# en systemd: systemctl list-units --state=failed
# manual: procesos con etime < 60s y high cpu
ps -eo pid,etime,comm | awk '$2 ~ /[0-9]{2}:[0-9]{2}/ && length($2) < 6 {print "  RECENT PID "$1" "$2" "$3}' | head -10
echo ""

# 7. Reporte de lo que SOBREVIVE
echo "[7/12] PROCESOS SOBREVIVIENTES (lo que NO se mata):"
ps -eo pid,ppid,user,etime,stat,%mem,rss,comm --sort=-rss | head -30
echo ""

# 8. RAM final
echo "[8/12] RAM FINAL:"
free -h
echo ""

echo "=== RESUMEN FASE 2 ==="
echo "Killed: $killed procesos"
echo "Kept: servicios legítimos (systemd, sshd, dockerd, nginx, node/openclaw, claude, etc.)"
