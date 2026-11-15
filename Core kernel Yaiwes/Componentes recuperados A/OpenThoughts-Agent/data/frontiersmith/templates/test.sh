#!/bin/bash
# In-container judge entrypoint. Compiles + runs the contestant's
# /app/solution.cpp against the 10 testlib cases, computes the mean quality
# ratio, and thresholds it at TAU into a binary /logs/verifier/reward.txt.
mkdir -p /logs/verifier
python3 /tests/run_judge.py 2>&1 | tee /logs/verifier/evaluation.log
# Fallback: if the judge crashed before writing a reward, fail closed.
if [ ! -f /logs/verifier/reward.txt ]; then
    echo "0" > /logs/verifier/reward.txt
fi
