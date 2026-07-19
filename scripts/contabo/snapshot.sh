#!/bin/bash
CID="INT-15169759"; CS="ygExp61IwrV9eu0dImIirLR0oxvit3Sm"
U="${MAXBRY_EMAIL}"; P='${CONTABO_PASSWORD}'
IID=203428294
T=$(curl -s -X POST "https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token" -d "grant_type=password&client_id=$CID&client_secret=$CS&username=$U&password=$P" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token','FAIL'))" 2>/dev/null)
if [ "$T" != "FAIL" ] && [ -n "$T" ]; then
  S=$(curl -s -X POST "https://api.contabo.com/v1/compute/instances/$IID/snapshots" -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{\"name\":\"auto-$(date +%Y%m%d-%H%M)\"}")
  echo "$(date '+%F %T') snapshot: $S"
else
  echo "$(date '+%F %T') snapshot FAIL: no token"
fi
