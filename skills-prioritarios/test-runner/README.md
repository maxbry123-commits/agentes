# test-runner

## Qué hace
Detecta el framework de tests del proyecto target (pytest, vitest, jest, go test, cargo test) y los corre. Devuelve resumen estructurado (pass/fail/skip, duración, archivos fallidos).

## Cuándo se usa
- Después de cada cambio de código (validación rápida).
- En el nodo `HEALTH` del pipeline DSL DAG SHERIFF.
- Antes de hacer `git push` (en CI local).

## Schema

```yaml
id: test-runner
version: 0.1.0
entry: ./run.py
required_tools: [bash, fs, parse]
tags: [qa, test, ci]
source: core
```

## Uso

```bash
openclaw skill run test-runner --input '{"path":".","framework":"auto","max_duration_s":120}'
openclaw skill run test-runner --input '{"path":"core/tests","framework":"pytest"}'
```

## Frameworks soportados (v0.1)
- `pytest` (Python)
- `vitest` / `jest` (Node)
- `go test` (Go)
- `cargo test` (Rust)
- `auto` (detecta por archivos `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`)

## Estado
- Spec completa, scripts en este dir.
- Pendiente: detección robusta de framework y parseo de output.
