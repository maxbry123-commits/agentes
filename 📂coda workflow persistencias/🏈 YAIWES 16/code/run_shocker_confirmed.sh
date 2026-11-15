#!/bin/bash
# Run against Shocker WITH confirmation prompts (recommended first run)
source venv/bin/activate

# Get attacker IP automatically
ATTACKER_IP=$(ip addr show tun0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
echo "Attacker IP: $ATTACKER_IP"

python -m src.main \
    --target 10.10.10.56 \
    --machine shocker \
    --attacker-ip "$ATTACKER_IP" \
    --output-dir output/shocker_run1 \
    --log-level INFO