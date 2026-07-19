 </runtime-baseline/RUNTIME_VALIDATION.md 2>/dev/null
# RUNTIME VALIDATION
Date: 2026-07-10T01:48:20Z

## Test 1: OpenClaw agent (winnerModel extraction)
- command: openclaw agent --agent main --message-file /tmp/oc-val.txt --json
- result: OK
- winner: ? / ?
- duration: 11524ms

## Test 2: Claude Code
- command: claude -p 'reply OK'
- result: OK
- duration: 63160ms

## Test 3: MiMo Code
root@vmi3428294:~# echo 