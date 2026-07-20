# task-manager — ejemplo básico

## Crear 3 TODOs

```bash
echo '{"action":"add","title":"Auditar repo agentes","owner":"M3"}' | openclaw skill run task-manager
echo '{"action":"add","title":"Levantar HF Space sync","owner":"M3"}' | openclaw skill run task-manager
echo '{"action":"add","title":"PR a main con registries","owner":"M3"}' | openclaw skill run task-manager
```

## Listar pendientes

```bash
echo '{"action":"list","status":"pending"}' | openclaw skill run task-manager
```

## Marcar como hecho

```bash
echo '{"action":"done","id":"t-001"}' | openclaw skill run task-manager
```

## Output esperado
```json
{ "ok": true, "items": [...], "count": 2 }
```
