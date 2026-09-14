"""
Cognithor · Startup Checker -- Auto-Dependency Loading at Startup.

Verifies that all runtime dependencies are available and attempts to
auto-install or auto-start missing components:
  - Python optional-dependency groups
  - Ollama server
  - LLM models
  - Directory structure
  - Node.js dependencies (UI)

Usage:
    from cognithor.core.startup_check import StartupChecker
    checker = StartupChecker(config)
    report = checker.check_and_fix_all()
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# ============================================================================
# Dependency mapping: pip-package-name -> import-module-name
# ============================================================================

# Packages whose import name differs from their pip name
_IMPORT_NAME_MAP: dict[str, str] = {
    "beautifulsoup4": "bs4",
    "python-telegram-bot": "telegram",
    "faster-whisper": "faster_whisper",
    "piper-tts": "piper",
    "fpdf2": "fpdf",
    "python-docx": "docx",
    "ddgs": "ddgs",
    "sqlite-vec": "sqlite_vec",
    "faiss-cpu": "faiss",
    "uvicorn": "uvicorn",
    "webrtcvad": "webrtcvad",
    "sounddevice": "sounddevice",
    "apscheduler": "apscheduler",
    "croniter": "croniter",
    "google-auth": "google.auth",
    "google-api-core": "google.api_core",
    "psycopg": "psycopg",
    "psycopg-pool": "psycopg_pool",
    "pgvector": "pgvector",
    "elevenlabs": "elevenlabs",
    "irc": "irc",
    "twitchio": "twitchio",
}

# Optional dependency groups as declared in pyproject.toml
OPTIONAL_GROUPS: dict[str, list[str]] = {
    "memory": ["numpy", "sqlite-vec", "beautifulsoup4"],
    "vector": ["faiss-cpu"],
    "mcp": ["mcp"],
    "telegram": ["python-telegram-bot"],
    "web": ["fastapi", "uvicorn", "websockets"],
    "voice": ["faster-whisper", "piper-tts", "sounddevice"],
    "search": ["trafilatura", "ddgs"],
    "documents": ["fpdf2", "python-docx"],
    "cron": ["apscheduler", "croniter"],
}

# Default Ollama URL
_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


# ============================================================================
# StartupReport
# ============================================================================


@dataclass
class StartupReport:
    """Aggregated result of all startup checks.

    Attributes:
        checks_passed: List of checks that succeeded without intervention.
        fixes_applied: List of auto-fixes that were applied (e.g. packages installed).
        warnings: List of non-blocking warnings.
        errors: List of hard errors (informational -- we don't block startup).
    """

    checks_passed: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if no errors were recorded."""
        return len(self.errors) == 0

    def merge(self, other: StartupReport) -> None:
        """Merge another report into this one."""
        self.checks_passed.extend(other.checks_passed)
        self.fixes_applied.extend(other.fixes_applied)
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)


# ============================================================================
# Helper functions
# ============================================================================


def _import_name(pip_package: str) -> str:
    """Resolve the importable module name for a pip package name.

    For most packages the import name equals the pip name (lowered,
    hyphens replaced by underscores).  For known exceptions we use
    ``_IMPORT_NAME_MAP``.
    """
    # Strip version specifiers that may have been left in (e.g. "mcp>=1.7")
    base = pip_package.split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip()
    if base in _IMPORT_NAME_MAP:
        return _IMPORT_NAME_MAP[base]
    return base.replace("-", "_")


def _can_import(module_name: str) -> bool:
    """Return True if *module_name* is importable."""
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def _pip_install(
    packages: list[str], *, quiet: bool = True, timeout: int = 300
) -> tuple[bool, str]:
    """Run ``pip install`` for the given packages.

    Returns (success, stderr_output).
    """
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    if quiet:
        cmd.append("--quiet")
    cmd.append("--disable-pip-version-check")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "pip install timed out"
    except Exception as exc:
        return False, str(exc)


def _http_get_json(url: str, timeout: int = 5) -> dict[str, Any] | None:
    """Perform a simple HTTP GET and return parsed JSON, or None on failure."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())  # type: ignore[no-any-return]
    except Exception:
        return None


# ============================================================================
# StartupChecker
# ============================================================================


class StartupChecker:
    """Comprehensive startup dependency checker.

    Parameters:
        config: The loaded CognithorConfig object.  May be ``None`` for
                unit-testing individual methods.
    """

    def __init__(self, config: Any = None, *, auto_install: bool = False) -> None:
        self._config = config
        self._auto_install = auto_install

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def check_and_fix_all(self) -> StartupReport:
        """Run all checks and return an aggregated report.

        This method is **idempotent** and safe to run multiple times.
        It never blocks startup -- failures are recorded as warnings
        or errors in the report.
        """
        report = StartupReport()

        # 1. Python packages
        try:
            pkg_report = self.check_python_packages()
            report.merge(pkg_report)
        except Exception as exc:
            log.warning("startup_check_packages_error", error=str(exc))
            report.errors.append(f"Package check failed: {exc}")

        # 2. Ollama server
        try:
            ollama_report = self.check_ollama()
            report.merge(ollama_report)
        except Exception as exc:
            log.warning("startup_check_ollama_error", error=str(exc))
            report.errors.append(f"Ollama check failed: {exc}")

        # 3. LLM models (requires Ollama to be running)
        try:
            model_report = self.check_models()
            report.merge(model_report)
        except Exception as exc:
            log.warning("startup_check_models_error", error=str(exc))
            report.errors.append(f"Model check failed: {exc}")

        # 4. Directories
        try:
            dir_report = self.check_directories()
            report.merge(dir_report)
        except Exception as exc:
            log.warning("startup_check_dirs_error", error=str(exc))
            report.errors.append(f"Directory check failed: {exc}")

        # 5. Node modules — removed (legacy React UI replaced by Flutter)

        # Log summary (debug — clean startup output)
        log.debug(
            "startup_check_complete",
            passed=len(report.checks_passed),
            fixes=len(report.fixes_applied),
            warnings=len(report.warnings),
            errors=len(report.errors),
        )

        return report

    # ------------------------------------------------------------------
    # 1. Python packages
    # ------------------------------------------------------------------

    def check_python_packages(self) -> StartupReport:
        """Verify optional dependency groups and auto-install missing ones.

        Iterates through ``OPTIONAL_GROUPS`` and checks whether each
        package is importable.  Missing packages are collected per group
        and installed via ``pip install``.
        """
        report = StartupReport()

        for group, packages in OPTIONAL_GROUPS.items():
            missing_pkgs: list[str] = []
            for pkg in packages:
                mod_name = _import_name(pkg)
                if _can_import(mod_name):
                    report.checks_passed.append(f"pkg:{mod_name}")
                else:
                    missing_pkgs.append(pkg)

            if not missing_pkgs:
                continue

            if not self._auto_install:
                # Without --auto-install: only warn, do not install
                msg = (
                    f"Missing [{group}]: {', '.join(missing_pkgs)} "
                    f"-- run with --auto-install or: pip install {' '.join(missing_pkgs)}"
                )
                report.warnings.append(msg)
                log.warning("startup_packages_missing", group=group, packages=missing_pkgs)
                continue

            # Attempt auto-install (only with explicit --auto-install)
            log.info(
                "startup_installing_packages",
                group=group,
                packages=missing_pkgs,
            )
            success, stderr = _pip_install(missing_pkgs)

            if success:
                report.fixes_applied.append(f"Installed [{group}]: {', '.join(missing_pkgs)}")
                log.info("startup_packages_installed", group=group, packages=missing_pkgs)
            else:
                msg = f"Failed to install [{group}]: {', '.join(missing_pkgs)}"
                if stderr:
                    msg += f" -- {stderr[:200]}"
                report.warnings.append(msg)
                log.warning("startup_packages_install_failed", group=group, error=stderr[:300])

        return report

    # ------------------------------------------------------------------
    # 2. Ollama server
    # ------------------------------------------------------------------

    def check_ollama(self) -> StartupReport:
        """Check whether Ollama is running; auto-start if possible.

        Only relevant for backends that use Ollama (``ollama``, ``lmstudio``
        with Ollama-based models).  Cloud backends skip this check entirely.

        Uses the same discovery pattern as ``bootstrap_windows.py``:
        PATH lookup, then LOCALAPPDATA, then Program Files.
        """
        report = StartupReport()

        # Skip Ollama check for cloud backends
        if self._config is not None:
            backend_type = getattr(self._config, "llm_backend_type", "ollama")
            if backend_type not in ("ollama", "lmstudio"):
                report.checks_passed.append(f"Backend is {backend_type} -- Ollama check skipped")
                return report

        ollama_url = _OLLAMA_URL
        if self._config is not None:
            ollama_url = getattr(getattr(self._config, "ollama", None), "base_url", _OLLAMA_URL)

        if self._ollama_is_running(ollama_url):
            report.checks_passed.append("Ollama running")
            log.debug("startup_ollama_running")
            return report

        # Check if using remote mode (config.ollama.mode or URL heuristic)
        _ollama_mode = (
            getattr(getattr(self._config, "ollama", None), "mode", "local")
            if self._config
            else "local"
        )
        _is_remote = _ollama_mode == "remote" or not any(
            h in ollama_url for h in ("localhost", "127.0.0.1", "0.0.0.0", "::1")
        )
        if _is_remote:
            # Remote server not reachable — warn but don't try to start locally
            report.warnings.append(
                f"Remote Ollama server at {ollama_url} not reachable. "
                f"Check the server is running and the URL is correct."
            )
            log.warning("startup_remote_ollama_unreachable", url=ollama_url)
            return report

        # Not running (local mode)
        if not self._auto_install:
            # Without --auto-install: only warn, do not auto-start
            report.warnings.append(
                "Ollama not running -- run with --auto-install to auto-start, "
                "or start manually: ollama serve"
            )
            log.warning("startup_ollama_not_running")
            return report

        # Try to find and start it locally (only with explicit --auto-install)
        ollama_path = self._find_ollama()
        if ollama_path is None:
            report.warnings.append("Ollama not found. Install from https://ollama.com/download")
            log.warning("startup_ollama_not_found")
            return report

        log.info("startup_starting_ollama", path=ollama_path)
        started = self._start_ollama(ollama_path, ollama_url)

        if started:
            report.fixes_applied.append(f"Ollama auto-started ({ollama_path})")
            log.info("startup_ollama_started")
        else:
            report.warnings.append(
                f'Ollama found but could not be started. Start manually: "{ollama_path}" serve'
            )
            log.warning("startup_ollama_start_failed")

        return report

    # ------------------------------------------------------------------
    # 3. LLM models
    # ------------------------------------------------------------------

    # Backends where models are accessed via API, not downloaded locally
    _CLOUD_BACKENDS = frozenset(
        {
            "openai",
            "anthropic",
            "gemini",
            "groq",
            "deepseek",
            "mistral",
            "together",
            "openrouter",
            "xai",
            "cerebras",
            "github",
            "bedrock",
            "huggingface",
            "moonshot",
        }
    )

    def check_models(self) -> StartupReport:
        """Check if required LLM models are available; auto-pull if missing.

        Only runs for local backends (ollama, lmstudio).  Cloud backends
        (OpenAI, Anthropic, etc.) access models via API — no local
        download needed.
        """
        report = StartupReport()

        if self._config is None:
            report.warnings.append("No config provided -- model check skipped")
            return report

        # Skip model pulling for cloud backends
        backend_type = getattr(self._config, "llm_backend_type", "ollama")
        if backend_type in self._CLOUD_BACKENDS:
            report.checks_passed.append(f"Cloud backend ({backend_type}) -- model pull skipped")
            log.debug("startup_skip_model_pull_cloud", backend=backend_type)
            return report

        ollama_url = getattr(getattr(self._config, "ollama", None), "base_url", _OLLAMA_URL)

        # Gather required model names from config
        required_models: list[str] = []
        models_cfg = getattr(self._config, "models", None)
        if models_cfg is not None:
            for attr in ("planner", "executor", "coder", "embedding"):
                model_cfg = getattr(models_cfg, attr, None)
                if model_cfg is not None:
                    name = getattr(model_cfg, "name", None)
                    if name:
                        required_models.append(name)

        if not required_models:
            report.checks_passed.append("No models configured")
            return report

        # Query installed models
        data = _http_get_json(f"{ollama_url}/api/tags")
        if data is None:
            report.warnings.append("Cannot reach Ollama API -- model check skipped")
            return report

        installed_raw = [m.get("name", "") for m in data.get("models", [])]
        installed_lower = [m.lower() for m in installed_raw]

        ollama_path = self._find_ollama()

        for model in required_models:
            if self._model_installed(model, installed_lower):
                report.checks_passed.append(f"model:{model}")
                continue

            if not self._auto_install:
                # Without --auto-install: only warn, do not pull
                report.warnings.append(
                    f"Model '{model}' missing -- run with --auto-install or: ollama pull {model}"
                )
                log.warning("startup_model_missing", model=model)
                continue

            # Attempt auto-pull (only with explicit --auto-install)
            if ollama_path is None:
                report.warnings.append(
                    f"Model '{model}' missing but Ollama binary not found for pull"
                )
                continue

            log.info("startup_pulling_model", model=model)
            pulled = self._pull_model(model, ollama_path)

            if pulled:
                report.fixes_applied.append(f"Pulled model: {model}")
                log.info("startup_model_pulled", model=model)
            else:
                report.warnings.append(
                    f"Failed to pull model '{model}'. Run manually: ollama pull {model}"
                )
                log.warning("startup_model_pull_failed", model=model)

        return report

    # ------------------------------------------------------------------
    # 4. Directories
    # ------------------------------------------------------------------

    def check_directories(self) -> StartupReport:
        """Verify the directory structure exists; create if missing.

        Uses config.cognithor_home as the base path and ensures standard
        subdirectories are present.
        """
        report = StartupReport()

        if self._config is None:
            report.warnings.append("No config -- directory check skipped")
            return report

        cognithor_home = getattr(self._config, "cognithor_home", None)
        if cognithor_home is None:
            report.warnings.append("cognithor_home not set -- directory check skipped")
            return report

        base = Path(str(cognithor_home))
        subdirs = [
            "memory",
            "memory/episodes",
            "memory/knowledge",
            "memory/procedures",
            "memory/sessions",
            "index",
            "logs",
            "cache",
            "cache/web_search",
            "vault",
            "policies",
            "skills",
        ]

        for sub in subdirs:
            target = base / sub
            if target.is_dir():
                report.checks_passed.append(f"dir:{sub}")
            else:
                try:
                    target.mkdir(parents=True, exist_ok=True)
                    report.fixes_applied.append(f"Created directory: {target}")
                    log.info("startup_dir_created", path=str(target))
                except Exception as exc:
                    report.errors.append(f"Cannot create {target}: {exc}")
                    log.warning("startup_dir_create_failed", path=str(target), error=str(exc))

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_repo_root(self) -> str | None:
        """Try to locate the repository root from the cognithor package location."""
        try:
            import cognithor

            pkg_dir = Path(cognithor.__file__).resolve().parent  # src/cognithor
            # src/cognithor -> src -> repo_root
            candidate = pkg_dir.parent.parent
            if (candidate / "pyproject.toml").is_file():
                return str(candidate)
        except Exception:
            log.debug("startup_check_repo_root_detection_failed", exc_info=True)
        return None

    @staticmethod
    def _ollama_is_running(ollama_url: str = _OLLAMA_URL) -> bool:
        """Return True if the Ollama server responds."""
        try:
            req = urllib.request.Request(f"{ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    @staticmethod
    def _find_ollama() -> str | None:
        """Locate the Ollama binary (PATH, LOCALAPPDATA, Program Files)."""
        path = shutil.which("ollama")
        if path:
            return path

        if platform.system() == "Windows":
            local_app = os.environ.get("LOCALAPPDATA", "")
            if local_app:
                candidate = os.path.join(local_app, "Programs", "Ollama", "ollama.exe")
                if os.path.isfile(candidate):
                    return candidate
            prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            candidate2 = os.path.join(prog_files, "Ollama", "ollama.exe")
            if os.path.isfile(candidate2):
                return candidate2
        else:
            # Linux/macOS common paths
            for p in ["/usr/local/bin/ollama", "/usr/bin/ollama", "/opt/homebrew/bin/ollama"]:
                if os.path.isfile(p):
                    return p

        return None

    @staticmethod
    def _start_ollama(
        ollama_path: str,
        ollama_url: str = _OLLAMA_URL,
        max_wait: float = 15.0,
    ) -> bool:
        """Start Ollama serve and wait until the API responds."""
        try:
            kwargs: dict[str, Any] = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if platform.system() == "Windows":
                CREATE_NO_WINDOW = 0x08000000
                kwargs["creationflags"] = CREATE_NO_WINDOW

            subprocess.Popen([ollama_path, "serve"], **kwargs)

            # Poll until ready
            deadline = time.monotonic() + max_wait
            while time.monotonic() < deadline:
                time.sleep(0.5)
                if StartupChecker._ollama_is_running(ollama_url):
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def _model_installed(model_name: str, installed_lower: list[str]) -> bool:
        """Check if a model is installed (handles :latest vs :tag matching)."""
        name_lower = model_name.lower()
        base = name_lower.split(":")[0]

        for installed in installed_lower:
            if name_lower == installed:
                return True
            # "qwen3:8b" matches "qwen3:8b" or "qwen3:8b-<variant>"
            if installed.startswith(base + ":"):
                # If the requested name has a tag, require exact match
                if ":" in name_lower:
                    tag = name_lower.split(":", 1)[1]
                    inst_tag = installed.split(":", 1)[1]
                    if tag == inst_tag or inst_tag.startswith(tag):
                        return True
                else:
                    # No specific tag requested -- any version matches
                    return True
        return False

    @staticmethod
    def _pull_model(model: str, ollama_path: str, timeout: int = 1800) -> bool:
        """Pull a model via ``ollama pull``."""
        try:
            result = subprocess.run(
                [ollama_path, "pull", model],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            log.warning("startup_model_pull_timeout", model=model, timeout=timeout)
            return False
        except Exception as exc:
            log.warning("startup_model_pull_error", model=model, error=str(exc))
            return False
