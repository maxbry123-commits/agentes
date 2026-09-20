# Nota 2026-09-20 - Swap de agentes en los handoffs de fase_0

## Por que se cambiaron los 3 agentes originales

Verificados hoy leyendo archivos reales (no supuestos):

- `claude_code`: no tiene `package.json` en la raiz. El contenido real que hay (README.md, CHANGELOG.md de 587KB, feed.xml, demo.gif.chunks) corresponde a un repo de documentacion/changelog, no al codigo fuente instalable del CLI. No sirve para este slot.
- `codex`: SI tiene codigo real, pero es el monorepo completo `codex-rs` + herramientas node. Requiere toolchain Rust (`cargo`) para compilar el binario (`cargo run --manifest-path ./codex-rs/Cargo.toml ...`). No es un pip/npm install simple.
- `opencode`: SI tiene codigo real, pero es un monorepo Bun (`packageManager: bun@1.3.14`) con dependencias nativas (node-pty, tree-sitter, electron) y `"private": true`. Requiere `bun install` + build de un workspace grande, no un install simple.

## Reemplazos verificados hoy (pip-installable, sin toolchain adicional)

- `aider`: `pyproject.toml` con `[project.scripts] aider = "aider.main:main"`, setuptools estandar, deps normales de pip.
- `smolagents`: `pyproject.toml` con `[project.scripts] smolagent = "smolagents.cli:main"`, setuptools estandar, deps normales de pip (huggingface-hub, requests, rich, jinja2).

No se verifico un tercer candidato para no alargar esta busqueda mas de lo necesario (`qwen_code` y `openhands` no tienen los archivos de manifiesto en la raiz donde se buscaron - no se descarta que existan en otra ruta, solo no se confirmaron hoy).

## Reasignacion de los 5 nodos de fase_0
- `aider` -> N-1.1 (submodules en CI) + N-2.8 (7 archivos de gobernanza)
- `smolagents` -> N-1.3 (montar mcode) + N-1.4 (5 keys NVIDIA) + N-2.11 (biblioteca RAG)

## Estado de los handoffs anteriores
No se borraron (regla R03). `HANDOFF-claude_code.md`, `HANDOFF-codex.md` y `HANDOFF-opencode.md` quedan en el repo como estaban, sin marca de superseded todavia (pendiente si el Director quiere que se anoten como obsoletos o se dejen como estan).

## Lo que sigue sin resolver
Sigue sin haber, en esta sesion, un mecanismo real que instale `aider`/`smolagents` y los ejecute de forma autonoma contra su handoff. Eso es la siguiente pieza si se quiere automatizar de verdad, no solo dejar el contrato de tarea escrito.
