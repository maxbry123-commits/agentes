# web-search — ejemplo básico

```bash
# Con Serper
export SERPER_API_KEY=...
echo '{"q":"daytona io api documentation","n":5}' | openclaw skill run web-search

# Sin Serper, cae a DDG
echo '{"q":"openclaw mcp bridge","n":10,"provider":"auto"}' | openclaw skill run web-search
```

## Output
```json
{
  "ok": true,
  "provider_used": "serper",
  "results": [
    {"title":"...","url":"https://...","snippet":"..."}
  ],
  "count": 5
}
```
