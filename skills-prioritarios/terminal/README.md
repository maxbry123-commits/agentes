# terminal

## Qué hace
Wrapper de bash con sandboxing básico: timeout, output cap, working-dir aislado, y lista blanca/blacklist de comandos.

## Cuándo se usa
- Cuando una skill necesita ejecutar un comando arbitrario (no un git, no un test, sino "corre esto").
- En el harness E2B para tareas de programación.

## Schema
```yaml
id: terminal
version: 0.1.0
entry: ./run.py
required_tools: [bash]
tags: [shell, exec]
source: core
```

## Uso
```bash
openclaw skill run terminal --input '{"cmd":"ls -la","cwd":".","timeout_s":10}'
openclaw skill run terminal --input '{"cmd":"curl -sS https://api.github.com/zen","timeout_s":5}'
```

## Seguridad
- Default `timeout_s = 30`, `max_output_bytes = 1MB`.
- Lista negra de comandos: `rm -rf /`, `mkfs`, `dd if=`, `:(){ :|:& };:` (fork bomb).
- Lista negra de paths: `/etc`, `/var`, `/boot` (read-only).
- Si el comando toca algo no permitido → denegado antes de ejecutar.

## Estado
- Spec completa, scripts en este dir.
- Pendiente: rate-limit y audit log persistente.
