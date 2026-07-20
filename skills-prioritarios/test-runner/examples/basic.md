# test-runner — ejemplo básico

```bash
# Detección automática
echo '{"path":"./core","framework":"auto"}' | openclaw skill run test-runner

# Forzar pytest
echo '{"path":"./core","framework":"pytest","max_duration_s":60}' | openclaw skill run test-runner
```

## Output
```json
{
  "ok": true,
  "framework": "pytest",
  "duration_s": 12.3,
  "returncode": 0
}
```
