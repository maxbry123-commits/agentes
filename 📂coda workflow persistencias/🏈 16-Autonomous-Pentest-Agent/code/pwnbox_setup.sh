# On HTB Pwnbox or your Kali VM:

# 1. Clone your repo
git clone https://github.com/deltaRed1a/autonomous-pentest-agent.git
cd autonomous-pentest-agent

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create .env
cp .env.example .env
nano .env
# Add your ANTHROPIC_API_KEY

# 4. Verify VPN is connected
ip addr show tun0 | grep inet
# Note your attacker IP

# 5. Verify target is reachable (Shocker should be spawned on HTB)
ping -c 3 10.10.10.56

# 6. Run preflight checks
bash preflight_check.sh

# 7. GO — Confirmed run against Shocker
ATTACKER_IP=$(ip addr show tun0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
python -m src.main \
    --target 10.10.10.56 \
    --machine shocker \
    --attacker-ip "$ATTACKER_IP" \
    --output-dir output/shocker_run1