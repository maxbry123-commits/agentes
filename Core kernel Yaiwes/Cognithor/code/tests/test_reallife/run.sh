#!/bin/bash
# Run real-life test suite
# Usage: ./tests/test_reallife/run.sh [--docker]

set -e

if [ "$1" = "--docker" ]; then
    echo "Building and running tests in Docker..."
    docker compose -f tests/test_reallife/docker-compose.yml up --build --abort-on-container-exit
    exit $?
fi

echo "Running real-life tests locally..."
python -m pytest tests/test_reallife/ -v --tb=short -x
