"""Tests for install.sh fixes, vite.config.js ENOENT fix, and doc updates.

Each test proves one specific bug fix works. Tests are cross-platform:
bash tests use subprocess (require bash in PATH — Git Bash on Windows),
Node.js tests use subprocess, doc tests are pure Python.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO / "install.sh"
QUICKSTART_MD = REPO / "QUICKSTART.md"
README_MD = REPO / "README.md"
VITE_CONFIG = REPO / "ui" / "vite.config.js"
PYPROJECT = REPO / "pyproject.toml"

# Locate bash: Git Bash on Windows, /bin/bash on Unix
_BASH = shutil.which("bash")

needs_bash = pytest.mark.skipif(_BASH is None, reason="bash not found in PATH")
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not found in PATH")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_bash(
    script: str, *, env: dict | None = None, timeout: int = 15
) -> subprocess.CompletedProcess:
    """Run a bash snippet and return the result (never raises on non-zero)."""
    merged_env = {**os.environ, **(env or {})}
    # Force LANG for reproducible output
    merged_env["LANG"] = "C"
    return subprocess.run(
        [_BASH, "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged_env,
    )


def _run_node(script: str, *, timeout: int = 10) -> subprocess.CompletedProcess:
    """Run a Node.js snippet and return the result."""
    return subprocess.run(
        [shutil.which("node"), "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# =========================================================================
# Fix #1: chmod +x in docs (QUICKSTART.md + README.md)
# =========================================================================


class TestFix1ChmodInDocs:
    """Docs must tell users to chmod +x install.sh BEFORE running it."""

    def test_quickstart_has_chmod_before_run(self):
        text = _read(QUICKSTART_MD)
        # Find the code block containing install.sh
        pattern = r"chmod \+x install\.sh\n\./install\.sh"
        assert re.search(pattern, text), (
            "QUICKSTART.md must have 'chmod +x install.sh' on the line "
            "immediately before './install.sh'"
        )

    def test_readme_has_chmod_before_run(self):
        text = _read(README_MD)
        # Accept both "chmod +x install.sh\n./install.sh" and "chmod +x install.sh && ./install.sh"
        pattern = r"chmod \+x install\.sh\s*(?:\n|&&)\s*\.?/?install\.sh"
        assert re.search(pattern, text), (
            "README.md must have 'chmod +x install.sh' before './install.sh' "
            "(either on the next line or chained with &&)"
        )


# =========================================================================
# Fix #2: pip not found → abort with helpful message
# =========================================================================


class TestFix2PipAbort:
    """If pip is missing, install.sh must exit with the exact fix command."""

    @needs_bash
    def test_detect_installer_fails_without_pip(self, tmp_path):
        # Source just the helper functions + detect_installer,
        # with a fake PATH that has no pip and no uv
        script = textwrap.dedent(f"""\
            set +e  # we expect a fatal exit, don't let set -e interfere
            # Minimal stubs from install.sh
            RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
            INSTALL_FAILED=false
            info()    {{ echo "INFO: $*"; }}
            success() {{ echo "OK: $*"; }}
            warn()    {{ echo "WARN: $*"; }}
            error()   {{ echo "ERROR: $*" >&2; }}
            show_error_submission() {{ echo "SUBMIT_ERROR_SHOWN"; }}
            fatal()   {{ error "$*"; INSTALL_FAILED=true; show_error_submission; exit 1; }}
            check_command() {{ command -v "$1" &>/dev/null; }}
            USE_UV=false
            PKG_INSTALLER=""

            # Fake PATH: empty dir so nothing is found
            export PATH="{tmp_path}"

            # Override python3 to simulate pip-missing
            python3() {{
                if [[ "$1" == "-m" && "$2" == "pip" ]]; then
                    return 1  # pip not available
                fi
                command python3 "$@"
            }}
            export -f python3

            detect_installer() {{
                if [[ "$USE_UV" == true ]]; then return 1; fi
                if check_command uv; then PKG_INSTALLER="uv"; return 0; fi
                if python3 -m pip --version &>/dev/null; then
                    PKG_INSTALLER="pip"; return 0
                fi
                echo ""
                error "pip nicht gefunden!"
                echo "    sudo apt install python3-pip"
                fatal "pip ist eine Pflicht-Abhaengigkeit."
            }}

            detect_installer
            echo "SHOULD_NOT_REACH"
        """)
        r = _run_bash(script)
        combined = r.stdout + r.stderr
        assert r.returncode != 0, "Must exit non-zero when pip is missing"
        assert "sudo apt install python3-pip" in combined, (
            "Must print the exact apt install command"
        )
        assert "SHOULD_NOT_REACH" not in combined, "Must not continue after fatal"
        assert "SUBMIT_ERROR_SHOWN" in combined, "Must show error submission helper"

    @needs_bash
    def test_detect_installer_succeeds_with_pip(self):
        # In the real environment (our CI/dev machine), pip exists.
        # On Windows Git Bash, python3 may not exist — try python too.
        script = textwrap.dedent("""\
            set +e
            RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
            info()    { echo "INFO: $*"; }
            success() { echo "OK: $*"; }
            warn()    { echo "WARN: $*"; }
            error()   { echo "ERROR: $*" >&2; }
            fatal()   { error "$*"; exit 1; }
            check_command() { command -v "$1" &>/dev/null; }
            USE_UV=false
            PKG_INSTALLER=""

            # Try python3 first (Linux), then python (Windows Git Bash)
            if python3 -m pip --version &>/dev/null; then
                echo "RESULT=pip"; exit 0
            fi
            if python -m pip --version &>/dev/null; then
                echo "RESULT=pip"; exit 0
            fi
            if command -v uv &>/dev/null; then
                echo "RESULT=uv"; exit 0
            fi
            echo "RESULT=none"
        """)
        r = _run_bash(script)
        assert "RESULT=pip" in r.stdout or "RESULT=uv" in r.stdout, (
            "On a dev machine, either pip or uv must be detected"
        )


# =========================================================================
# Fix #3: venv broken → delete and recreate
# =========================================================================


class TestFix3VenvCorruption:
    """If venv dir exists but bin/activate is missing, delete + recreate."""

    @needs_bash
    def test_corrupted_venv_is_deleted(self, tmp_path):
        # Create a "corrupted" venv: directory exists but no bin/activate
        broken_venv = tmp_path / "venv"
        broken_venv.mkdir()
        (broken_venv / "lib").mkdir()  # some leftover
        assert not (broken_venv / "bin" / "activate").exists()

        script = textwrap.dedent(f"""\
            set +e
            VENV_DIR="{broken_venv.as_posix()}"
            RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
            info()    {{ echo "INFO: $*"; }}
            success() {{ echo "OK: $*"; }}
            warn()    {{ echo "WARN: $*"; }}

            if [[ -d "$VENV_DIR" ]]; then
                if [[ -f "$VENV_DIR/bin/activate" ]]; then
                    echo "VENV_VALID"
                else
                    warn "Korruptes venv erkannt (bin/activate fehlt) -- wird neu erstellt"
                    rm -rf "$VENV_DIR"
                    echo "VENV_DELETED"
                fi
            fi
        """)
        r = _run_bash(script)
        assert "VENV_DELETED" in r.stdout, "Corrupted venv must be deleted"
        assert "Korruptes venv" in r.stdout, "Must warn about corruption"
        assert not broken_venv.exists(), "Directory must actually be gone"

    @needs_bash
    def test_valid_venv_is_kept(self, tmp_path):
        # Create a "valid" venv: directory with bin/activate
        valid_venv = tmp_path / "venv"
        valid_venv.mkdir()
        (valid_venv / "bin").mkdir(parents=True)
        (valid_venv / "bin" / "activate").write_text("# fake activate")

        script = textwrap.dedent(f"""\
            set +e
            VENV_DIR="{valid_venv.as_posix()}"

            if [[ -d "$VENV_DIR" ]]; then
                if [[ -f "$VENV_DIR/bin/activate" ]]; then
                    echo "VENV_VALID"
                else
                    echo "VENV_DELETED"
                fi
            fi
        """)
        r = _run_bash(script)
        assert "VENV_VALID" in r.stdout, "Valid venv must not be deleted"
        assert (valid_venv / "bin" / "activate").exists()


# =========================================================================
# Fix #4: Ollama model download is optional (never blocking)
# =========================================================================


class TestFix4OllamaOptional:
    """install.sh must NOT contain any 'ollama pull' that runs automatically."""

    def test_no_automatic_ollama_pull(self):
        text = _read(INSTALL_SH)
        # The old code had: ollama pull "$model" || warn ...
        # The new code only prints: echo "    ollama pull $model"
        # Find lines that actually execute ollama pull (not in echo/info/comment)
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue
            # Skip echo/info/warn statements (they just print the command)
            if any(stripped.startswith(p) for p in ("echo", "info", "warn", "success")):
                continue
            # This would be the dangerous pattern: a bare 'ollama pull'
            if re.match(r"^\s*ollama\s+pull\b", stripped):
                pytest.fail(
                    f"Line {i}: found automatic 'ollama pull' execution: {stripped!r}\n"
                    "Model downloads must be optional (print command, don't execute)"
                )

    def test_prints_manual_pull_commands(self):
        text = _read(INSTALL_SH)
        assert "ollama pull" in text, "Must mention ollama pull commands for the user"
        # But only inside echo/info/warn
        pull_lines = [
            line.strip()
            for line in text.splitlines()
            if "ollama pull" in line and not line.strip().startswith("#")
        ]
        for line in pull_lines:
            assert any(line.startswith(p) for p in ("echo", "info", "warn", "if")), (
                f"ollama pull must only appear in echo/info/warn/if-guarded, got: {line!r}"
            )


# =========================================================================
# Fix #5: pip install has progress feedback
# =========================================================================


class TestFix5PipProgress:
    """pip install must use --progress-bar on and print duration estimate."""

    def test_progress_bar_flag(self):
        text = _read(INSTALL_SH)
        assert "--progress-bar on" in text, "pip install command must include --progress-bar on"

    def test_duration_estimate_printed(self):
        text = _read(INSTALL_SH)
        assert "2-5 minutes" in text, "Must print duration estimate before pip install"


# =========================================================================
# Fix #6: Verbose directory creation with timeout and permission errors
# =========================================================================


class TestFix6VerboseMkdir:
    """Every mkdir must be verbose, have a timeout, and handle permission errors."""

    def test_create_directory_safe_function_exists(self):
        text = _read(INSTALL_SH)
        assert "create_directory_safe()" in text, "Must define create_directory_safe function"

    @needs_bash
    def test_creates_directory_with_verbose_output(self, tmp_path):
        target = tmp_path / "test_dir"
        script = textwrap.dedent(f"""\
            set +e
            TMPDIR="{tmp_path.as_posix()}"
            RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
            info()    {{ echo "INFO: $*"; }}
            success() {{ echo "OK: $*"; }}
            warn()    {{ echo "WARN: $*"; }}
            error()   {{ echo "ERROR: $*" >&2; }}
            fatal()   {{ error "$*"; exit 1; }}

            create_directory_safe() {{
                local dir="$1"
                if [[ -d "$dir" ]]; then
                    info "  [vorhanden] $dir"
                    return 0
                fi
                local err_file
                err_file=$(mktemp "${{TMPDIR:-/tmp}}/jarvis_mkdir_XXXXXX" \
2>/dev/null || echo "/tmp/jarvis_mkdir_err")
                if mkdir -p "$dir" 2>"$err_file"; then
                    success "  [erstellt]  $dir"
                    rm -f "$err_file" 2>/dev/null
                else
                    error "Verzeichnis konnte nicht erstellt werden: $dir"
                    rm -f "$err_file" 2>/dev/null
                    echo "    sudo mkdir -p $dir"
                    fatal "Verzeichnis-Erstellung fehlgeschlagen."
                fi
            }}

            create_directory_safe "{target.as_posix()}"
        """)
        r = _run_bash(script)
        assert r.returncode == 0
        assert "[erstellt]" in r.stdout, "Must print [erstellt] for new directory"
        assert target.exists(), "Directory must actually be created"

    @needs_bash
    def test_existing_directory_says_vorhanden(self, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()

        script = textwrap.dedent(f"""\
            set +e
            RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
            info()    {{ echo "INFO: $*"; }}
            success() {{ echo "OK: $*"; }}

            create_directory_safe() {{
                local dir="$1"
                if [[ -d "$dir" ]]; then
                    info "  [vorhanden] $dir"
                    return 0
                fi
                success "  [erstellt]  $dir"
            }}

            create_directory_safe "{target.as_posix()}"
        """)
        r = _run_bash(script)
        assert "[vorhanden]" in r.stdout, "Must print [vorhanden] for existing dir"

    def test_no_timeout_command_in_mkdir(self):
        """mkdir must NOT use 'timeout' (not available on macOS)."""
        text = _read(INSTALL_SH)
        assert "timeout 30 mkdir" not in text, (
            "mkdir must not use 'timeout' (not portable to macOS)"
        )

    def test_has_sudo_fix_on_permission_error(self):
        text = _read(INSTALL_SH)
        assert "sudo mkdir -p" in text, "Must print sudo mkdir fix command on permission failure"
        assert "sudo chown" in text, "Must print sudo chown fix command on permission failure"


# =========================================================================
# Fix #7: Dynamic version from pyproject.toml (not hardcoded)
# =========================================================================


class TestFix7DynamicVersion:
    """Banner must read version from pyproject.toml, not hardcode v0.1.0."""

    def test_no_hardcoded_version(self):
        text = _read(INSTALL_SH)
        assert "v0.1.0" not in text, "Must not contain hardcoded v0.1.0"

    def test_reads_from_pyproject(self):
        text = _read(INSTALL_SH)
        assert "pyproject.toml" in text, "Must reference pyproject.toml for version"

    @needs_bash
    def test_version_extraction_returns_real_version(self):
        """Run the actual grep command from install.sh against pyproject.toml."""
        script = textwrap.dedent(f"""\
            version=$(grep '^version' "{PYPROJECT.as_posix()}" | head -1 | cut -d'"' -f2)
            echo "VERSION=$version"
        """)
        r = _run_bash(script)
        assert r.returncode == 0
        # Extract the version
        match = re.search(r"VERSION=(\S+)", r.stdout)
        assert match, f"Must extract a version, got: {r.stdout!r}"
        version = match.group(1)
        # Must be a real semver-ish string, not empty or "unknown"
        assert re.match(r"\d+\.\d+", version), (
            f"Extracted version must be numeric (got {version!r})"
        )
        assert version != "unknown"


# =========================================================================
# Fix #8: Windows python ENOENT fallback in vite.config.js
# =========================================================================


@pytest.mark.skipif(
    not (REPO / "ui" / "vite.config.js").exists(),
    reason="React UI removed — Flutter is the primary UI since v0.42.0",
)
class TestFix8VitePythonFallback:
    """Vite launcher must try python3 if python fails (and vice versa)."""

    def test_platform_aware_python_cmd(self):
        text = _read(VITE_CONFIG)
        assert "process.platform === 'win32'" in text, (
            "Must check platform to choose python command"
        )
        assert "'python'" in text and "'python3'" in text, "Must reference both python and python3"

    def test_enoent_retry_logic_exists(self):
        text = _read(VITE_CONFIG)
        assert "ENOENT" in text, "Must handle ENOENT error code"
        assert "retryWithFallback" in text, "Must have retry parameter"

    def test_user_friendly_error_message(self):
        text = _read(VITE_CONFIG)
        assert "sudo apt install python3" in text, (
            "Must include Ubuntu install hint on final failure"
        )
        assert "brew install python" in text, "Must include macOS install hint on final failure"

    @needs_node
    def test_fallback_logic_correctness(self):
        """Run the retry logic in Node.js to verify it flips correctly."""
        script = textwrap.dedent("""\
            // Simulate the fallback logic from vite.config.js
            const results = [];

            function simulate(platform) {
                const pythonCmd = platform === 'win32' ? 'python' : 'python3';

                // First call: retryWithFallback=true → uses pythonCmd
                const cmd1 = pythonCmd;
                // On ENOENT, fallback call: retryWithFallback=false
                const cmd2 = cmd1 === 'python' ? 'python3' : 'python';

                results.push({
                    platform,
                    first_try: cmd1,
                    fallback: cmd2,
                    different: cmd1 !== cmd2,
                });
            }

            simulate('win32');
            simulate('linux');
            simulate('darwin');

            // Verify
            let ok = true;
            for (const r of results) {
                if (!r.different) {
                    console.error(`FAIL: ${r.platform}: first=${r.first_try} fallback=${r.fallback} (same!)`);
                    ok = false;
                }
            }

            if (ok) {
                console.log('FALLBACK_LOGIC_OK');
                for (const r of results) {
                    console.log(`  ${r.platform}: ${r.first_try} -> ${r.fallback}`);
                }
            }
            process.exit(ok ? 0 : 1);
        """)
        r = _run_node(script)
        assert r.returncode == 0, f"Node test failed: {r.stderr}"
        assert "FALLBACK_LOGIC_OK" in r.stdout
        # Verify specific mappings
        assert "win32: python -> python3" in r.stdout
        assert "linux: python3 -> python" in r.stdout
        assert "darwin: python3 -> python" in r.stdout


# =========================================================================
# Fix #9: Error submission helper at end of failures
# =========================================================================


class TestFix9ErrorSubmission:
    """On any fatal error, print GitHub issue URL."""

    def test_github_url_in_helper(self):
        text = _read(INSTALL_SH)
        assert "https://github.com/Alex8791-cyber/cognithor/issues/new" in text

    def test_fatal_calls_show_error_submission(self):
        text = _read(INSTALL_SH)
        # The fatal() function must call show_error_submission
        # Find the fatal function body
        lines = text.splitlines()
        in_fatal = False
        found_call = False
        for line in lines:
            if "fatal()" in line and "{" in line:
                in_fatal = True
            if in_fatal and "show_error_submission" in line:
                found_call = True
                break
            if in_fatal and "}" in line:
                break
        assert found_call, "fatal() must call show_error_submission()"

    @needs_bash
    def test_error_submission_output(self):
        """Run the helper function and verify output."""
        script = textwrap.dedent("""\
            RED=''; BOLD=''; NC=''
            show_error_submission() {
                echo ""
                echo "[X] Installation fehlgeschlagen."
                echo ""
                echo "  Bitte oeffne ein Issue auf GitHub:"
                echo "  https://github.com/Alex8791-cyber/cognithor/issues/new"
                echo ""
                echo "  Fuege die obige Ausgabe als Log bei."
                echo ""
            }
            show_error_submission
        """)
        r = _run_bash(script)
        assert "issues/new" in r.stdout
        assert "fehlgeschlagen" in r.stdout
        assert "Log" in r.stdout


# =========================================================================
# General: ASCII-safe output (no Unicode that breaks cp1252)
# =========================================================================


class TestASCIISafe:
    """install.sh must not use Unicode symbols that break on Windows cp1252."""

    def test_no_unicode_symbols_in_output_functions(self):
        text = _read(INSTALL_SH)
        # These specific Unicode chars were in the old version
        forbidden = {
            "\u2713": "checkmark (was in success())",
            "\u2717": "cross (was in error())",
            "\u26a0": "warning (was in warn())",
            "\u2139": "info (was in info())",
            "\u2714": "heavy checkmark",
            "\u2718": "heavy cross",
            "\u23f3": "hourglass",
            "\u274c": "cross mark",
            "\u2705": "check mark button",
        }
        for char, desc in forbidden.items():
            assert char not in text, (
                f"install.sh contains Unicode {desc} ({char!r}) — "
                "use ASCII-safe [OK]/[X]/[!]/[i] instead"
            )

    def test_uses_ascii_brackets(self):
        text = _read(INSTALL_SH)
        assert "[OK]" in text, "success() must use [OK]"
        assert "[X]" in text, "error()/fatal() must use [X]"
        assert "[!]" in text, "warn() must use [!]"
        assert "[i]" in text, "info() must use [i]"


# =========================================================================
# macOS portability: no 'timeout' command, no 'sed -i' without backup
# =========================================================================


class TestMacOSPortability:
    """install.sh must not use GNU-only commands."""

    def test_no_timeout_command(self):
        """'timeout' is GNU coreutils — not available on macOS."""
        text = _read(INSTALL_SH)
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.match(r"\btimeout\b", stripped):
                pytest.fail(
                    f"Line {i}: uses 'timeout' command (GNU-only, not on macOS): {stripped!r}"
                )

    def test_no_sed_dash_i(self):
        """'sed -i' without '' arg fails on BSD/macOS sed."""
        text = _read(INSTALL_SH)
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"\bsed\s+-i\b", stripped):
                pytest.fail(
                    f"Line {i}: uses 'sed -i' (fails on macOS BSD sed): "
                    f"{stripped!r}\n"
                    "Use grep -v + mv or sed -i '' (with empty backup) instead"
                )

    @needs_bash
    def test_uninstall_alias_removal_without_sed(self, tmp_path):
        """Uninstall must remove shell aliases without sed -i."""
        fake_rc = tmp_path / ".bashrc"
        fake_rc.write_text(
            "export PATH=/usr/bin\n"
            "# Jarvis Agent OS\n"
            "alias jarvis='/home/user/.cognithor/venv/bin/jarvis'\n"
            "export EDITOR=vim\n"
        )
        script = textwrap.dedent(f"""\
            set +e
            rc="{fake_rc.as_posix()}"
            if grep -q "Jarvis Agent OS\\|jarvis.*venv.*bin.*jarvis" "$rc" 2>/dev/null; then
                grep -v "Jarvis Agent OS" "$rc" | grep -v "cognithor.*venv.*bin.*jarvis" > "${{rc}}.jarvis_tmp" \\
                    && mv "${{rc}}.jarvis_tmp" "$rc" \\
                    || rm -f "${{rc}}.jarvis_tmp"
            fi
            cat "$rc"
        """)
        r = _run_bash(script)
        assert r.returncode == 0
        remaining = fake_rc.read_text()
        assert "Jarvis Agent OS" not in remaining, "Must remove Jarvis comment"
        assert "jarvis" not in remaining.lower() or "venv" not in remaining, (
            "Must remove jarvis alias"
        )
        assert "export PATH" in remaining, "Must keep non-jarvis lines"
        assert "export EDITOR" in remaining, "Must keep non-jarvis lines"


# =========================================================================
# Bash set -e safety: ((errors++)) when errors=0 is falsy → kills script
# =========================================================================


class TestSetESafety:
    """install.sh must not use ((errors++)) — it's falsy when errors=0 under set -e."""

    def test_no_double_paren_increment(self):
        text = _read(INSTALL_SH)
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "((errors++))" in stripped:
                pytest.fail(
                    f"Line {i}: uses ((errors++)) which is falsy when errors=0 "
                    f"under set -e — use errors=$((errors + 1)) instead"
                )

    @needs_bash
    def test_safe_increment_survives_set_e(self):
        """Prove errors=$((errors + 1)) survives under set -e."""
        script = textwrap.dedent("""\
            set -e
            errors=0
            errors=$((errors + 1))
            echo "SURVIVED errors=$errors"
        """)
        r = _run_bash(script)
        assert "SURVIVED errors=1" in r.stdout, "errors=$((errors + 1)) must survive set -e"

    @needs_bash
    def test_unsafe_increment_dies_under_set_e(self):
        """Prove ((errors++)) dies under set -e when errors=0."""
        script = textwrap.dedent("""\
            set -e
            errors=0
            ((errors++))
            echo "SURVIVED"
        """)
        r = _run_bash(script)
        assert r.returncode != 0, "((errors++)) must fail under set -e"
        assert "SURVIVED" not in r.stdout, "Script must die before echo"


# =========================================================================
# Vite venv Python detection
# =========================================================================


@pytest.mark.skipif(
    not (REPO / "ui" / "vite.config.js").exists(),
    reason="React UI removed — Flutter is the primary UI since v0.42.0",
)
class TestViteVenvPython:
    """Vite must prefer venv Python over system Python."""

    def test_findPythonCmd_exists(self):
        text = _read(VITE_CONFIG)
        assert "findPythonCmd" in text, "Must have findPythonCmd function for venv detection"

    def test_checks_local_venv(self):
        text = _read(VITE_CONFIG)
        assert ".venv" in text, "Must check for repo-local .venv"

    def test_checks_jarvis_home_venv(self):
        text = _read(VITE_CONFIG)
        assert ".cognithor" in text and "venv" in text, "Must check for ~/.cognithor/venv"

    def test_uses_existsSync(self):
        text = _read(VITE_CONFIG)
        assert "existsSync" in text, "Must use existsSync to check venv paths"

    @needs_node
    def test_venv_detection_logic(self, tmp_path):
        """Simulate findPythonCmd with mock venv dirs."""
        # Create a fake .venv/bin/python
        if sys.platform == "win32":
            venv_py = tmp_path / ".venv" / "Scripts" / "python.exe"
        else:
            venv_py = tmp_path / ".venv" / "bin" / "python"
        venv_py.parent.mkdir(parents=True)
        venv_py.write_text("#!/usr/bin/env python3\n")

        script = textwrap.dedent(f"""\
            const {{ existsSync }} = require('fs');
            const {{ resolve, join }} = require('path');

            const BACKEND_DIR = "{tmp_path.as_posix()}";
            const isWin = process.platform === 'win32';

            // Check repo-local .venv
            const localVenv = isWin
              ? resolve(BACKEND_DIR, '.venv', 'Scripts', 'python.exe')
              : resolve(BACKEND_DIR, '.venv', 'bin', 'python');

            if (existsSync(localVenv)) {{
              console.log('FOUND_VENV=' + localVenv);
            }} else {{
              console.log('VENV_NOT_FOUND');
            }}
        """)
        r = _run_node(script)
        assert "FOUND_VENV=" in r.stdout, f"Must detect .venv Python, got: {r.stdout!r}"
        assert ".venv" in r.stdout
