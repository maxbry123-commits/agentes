# backend — conventions (Python)

All conventions in the root `CLAUDE.md` apply here. Python-specific emphasis:

- **No leading `_`; use `p_` for private** (`no-underscore-names`), and a `p_` name used outside its
  file/class must be made **public** (`p-private`). Both are linter-enforced for `backend/`.
- **Absolute imports only** — `from backend.apps.foo import bar`, never `from .foo import bar`.
- **No barrels** — `__init__.py` must not exist solely to re-export.
- **`@typechecked` on every function**, and prefer `typing` generics (`List`, `Dict`, `Optional`)
  over builtins. Pyright/Pylance strict.
- **Classes are pydantic `BaseModel`** (`model_config = ConfigDict(validate_assignment=True)`,
  `InstanceOf[...]` for unrecognized field types). Don't use plain classes or bare `dict`s for
  structured data — model it. Legitimate dicts: dynamic-key registries and external protocol shapes
  (SDK hook returns, `model_dump` output).
- **Single-purpose file naming** — a one-export file is named after its export.
- **Comments are ONE line each, no exceptions** — never wrap across multiple `#` lines; keep only
  WHY/gotcha comments, delete restating or dead-code comments. Docstrings are exempt.
- **No gratuitous blank lines** — never stack 2+ blanks; keep imports tight (only the single
  stdlib/third-party/local group separators).

Touch a file → it must be clean under these rules. Pre-existing debt is grandfathered in
`linter/config/config.json`; don't mass-migrate untouched files.
