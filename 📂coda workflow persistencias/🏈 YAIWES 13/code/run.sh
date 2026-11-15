#!/bin/bash

# Check if .env exists
if [ ! -f .env ]; then
    echo "[!] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "[*] Please edit .env with your credentials and run this script again."
    exit 1
fi

echo "[*] Building and Starting Agent..."
docker compose up --build
