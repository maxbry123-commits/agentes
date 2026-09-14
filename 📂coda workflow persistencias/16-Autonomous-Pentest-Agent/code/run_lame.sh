#!/bin/bash
# Run against Lame (secondary target)
source venv/bin/activate

ATTACKER_IP=$(ip addr show tun0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

# Despawn Shocker, spawn Lame on HTB first!
python -m src.main \
    --target 10.10.10.3 \
    --machine lame \
    --attacker-ip "$ATTACKER_IP" \
    --output-dir output/lame_run1 \
    --log-level INFO