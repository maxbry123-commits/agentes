#!/bin/bash
# nct_health_v2.sh — Health check v2 de NCT
set +e
G='\033[0;32m'; R='\033[0;31m'; N='\033[0m'
ps() { if [ "$1" = "OK" ]; then printf "%-30s [${G}OK${N}] %s\n" "$2" "$3"; else printf "%-30s [${R}FAIL${N}] %s\n" "$2" "$3"; fi; }
echo "=== NCT Health Check v2 $(date -u +%FT%TZ) ==="
echo
echo "--- servicios ---"
for s in ssh openclaw litellm fail2ban; do
    st=$(systemctl is-active $s 2>/dev/null)
    [ "$st" = "active" ] && ps OK "$s" "active" || ps FAIL "$s" "$st"
done
pgrep -fa 'open-webui serve' > /dev/null && ps OK "open-webui" "running" || ps FAIL "open-webui" "stopped"

echo
echo "--- puertos ---"
PORTS=$(ss -tlnp 2>/dev/null | grep -E ':(22|18789|4000|8080) ' | wc -l)
[ $PORTS -ge 4 ] && ps OK "puertos" "$PORTS/4 escuchando" || ps FAIL "puertos" "$PORTS/4"

echo
echo "--- 16 repos proyecto (incluye agentes) ---"
N_REPOS=0
for d in /opt/nct/repos/*/; do
    name=$(basename "$d")
    case "$name" in
        repos_index|repos_inventory|pendientes) continue ;;
    esac
    N_REPOS=$((N_REPOS+1))
done
[ $N_REPOS -eq 16 ] && ps OK "repos proyecto" "$N_REPOS/16" || ps FAIL "repos proyecto" "$N_REPOS/16"

echo
echo "--- 5 foundation ---"
N_FOUND=0
for d in /opt/nct/foundation/*/; do
    N_FOUND=$((N_FOUND+1))
done
[ $N_FOUND -eq 5 ] && ps OK "foundation" "$N_FOUND/5" || ps FAIL "foundation" "$N_FOUND/5"

echo
echo "--- 8 sub-agentes en repo agentes ---"
N_AG=0
for g in A B C D; do
    [ -d /opt/nct/repos/agentes/claude-code-vps-$g ] && N_AG=$((N_AG+1))
    [ -d /opt/nct/repos/agentes/mimo-code-vps-$g ] && N_AG=$((N_AG+1))
done
[ $N_AG -eq 8 ] && ps OK "sub-agentes" "$N_AG/8" || ps FAIL "sub-agentes" "$N_AG/8"

echo
echo "--- 4 modelos LiteLLM ---"
N_M=$(curl -sS -m 5 http://127.0.0.1:4000/v1/models 2>/dev/null | python3 -c "import json,sys; print(len(json.loads(sys.stdin.read()).get('data',[])))" 2>/dev/null)
[ "$N_M" = "4" ] && ps OK "litellm modelos" "$N_M/4" || ps FAIL "litellm modelos" "$N_M/4"

echo
echo "--- secret manager ---"
N_SEC=$(ls /opt/nct/secrets/providers/*.env 2>/dev/null | wc -l)
[ $N_SEC -ge 12 ] && ps OK "secret files" "$N_SEC archivos" || ps FAIL "secret files" "$N_SEC archivos"

echo
echo "--- github ---"
GHO=$(ssh -T -o BatchMode=yes -o ConnectTimeout=5 git@github.com 2>&1 | grep -o "maxbry123-commits" | head -1)
[ -n "$GHO" ] && ps OK "github auth" "maxbry123-commits" || ps FAIL "github auth" "fail"

echo
echo "--- skill router ---"
[ -f /opt/nct/skills/registry/skill_registry.json ] && ps OK "skill_registry" "OK" || ps FAIL "skill_registry" "FAIL"

echo
echo "=== END ==="
