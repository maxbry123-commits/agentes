#!/bin/bash
# Corre health check cada 20 min y guarda log
set +e
mkdir -p /opt/nct/logs/health
TS=$(date -u +%Y%m%d-%H%M%S)
/opt/nct/scripts/health/nct_health_v2.sh > /opt/nct/logs/health/health-$TS.log 2>&1
# Borrar logs viejos (>7 dias)
find /opt/nct/logs/health -mtime +7 -delete
