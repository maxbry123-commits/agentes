#!/bin/bash
# ============================================
# HTB ENVIRONMENT SETUP CHECKLIST
# ============================================

echo "=== STEP 1: HTB VPN Connection ==="
echo "Option A: Kali Linux (your machine)"
echo "  1. Download your HTB VPN .ovpn file from https://app.hackthebox.com/connections"
echo "  2. Connect:"
echo "     sudo openvpn lab_deltaRed1a.ovpn"
echo ""
echo "Option B: HTB Pwnbox (browser-based)"
echo "  1. Go to https://app.hackthebox.com"
echo "  2. Click 'Pwnbox' → Start"
echo "  3. VPN is pre-connected"
echo ""

echo "=== STEP 2: Spawn Target Machine ==="
echo "  1. Go to https://app.hackthebox.com/machines"
echo "  2. Search for 'Shocker' (retired machines)"
echo "  3. Click 'Spawn Machine'"
echo "  4. Note the target IP (should be 10.10.10.56)"
echo ""

echo "=== STEP 3: Verify Connectivity ==="
echo "  Run these commands:"
echo "     # Get your attacker IP (tun0 interface)"
echo "     ip addr show tun0 | grep inet"
echo ""
echo "     # Verify target is reachable"
echo "     ping -c 3 10.10.10.56"
echo ""

echo "=== STEP 4: Configure the Agent ==="
echo "  Edit .env file:"
echo "     ANTHROPIC_API_KEY=sk-ant-your-key"
echo "     TARGET_IP=10.10.10.56"
echo "     MACHINE_PROFILE=shocker"
echo ""

echo "=== STEP 5: Dry Run First ==="
echo "  python -m src.main --target 10.10.10.56 --machine shocker --attacker-ip YOUR_TUN0_IP --dry-run"