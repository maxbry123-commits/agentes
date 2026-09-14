#!/usr/bin/env python3
"""Atomic rename: jarvis -> cognithor.

This script performs the complete package rename in one pass.
Run from the project root: python scripts/rename_jarvis_to_cognithor.py

What it does:
1. git mv src/jarvis -> src/cognithor
2. Update all Python imports in src/ and tests/
3. Update JARVIS_ env vars -> COGNITHOR_ (with fallback support)
4. Update ~/.jarvis paths -> ~/.cognithor
5. Update Flutter package name
6. Update pyproject.toml, shell scripts, Docker, CI
7. Create backwards-compat jarvis shim

What it does NOT touch:
- "Jarvis" personality name in prompts/personality
- jarvis CLI entry point alias (backwards compat)
- Git history / CHANGELOG historical entries
- Widget class names (JarvisTextField etc.)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"
FLUTTER = ROOT / "flutter_app"

# Counters
stats: dict[str, int] = {
    "files_modified": 0,
    "imports_replaced": 0,
    "env_vars_replaced": 0,
    "paths_replaced": 0,
    "dart_imports_replaced": 0,
}


def replace_in_file(
    path: Path, replacements: list[tuple[str, str]], skip_patterns: list[str] | None = None
) -> int:
    """Apply replacements to a file. Returns count of replacements made."""
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0

    original = content
    count = 0

    for old, new in replacements:
        # Skip if line matches any skip pattern
        if skip_patterns:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if any(sp in line for sp in skip_patterns):
                    new_lines.append(line)
                else:
                    replaced = line.replace(old, new)
                    if replaced != line:
                        count += line.count(old)
                    new_lines.append(replaced)
            content = "\n".join(new_lines)
        else:
            occurrences = content.count(old)
            if occurrences:
                content = content.replace(old, new)
                count += occurrences

    if content != original:
        path.write_text(content, encoding="utf-8")
        stats["files_modified"] += 1

    return count


def step_git_mv():
    """Step 1: Rename directory."""
    print("\n=== Step 1: git mv src/jarvis -> src/cognithor ===")
    src_jarvis = SRC / "jarvis"
    src_cognithor = SRC / "cognithor"

    if not src_jarvis.exists():
        print("  [SKIP] src/jarvis/ does not exist (already renamed?)")
        return

    if src_cognithor.exists():
        print("  [ERROR] src/cognithor/ already exists!")
        sys.exit(1)

    subprocess.run(["git", "mv", str(src_jarvis), str(src_cognithor)], check=True, cwd=ROOT)
    print("  [OK] Renamed src/jarvis/ -> src/cognithor/")


def step_python_imports():
    """Step 2: Update all Python imports."""
    print("\n=== Step 2: Update Python imports ===")

    # Personality/prompt strings to skip
    skip = [
        "Du bist Jarvis",
        "Jarvis --",
        "persoenliche Assistent",
        "JARVIS SYSTEMPROMPT",
        "Jarvis.",  # Personality references in docstrings
    ]

    replacements = [
        ("from jarvis.", "from cognithor."),
        ("import jarvis.", "import cognithor."),
        ("import jarvis\n", "import cognithor\n"),
        ("import jarvis\r", "import cognithor\r"),
        ('"jarvis.', '"cognithor.'),
        ("'jarvis.", "'cognithor."),
        ("jarvis.__main__", "cognithor.__main__"),
        ("jarvis.__version__", "cognithor.__version__"),
    ]

    total = 0
    for py_file in list(SRC.rglob("*.py")) + list(TESTS.rglob("*.py")):
        count = replace_in_file(py_file, replacements, skip_patterns=skip)
        total += count

    stats["imports_replaced"] = total
    print(f"  [OK] {total} import replacements across src/ and tests/")


def step_env_vars():
    """Step 3: Update JARVIS_ env var references."""
    print("\n=== Step 3: Update environment variables ===")

    replacements = [
        ("JARVIS_", "COGNITHOR_"),
    ]

    # Skip in personality/prompt contexts
    skip = ["JARVIS SYSTEMPROMPT", "JARVIS_TEST_MODE"]  # Keep test mode for CI compat

    total = 0
    for py_file in list(SRC.rglob("*.py")) + list(TESTS.rglob("*.py")):
        count = replace_in_file(py_file, replacements, skip_patterns=skip)
        total += count

    # Also update shell scripts
    for script in ROOT.glob("*.sh"):
        total += replace_in_file(script, replacements)
    for script in ROOT.glob("*.bat"):
        total += replace_in_file(script, replacements)
    if (ROOT / "install.sh").exists():
        total += replace_in_file(ROOT / "install.sh", replacements)
    if (ROOT / "install.bat").exists():
        total += replace_in_file(ROOT / "install.bat", replacements)

    # Docker files
    for df in ROOT.glob("docker-compose*.yml"):
        total += replace_in_file(df, replacements)
    for df in ROOT.glob("Dockerfile*"):
        total += replace_in_file(df, replacements)

    # CI workflows
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        total += replace_in_file(wf, replacements)

    # .env files
    for env_file in ROOT.glob(".env*"):
        total += replace_in_file(env_file, replacements)

    stats["env_vars_replaced"] = total
    print(f"  [OK] {total} env var replacements")


def step_home_paths():
    """Step 4: Update ~/.jarvis path references."""
    print("\n=== Step 4: Update home directory paths ===")

    replacements = [
        ('".jarvis"', '".cognithor"'),
        ("'.jarvis'", "'.cognithor'"),
        ("/.jarvis/", "/.cognithor/"),
        ('/.jarvis"', '/.cognithor"'),
        ("\\.jarvis\\", "\\.cognithor\\"),
        ("~/.jarvis", "~/.cognithor"),
    ]

    total = 0
    for py_file in list(SRC.rglob("*.py")) + list(TESTS.rglob("*.py")):
        count = replace_in_file(py_file, replacements)
        total += count

    # Also docs
    for md_file in (ROOT / "docs").rglob("*.md"):
        total += replace_in_file(md_file, replacements)

    # Shell scripts
    for script in [ROOT / "install.sh", ROOT / "install.bat", ROOT / "start_cognithor.bat"]:
        if script.exists():
            total += replace_in_file(script, replacements)

    # Installer files
    for installer_file in (ROOT / "installer").glob("*.py"):
        total += replace_in_file(installer_file, replacements)
    iss = ROOT / "installer" / "cognithor.iss"
    if iss.exists():
        total += replace_in_file(iss, replacements)

    stats["paths_replaced"] = total
    print(f"  [OK] {total} path replacements")


def step_flutter():
    """Step 5: Rename Flutter package."""
    print("\n=== Step 5: Flutter package rename ===")

    if not FLUTTER.exists():
        print("  [SKIP] flutter_app/ not found")
        return

    replacements = [
        ("package:jarvis_ui/", "package:cognithor_ui/"),
        ("name: jarvis_ui", "name: cognithor_ui"),
    ]

    total = 0
    # pubspec.yaml
    pubspec = FLUTTER / "pubspec.yaml"
    if pubspec.exists():
        total += replace_in_file(pubspec, replacements)

    # All Dart files
    for dart_file in FLUTTER.rglob("*.dart"):
        count = replace_in_file(dart_file, replacements)
        total += count

    # l10n.yaml if it references the package
    l10n = FLUTTER / "l10n.yaml"
    if l10n.exists():
        total += replace_in_file(l10n, [("jarvis_ui", "cognithor_ui")])

    stats["dart_imports_replaced"] = total
    print(f"  [OK] {total} Flutter replacements")


def step_pyproject():
    """Step 6: Update pyproject.toml."""
    print("\n=== Step 6: Update pyproject.toml ===")

    toml = ROOT / "pyproject.toml"
    content = toml.read_text(encoding="utf-8")
    original = content

    # Package directory
    content = content.replace(
        'packages = ["src/jarvis"]', 'packages = ["src/cognithor", "src/jarvis"]'
    )

    # Entry points: keep jarvis as alias, update module path
    content = content.replace(
        'cognithor = "jarvis.__main__:main"',
        'cognithor = "cognithor.__main__:main"',
    )
    content = content.replace(
        'jarvis = "jarvis.__main__:main"',
        'jarvis = "cognithor.__main__:main"',
    )

    # Ruff/mypy tool sections
    content = content.replace("src/jarvis", "src/cognithor")

    if content != original:
        toml.write_text(content, encoding="utf-8")
        stats["files_modified"] += 1
        print("  [OK] pyproject.toml updated")
    else:
        print("  [SKIP] No changes needed")


def step_readme():
    """Step 7: Update README references."""
    print("\n=== Step 7: Update README ===")

    readme = ROOT / "README.md"
    if not readme.exists():
        return

    replacements = [
        ("python -m jarvis", "python -m cognithor"),
        ("src/jarvis/", "src/cognithor/"),
        ("from jarvis.", "from cognithor."),
        ("import jarvis", "import cognithor"),
    ]

    # Do NOT replace "Jarvis" personality name or historical references
    count = replace_in_file(
        readme,
        replacements,
        skip_patterns=[
            "Think of it as",  # "local Jarvis" analogy
            "personal",  # "personal AI assistant"
            "Jarvis --",  # Banner
        ],
    )
    print(f"  [OK] {count} README replacements")


def step_compat_shim():
    """Step 8: Create backwards-compat jarvis package."""
    print("\n=== Step 8: Create jarvis compat shim ===")

    shim_dir = SRC / "jarvis"
    shim_dir.mkdir(exist_ok=True)

    shim = shim_dir / "__init__.py"
    shim.write_text(
        '"""Backwards compatibility -- jarvis is now cognithor."""\n'
        "import importlib\n"
        "import sys\n"
        "import warnings\n"
        "\n"
        "warnings.warn(\n"
        "    \"The 'jarvis' package is deprecated. Use 'import cognithor' instead.\",\n"
        "    DeprecationWarning,\n"
        "    stacklevel=2,\n"
        ")\n"
        "\n"
        "from cognithor import *  # noqa: F401,F403\n"
        "from cognithor import BANNER_ASCII, PRODUCT_FULL, PRODUCT_NAME, __author__, __version__\n"
        "\n"
        "\n"
        "class _JarvisCompat:\n"
        '    """Redirect jarvis.* imports to cognithor.*"""\n'
        "\n"
        "    def find_module(self, fullname, path=None):\n"
        '        if fullname.startswith("jarvis."):\n'
        "            return self\n"
        "        return None\n"
        "\n"
        "    def load_module(self, fullname):\n"
        '        new_name = "cognithor" + fullname[len("jarvis"):]\n'
        "        if new_name not in sys.modules:\n"
        "            importlib.import_module(new_name)\n"
        "        sys.modules[fullname] = sys.modules[new_name]\n"
        "        return sys.modules[new_name]\n"
        "\n"
        "\n"
        "sys.meta_path.insert(0, _JarvisCompat())\n",
        encoding="utf-8",
    )
    # git add the new shim
    subprocess.run(["git", "add", str(shim)], check=True, cwd=ROOT)
    print("  [OK] Created src/jarvis/__init__.py compat shim")


def main():
    print("=" * 60)
    print("  COGNITHOR RENAME: jarvis -> cognithor")
    print("=" * 60)

    # Verify we're in the right directory
    if not (ROOT / "pyproject.toml").exists():
        print("[ERROR] Run from project root")
        sys.exit(1)

    step_git_mv()
    step_python_imports()
    step_env_vars()
    step_home_paths()
    step_flutter()
    step_pyproject()
    step_readme()
    step_compat_shim()

    print("\n" + "=" * 60)
    print("  RENAME COMPLETE")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    print("  Next steps:")
    print("  1. Run: python -m pytest tests/ -x -q")
    print("  2. Run: ruff check src/ tests/ --select=F821,F811")
    print("  3. Run: cd flutter_app && flutter build web --release")
    print("  4. git add -A && git commit")


if __name__ == "__main__":
    main()
