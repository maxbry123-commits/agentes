"""Code-Tools fuer Cognithor -- Python-REPL und Code-Analyse als MCP-Tools.

Zwei Tools:
  - run_python: Fuehrt Python-Code in der Sandbox aus (temp-Datei + SandboxExecutor)
  - analyze_code: Kombiniert CodeSmellDetector + CodeAuditor fuer strukturierte Analyse

Factory: register_code_tools(mcp_client, config) → CodeTools

Bibel-Referenz: §5.3 (MCP-Tools), §4.3 (Sandbox)
"""

from __future__ import annotations

import contextlib
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cognithor.core.sandbox import (
    NetworkPolicy,
    SandboxConfig,
    SandboxExecutor,
    SandboxLevel,
)
from cognithor.i18n import t
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.config import CognithorConfig

log = get_logger(__name__)

# Maximale Code-Groesse (Default: 1 MB, ueberschreibbar via config.code.max_code_size)
_DEFAULT_MAX_CODE_SIZE = 1_048_576
_DEFAULT_TIMEOUT = 60

# Backward-compatible alias for external imports (tests, etc.)
MAX_CODE_SIZE = _DEFAULT_MAX_CODE_SIZE

__all__ = [
    "MAX_CODE_SIZE",
    "CodeTools",
    "register_code_tools",
]


class CodeTools:
    """Python-REPL und Code-Analyse mit Sandbox-Isolation.

    Security-Architektur:
      - run_python: Code wird als temp-Datei geschrieben und via SandboxExecutor ausgefuehrt
      - analyze_code: Read-only, risikolos (AST-basiert)
      - Workspace-Confinement: Alle temp-Dateien im Workspace
    """

    def __init__(self, config: CognithorConfig) -> None:
        self._config = config

        # Limits aus Config lesen (mit sicheren Defaults)
        _code = getattr(config, "code", None)
        self._max_code_size: int = getattr(_code, "max_code_size", _DEFAULT_MAX_CODE_SIZE)
        self._default_timeout: int = getattr(_code, "default_timeout_seconds", _DEFAULT_TIMEOUT)

        # Sandbox-Konfiguration: wire UI SandboxConfig → execution SandboxConfig
        _ui_sandbox = getattr(config, "sandbox", None)
        sandbox_config = SandboxConfig(
            workspace_dir=config.workspace_dir,
            default_timeout=self._default_timeout,
        )

        if _ui_sandbox is not None:
            _mem = getattr(_ui_sandbox, "max_memory_mb", None)
            if _mem and isinstance(_mem, int):
                sandbox_config.max_memory_mb = _mem
            _cpu = getattr(_ui_sandbox, "max_cpu_seconds", None)
            if _cpu and isinstance(_cpu, int):
                sandbox_config.max_cpu_seconds = _cpu
            _net = getattr(_ui_sandbox, "network_access", None)
            if _net is not None:
                sandbox_config.network = NetworkPolicy.ALLOW if _net else NetworkPolicy.BLOCK
            _level = getattr(_ui_sandbox, "level", None)
            if _level is not None:
                level_val = _level.value if hasattr(_level, "value") else str(_level)
                if level_val in ("bwrap", "firejail", "bare", "process"):
                    with contextlib.suppress(ValueError):
                        sandbox_config.preferred_level = SandboxLevel(level_val)

        # Legacy: direct config attributes (backward compat)
        sandbox_level = getattr(config, "sandbox_level", None)
        if sandbox_level and sandbox_level in ("bwrap", "firejail", "bare"):
            sandbox_config.preferred_level = SandboxLevel(sandbox_level)

        sandbox_network = getattr(config, "sandbox_network", None)
        if sandbox_network and sandbox_network in ("allow", "block"):
            sandbox_config.network = NetworkPolicy(sandbox_network)

        self._sandbox = SandboxExecutor(sandbox_config)
        self._workspace = config.workspace_dir

        log.info(
            "code_tools_init",
            sandbox_level=self._sandbox.level.value,
            workspace=str(self._workspace),
        )

    async def run_python(
        self,
        code: str,
        timeout: int | None = None,
        working_dir: str | None = None,
    ) -> str:
        """Fuehrt Python-Code in der Sandbox aus.

        Schreibt den Code in eine temporaere .py-Datei im Workspace,
        fuehrt sie ueber den SandboxExecutor aus und bereinigt anschliessend.

        Args:
            code: Python-Code als String.
            timeout: Timeout in Sekunden (Default: aus Config oder 60).
            working_dir: Arbeitsverzeichnis (Default: Workspace).

        Returns:
            Kombinierter stdout + stderr Output.
        """
        if timeout is None:
            timeout = self._default_timeout

        if not code.strip():
            return t("code.no_code")

        code_size = len(code.encode("utf-8"))
        if code_size > self._max_code_size:
            return t(
                "code.too_large",
                size=f"{code_size / 1_048_576:.1f}",
                max=f"{self._max_code_size / 1_048_576:.0f}",
            )

        # GUI-Erkennung: headless-Modus aktivieren wenn GUI-Bibliotheken erkannt
        _GUI_IMPORTS = ("pygame", "tkinter", "PyQt", "PySide", "wx.", "gi.repository.Gtk")
        _code_lower = code.lower()
        _is_gui = False
        for gui_lib in _GUI_IMPORTS:
            if (
                f"import {gui_lib.lower()}" in _code_lower
                or f"from {gui_lib.lower()}" in _code_lower
            ):
                _is_gui = True
                break

        cwd = working_dir or str(self._workspace)

        # Working-Directory validieren -- muss unter Workspace liegen
        cwd_path = Path(cwd).expanduser().resolve()
        workspace_root = self._workspace.expanduser().resolve()
        try:
            cwd_path.relative_to(workspace_root)
        except ValueError:
            return t("code.working_dir_denied", cwd=cwd, root=workspace_root)
        cwd_path.mkdir(parents=True, exist_ok=True)

        # Temp-Datei erstellen
        temp_name = f"_jarvis_run_{uuid.uuid4().hex[:12]}.py"
        temp_path = cwd_path / temp_name

        try:
            # GUI-Headless: Dummy-Treiber injizieren damit der Code laeuft
            # ohne echtes Display. Fehler im Code werden trotzdem erkannt.
            if _is_gui:
                headless_preamble = (
                    "import os as _os\n"
                    '_os.environ.setdefault("SDL_VIDEODRIVER", "dummy")\n'
                    '_os.environ.setdefault("SDL_AUDIODRIVER", "dummy")\n'
                    '_os.environ.setdefault("DISPLAY", ":0")\n'
                )
                code = headless_preamble + code
                # Kuerzeren Timeout fuer GUI-Tests (kein Fenster-Loop noetig)
                timeout = min(timeout, 10)
                log.info("gui_headless_mode", library=gui_lib)

            # Code in temp-Datei schreiben
            temp_path.write_text(code, encoding="utf-8")

            log.info(
                "run_python_start",
                temp_file=str(temp_path),
                code_lines=code.count("\n") + 1,
                timeout=timeout,
            )

            # Via Sandbox ausfuehren
            command = f"{sys.executable} {temp_name}"
            result = await self._sandbox.execute(
                command,
                working_dir=str(cwd_path),
                timeout=timeout,
            )

            log.info(
                "run_python_done",
                exit_code=result.exit_code,
                sandbox=result.sandbox_level,
                stdout_len=len(result.stdout),
                stderr_len=len(result.stderr),
                timed_out=result.timed_out,
            )

            output = result.output
            if _is_gui:
                if result.exit_code == 0 or result.timed_out:
                    output += "\n" + t("code.headless_ok")
                else:
                    output += "\n" + t("code.headless_error", exit_code=result.exit_code)
            return output

        finally:
            # Temp-Datei bereinigen
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass  # Best-effort temp file cleanup, non-critical

    async def analyze_code(
        self,
        code: str = "",
        file_path: str = "",
    ) -> str:
        """Analysiert Python-Code auf Smells und Sicherheitsprobleme.

        Kombiniert CodeSmellDetector (Qualitaet) und CodeAuditor (Sicherheit)
        fuer einen strukturierten Bericht.

        Args:
            code: Python-Code als String (optional wenn file_path gegeben).
            file_path: Pfad zu einer Python-Datei (optional wenn code gegeben).

        Returns:
            Strukturierter Analyse-Bericht als Text.
        """
        if not code and not file_path:
            return t("code.no_input")

        # Code aus Datei laden wenn noetig
        source = code
        source_name = "<inline>"
        if file_path and not code:
            try:
                path = Path(file_path).expanduser().resolve()
                # Path-Traversal-Schutz: muss innerhalb Workspace liegen
                workspace_root = self._workspace.expanduser().resolve()
                try:
                    path.relative_to(workspace_root)
                except ValueError:
                    return t("code.file_access_denied", file_path=file_path, root=workspace_root)
                if not path.exists():
                    return t("code.file_not_found", file_path=file_path)
                if path.suffix != ".py":
                    return t("code.only_python")
                source = path.read_text(encoding="utf-8")
                source_name = str(path)
            except (OSError, UnicodeDecodeError) as e:
                return t("code.file_read_error", exc=e)

        # 1. Code-Smell-Analyse
        from cognithor.tools.code_analyzer import CodeSmellDetector

        smell_detector = CodeSmellDetector()
        smells = []

        # Fuer Datei-Analyse nutze analyze_file, sonst parse den Code direkt
        if file_path and not code:
            smells = smell_detector.analyze_file(file_path)
        else:
            # Inline-Code: Manuell parsen
            import ast

            try:
                ast.parse(source)
            except SyntaxError as e:
                _smells_text = f"Syntaxfehler in Zeile {e.lineno}: {e.msg}"
            else:
                # analyze_file braucht eine echte Datei -- temp-Datei erstellen
                tmp = self._workspace / f"_jarvis_analyze_{uuid.uuid4().hex[:8]}.py"
                try:
                    tmp.write_text(source, encoding="utf-8")
                    smells = smell_detector.analyze_file(str(tmp))
                finally:
                    try:
                        if tmp.exists():
                            tmp.unlink()
                    except OSError:
                        pass  # Best-effort temp file cleanup, non-critical

        # 2. Security-Analyse
        from cognithor.security.code_audit import CodeAuditor

        auditor = CodeAuditor()
        security_report = auditor.audit_skill(
            skill_name=source_name,
            code=source,
            file_path=source_name,
        )

        # 3. Bericht zusammenstellen
        lines = len(source.split("\n"))
        parts: list[str] = [
            f"## Code-Analyse: {source_name}",
            f"Zeilen: {lines}",
            "",
        ]

        # Smells
        if smells:
            parts.append(f"### Code-Smells ({len(smells)} gefunden)")
            for smell in smells:
                parts.append(
                    f"- [{smell.severity.upper()}] Zeile {smell.line}: "
                    f"{smell.smell_type} -- {smell.message}"
                )
                if smell.suggestion:
                    parts.append(f"  Vorschlag: {smell.suggestion}")
        else:
            parts.append("### Code-Smells: Keine gefunden")

        parts.append("")

        # Security
        findings = security_report.findings
        if findings:
            parts.append(f"### Sicherheit ({len(findings)} Findings)")
            for f in findings:
                parts.append(
                    f"- [{f.pattern.severity.value.upper()}] Zeile {f.line_number}: "
                    f"{f.pattern.name} -- {f.code_snippet}"
                )
                if f.pattern.recommendation:
                    parts.append(f"  Empfehlung: {f.pattern.recommendation}")
        else:
            parts.append("### Sicherheit: Keine Findings")

        parts.append("")

        # Gesamtbewertung
        parts.append(f"### Gesamt-Risiko: {security_report.overall_risk.upper()}")
        parts.append(f"Audit bestanden: {'Ja' if security_report.passed else 'Nein'}")

        if security_report.recommendations:
            parts.append("")
            parts.append("### Empfehlungen")
            for rec in security_report.recommendations:
                parts.append(f"- {rec}")

        return "\n".join(parts)


def register_code_tools(
    mcp_client: Any,
    config: CognithorConfig,
) -> CodeTools:
    """Registriert Code-Tools beim MCP-Client.

    Returns:
        CodeTools-Instanz.
    """
    tools = CodeTools(config)

    mcp_client.register_builtin_handler(
        "run_python",
        tools.run_python,
        description=(
            "Führt Python-Code in einer Sandbox aus. "
            "Der Code wird als temporäre Datei geschrieben und via Python-Interpreter ausgeführt. "
            "Arbeitsverzeichnis: ~/.cognithor/workspace/. "
            "Für autonomes Coding: Schreibe, teste und iteriere Code."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python-Code der ausgeführt werden soll",
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in Sekunden (Default: {tools._default_timeout})",
                    "default": tools._default_timeout,
                },
                "working_dir": {
                    "type": "string",
                    "description": "Arbeitsverzeichnis (Default: ~/.cognithor/workspace/)",
                    "default": None,
                },
            },
            "required": ["code"],
        },
    )

    mcp_client.register_builtin_handler(
        "analyze_code",
        tools.analyze_code,
        description=(
            "Analysiert Python-Code auf Code-Smells und Sicherheitsprobleme. "
            "Kombiniert AST-basierte Qualitätsanalyse mit Security-Pattern-Scanning. "
            "Read-only, kein Risiko. Akzeptiert Code als String oder Dateipfad."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python-Code als String (optional wenn file_path gegeben)",
                    "default": "",
                },
                "file_path": {
                    "type": "string",
                    "description": "Pfad zu einer Python-Datei (optional wenn code gegeben)",
                    "default": "",
                },
            },
        },
    )

    log.info(
        "code_tools_registered",
        tools=["run_python", "analyze_code"],
        sandbox_level=tools._sandbox.level.value,
    )
    return tools
