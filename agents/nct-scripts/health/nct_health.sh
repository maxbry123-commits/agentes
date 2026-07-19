#!/bin/bash
# nct_health.sh — Health check completo del VPS NCT
echo "=== NCT Health Check $(date -u +%FT%TZ) ==="
echo

# Servicios systemd
echo "--- servicios ---"
for s in ssh openclaw litellm fail2ban; do
    st=$(systemctl is-active $s 2>/dev/null)
    if [ "$st" = "active" ]; then echo "  $s: OK"; else echo "  $s: FAIL ($st)"; fi
done
pgrep -fa 'open-webui serve' > /dev/null && echo "  open-webui: OK" || echo "  open-webui: FAIL"

# Puertos
echo
echo "--- puertos ---"
ss -tlnp 2>/dev/null | grep -E ':(22|18789|4000|8080) ' | awk '{print "  "$0}'

# Recursos
echo
echo "--- recursos ---"
free -h | head -2
df -h / | tail -1

# GitHub
echo
echo "--- github ---"
ssh -T -o BatchMode=yes -o ConnectTimeout=5 git@github.com 2>&1 | head -1

# 16 repos
echo
echo "--- 16 repos (esperado 16/16) ---"
COUNT=$(ls -d /opt/nct/repos/*/ 2>/dev/null | grep -vE '/(repos_index|repos_inventory)' | wc -l)
echo "  encontrados: $COUNT"

# 4 subagentes VPS
echo
echo "--- 4 subagentes VPS ---"
for a in claude-code-vps-A claude-code-vps-B mimo-code-vps-A mimo-code-vps-B; do
    [ -d /opt/nct/repos/agentes/$a ] && echo "  $a: OK" || echo "  $a: FAIL"
done

# Skill Router
echo
echo "--- skill router ---"
[ -f /opt/nct/skills/registry/skill_registry.json ] && echo "  registry: OK" || echo "  registry: FAIL"
[ -d /opt/nct/skills/vault ] && echo "  vault: OK" || echo "  vault: FAIL"
[ -x /opt/nct/skills/judge/run_judge.sh ] && echo "  judge: OK" || echo "  judge: FAIL"

# Secret manager
echo
echo "--- secret manager (6 keys cerebras + 6 groq esperado) ---"
CEREBRAS=$(ls /opt/nct/secrets/providers/cerebras* /opt/nct/secrets/providers/openclaw_* /opt/nct/secrets/providers/mimo_primary* /opt/nct/secrets/providers/mimo_failover* /opt/nct/secrets/providers/claude_primary* /opt/nct/secrets/providers/claude_failover* 2>/dev/null | wc -l)
GROQ=$(ls /opt/nct/secrets/providers/openclaw_groq_* /opt/nct/secrets/providers/mimo_groq_* /opt/nct/secrets/providers/claude_groq_* 2>/dev/null | wc -l)
echo "  cerebras: $CEREBRAS archivos"
echo "  groq: $GROQ archivos"

echo
echo "=== FIN ==="
