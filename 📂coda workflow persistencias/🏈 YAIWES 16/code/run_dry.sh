#!/bin/bash
# Dry run — validates the agent logic without executing any commands
source venv/bin/activate

python -m src.main \
    --target 10.10.10.56 \
    --machine shocker \
    --attacker-ip 10.10.14.1 \
    --dry-run \
    --log-level DEBUG \
    --output-dir output/dry_run