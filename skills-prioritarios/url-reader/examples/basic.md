# url-reader — ejemplo básico

```bash
echo '{"url":"https://github.com/openclaw/openclaw","max_chars":20000}' | openclaw skill run url-reader
```

## Output
```json
{
  "ok": true,
  "status_code": 200,
  "final_url": "https://github.com/openclaw/openclaw",
  "markdown": "OpenClaw - the open source agent gateway...",
  "length": 18432,
  "truncated": false
}
```
