# jarvis → cognithor Rename — Design Spec

**Goal:** Rename the Python package from `jarvis` to `cognithor` in one atomic commit. Release as v0.87.0.

**Scope:** ~5,500 occurrences across ~600 files. Python source (514 files), tests (565 files), Flutter/Dart (598 imports), env vars (80 unique, 287 refs), paths (677 refs), shell scripts, Docker, CI, installer.

## Architecture

### 1. Automated rename script (`scripts/rename_jarvis_to_cognithor.py`)

Executes all changes in sequence:

1. **Pre-flight:** Verify git is clean, record baseline test count
2. **Directory rename:** `git mv src/jarvis src/cognithor`
3. **Python imports (src/):** `from jarvis.` → `from cognithor.`, `import jarvis` → `import cognithor`
4. **Python imports (tests/):** Same transformations
5. **Env vars:** `JARVIS_` → `COGNITHOR_` with dual-read fallback wrapper
6. **Home path:** `".cognithor"` → `".cognithor"` with migration detection
7. **Flutter:** `jarvis_ui` → `cognithor_ui` in pubspec.yaml + all Dart imports
8. **Config:** pyproject.toml packages, entry points
9. **Shell/Docker/CI:** All remaining JARVIS_ references
10. **Compat shim:** `src/jarvis/__init__.py` (removed after tests pass if not needed)
11. **Post-flight:** Full test suite, ruff lint, flutter build

### 2. Env var fallback

```python
def _env(new: str, old: str, default: str = "") -> str:
    return os.environ.get(new) or os.environ.get(old, default)
```

Applied in `config.py` where env vars are read. Both `COGNITHOR_*` and `JARVIS_*` work.

### 3. Home directory migration

```python
_NEW = Path.home() / ".cognithor"
_OLD = Path.home() / ".cognithor"
COGNITHOR_HOME = _NEW if _NEW.exists() else _OLD if _OLD.exists() else _NEW
```

On first start after upgrade: if `~/.cognithor` exists and `~/.cognithor` does not, create symlink `~/.cognithor` → `~/.cognithor`. No data copy, no risk.

### 4. What stays as "jarvis"/"Jarvis"

- Personality name in SYSTEM_PROMPT ("Du bist Jarvis")
- `jarvis` CLI entry point in pyproject.toml (backwards compat alias)
- Git history, CHANGELOG historical entries
- Widget class names (JarvisTextField etc.) — internal, no user impact

### 5. Flutter rename

- `pubspec.yaml`: `name: cognithor_ui`
- All `.dart` files: `package:jarvis_ui/` → `package:cognithor_ui/`
- Android Kotlin package path updated
- Widget class names unchanged (internal)

### 6. Verification

1. `python -c "from cognithor import __version__"`
2. `pytest tests/ -x -q` — all 13k+ tests green
3. `ruff check src/ tests/ --select=F821,F811`
4. `ruff format --check src/ tests/`
5. `flutter build web --release`
6. `grep -r "from jarvis\." src/cognithor/ --include="*.py"` → 0 results

### 7. Release

Tag v0.87.0, push, create GitHub release, PyPI publish triggers automatically.
