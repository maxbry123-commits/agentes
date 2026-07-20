# git — ejemplo básico

```bash
# Ver status
echo '{"action":"status","repo":"."}' | openclaw skill run git

# Crear branch + commit
echo '{"action":"branch","repo":".","name":"feature/registries"}' | openclaw skill run git
echo '{"action":"commit","repo":".","message":"feat: registries v0.1","files":["registries/"]}' | openclaw skill run git

# Push (sin force)
echo '{"action":"push","repo":".","branch":"feature/registries"}' | openclaw skill run git

# PR
echo '{"action":"pr","repo":".","title":"feat: registries v0.1","body":"first cut","base":"main"}' | openclaw skill run git
```

## Output esperado (pr)
```json
{ "ok": true, "stdout": "{\"number\":42,...}" }
```
