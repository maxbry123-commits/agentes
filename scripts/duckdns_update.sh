#!/bin/bash
TOKEN="d91e91b5-8885-49ec-bd22-07968b0f566a"
DOMAINS="maxbry1,maxbry2,maxbry3,maxbry4,maxbry5"
IP="$(curl -s -m 5 'https://api.ipify.org' 2>/dev/null || echo '95.111.232.89')"
curl -s "https://www.duckdns.org/update?domains=$DOMAINS&token=$TOKEN&ip=$IP" > /var/log/duckdns_update.log 2>&1
