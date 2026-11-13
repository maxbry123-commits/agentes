#!/bin/bash
# ============================================
# PRE-FLIGHT CHECKS — Run before the real engagement
# ============================================

echo "🔍 Checking required tools..."

TOOLS=("nmap" "gobuster" "nikto" "whatweb" "curl" "searchsploit" "nc" "python3" "smbclient")
MISSING=()

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "  ✅ $tool"
    else
        echo "  ❌ $tool — MISSING"
        MISSING+=("$tool")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing tools. On Kali, install with:"
    echo "  sudo apt update && sudo apt install -y ${MISSING[*]}"
fi

echo ""
echo "🔍 Checking Python environment..."
python3 -c "import anthropic; print('  ✅ anthropic SDK')" 2>/dev/null || echo "  ❌ anthropic SDK"
python3 -c "import yaml; print('  ✅ pyyaml')" 2>/dev/null || echo "  ❌ pyyaml"
python3 -c "import rich; print('  ✅ rich')" 2>/dev/null || echo "  ❌ rich"
python3 -c "import dotenv; print('  ✅ python-dotenv')" 2>/dev/null || echo "  ❌ python-dotenv"

echo ""
echo "🔍 Checking API key..."
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ ANTHROPIC_API_KEY is set"
elif [ -f .env ]; then
    if grep -q "ANTHROPIC_API_KEY=sk-" .env; then
        echo "  ✅ ANTHROPIC_API_KEY found in .env"
    else
        echo "  ❌ ANTHROPIC_API_KEY not configured in .env"
    fi
else
    echo "  ❌ No .env file found"
fi

echo ""
echo "🔍 Checking VPN connection..."
if ip addr show tun0 &> /dev/null; then
    ATTACKER_IP=$(ip addr show tun0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    echo "  ✅ VPN connected — Your IP: $ATTACKER_IP"
else
    echo "  ❌ VPN not connected (no tun0 interface)"
    echo "     Connect with: sudo openvpn your_htb.ovpn"
fi