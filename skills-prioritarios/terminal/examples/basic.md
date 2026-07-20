# terminal — ejemplo básico

```bash
# Listar archivos
echo '{"cmd":"ls -la","cwd":".","timeout_s":10}' | openclaw skill run terminal

# Pings
echo '{"cmd":"ping -c 1 8.8.8.8","timeout_s":5}' | openclaw skill run terminal

# Pipelines (mientras ninguno esté en blacklist)
echo '{"cmd":"ps aux | grep openclaw | grep -v grep","timeout_s":5}' | openclaw skill run terminal
```

## Output
```json
{
  "ok": true,
  "returncode": 0,
  "stdout": "...",
  "stderr": "",
  "duration_s": 0.12
}
```
