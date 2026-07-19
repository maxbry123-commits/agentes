 cat /root/.openclaw/skills/claude-code.md 2>/dev/null
# Skill: claude-code-vps
Al delegar a claude-code, ejecuta:
curl -sS -X POST http://127.0.0.1:8081/chat -H 'Content-Type: application/json' -d '{"prompt":"$TASK"}'
root@vmi3428294:~# echo 