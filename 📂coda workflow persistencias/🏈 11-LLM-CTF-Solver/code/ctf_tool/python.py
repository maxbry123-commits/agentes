import subprocess
import sys
import tempfile
import os
import time
import logging
import textwrap
import ast
from typing import Optional, Dict, Set
from ctf_tool.base_tool import BaseTool
from ctf_tool.ssh_client import SSHClient
from config import Config
from utils.security import get_blacklist

logger = logging.getLogger(__name__)

# 在 subprocess 回退模式下禁止导入的危险模块
_DANGEROUS_MODULES: Set[str] = {
    "os", "subprocess", "socket", "shutil", "ctypes", "signal",
    "multiprocessing", "threading", "pty", "fcntl", "posix",
    "sys", "importlib", "builtins", "__builtins__",
}


class PythonTool(BaseTool):
    """在本地或远程执行 Python 代码片段。"""

    _SANDBOX_MODES = ("subprocess", "docker")

    def __init__(self, tool_config: Optional[Dict] = None):
        tool_config = tool_config or {}
        self.remote = self._resolve_remote(tool_config.get("default_mode"))
        if self.remote:
            ssh_config: dict = Config.get_tool_config("ssh_shell")
            self.ssh = SSHClient(
                hostname=ssh_config.get("host", "127.0.0.1"),
                port=ssh_config.get("port", 22),
                username=ssh_config.get("username", ""),
                password=ssh_config.get("password", ""),
            )
        # 沙箱模式：docker(默认) / subprocess
        self.sandbox_mode = self._resolve_sandbox(tool_config.get("sandbox_mode"))

    # ---- 模式解析 -----------------------------------------------------

    @staticmethod
    def _resolve_remote(default_mode: Optional[str] = None) -> bool:
        """决定本地/远程执行模式。"""
        env_mode = os.getenv("AGENT_PYTHON_MODE")
        if env_mode in ("local", "remote"):
            return env_mode == "remote"
        if default_mode in ("local", "remote"):
            return default_mode == "remote"
        # 无显式配置时：SSH 已配置 → 默认远程（保持与 execute_shell_command 文件系统一致）
        ssh_configured = PythonTool._ssh_configured()
        if os.getenv("AGENT_NON_INTERACTIVE") == "1":
            return ssh_configured
        # 交互模式：询问用户，默认推荐项根据 SSH 配置决定
        print("\n--- Python 执行选项 ---")
        print("1. 本地执行")
        if ssh_configured:
            print("2. 远程执行 (推荐 — 与 shell 命令同一文件系统)")
        else:
            print("2. 远程执行")
        try:
            return input("请选择 (1/2): ").strip() == "2"
        except EOFError:
            result = ssh_configured
            logger.warning("非交互模式，默认使用%s执行", "远程" if result else "本地")
            return result

    @staticmethod
    def _ssh_configured() -> bool:
        """检测 SSH 是否已配置 — host + username 均非空即视为可用。"""
        try:
            cfg = Config.get_tool_config("ssh_shell")
            return bool(cfg.get("host") and cfg.get("username"))
        except Exception:
            return False

    @staticmethod
    def _resolve_sandbox(mode: Optional[str] = None) -> str:
        """决定本地沙箱模式（仅本地执行有效）。

        优先级: 配置项 > 环境变量 AGENT_PYTHON_SANDBOX > 默认 docker。
        """
        effective = mode or os.getenv("AGENT_PYTHON_SANDBOX", "docker")
        if effective not in PythonTool._SANDBOX_MODES:
            logger.warning("未知的 sandbox_mode '%s', 回退到 docker", effective)
            return "docker"
        if effective == "docker" and not PythonTool._docker_available():
            logger.warning("Docker 不可用, 回退到 subprocess 沙箱（受限模式）")
            return "subprocess"
        return effective

    @staticmethod
    def _docker_available() -> bool:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/python.py','step':'_docker_available','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    @staticmethod
    def _fix_indentation(code: str) -> str:
        """自动修复 LLM 生成的 Python 代码缩进问题。"""
        code = textwrap.dedent(code)
        try:
            ast.parse(code)
            return code
        except IndentationError:
            pass
        lines = code.split("\n")
        fixed = []
        indent = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed.append("")
                continue
            if any(stripped.startswith(kw) for kw in ("elif ", "else:", "except", "finally:", "except ", "elif")):
                indent = max(0, indent - 1)
            fixed.append("    " * indent + stripped)
            if stripped.endswith(":") and not stripped.startswith("#"):
                indent += 1
        return "\n".join(fixed)

    @staticmethod
    def _audit_ast(code: str) -> Optional[str]:
        """AST 安全审计 — 检测危险模块导入和函数调用。

        Returns:
            错误消息字符串（不安全时），或 None（安全时）。
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"代码语法错误，拒绝执行: {e}"

        for node in ast.walk(tree):
            # 检测危险 import (import os / from os import ...)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split(".")[0]
                    if base in _DANGEROUS_MODULES:
                        return f"禁止导入危险模块: {base}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base = node.module.split(".")[0]
                    if base in _DANGEROUS_MODULES:
                        return f"禁止从危险模块导入: {base}"

            # ── 检测危险函数调用 (exec / eval / compile / getattr) ──
            elif isinstance(node, ast.Call):
                # exec("import os") / eval("...") / compile("...", "", "exec")
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("exec", "eval", "compile"):
                        return f"禁止调用 {node.func.id}() — 沙箱逃逸入口"
                # getattr(__builtins__, "__import__")("os")
                if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                    if len(node.args) >= 2:
                        arg1 = node.args[1]
                        if isinstance(arg1, ast.Constant) and isinstance(arg1.value, str):
                            if arg1.value in ("__import__", "__builtins__", "__subclasses__"):
                                return "禁止 getattr 访问 __import__/__builtins__/__subclasses__"
                # open("...", "w") / open("...", "a") — 阻止写文件
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    if len(node.args) >= 2:
                        arg_mode = node.args[1]
                        if isinstance(arg_mode, ast.Constant) and isinstance(arg_mode.value, str):
                            if "w" in arg_mode.value or "a" in arg_mode.value:
                                return "禁止以写/追加模式打开文件 (open w/a)"

        return None

    def execute(self, tool_name: str, arguments: dict) -> str:
        content = arguments.get("content", "")
        content = self._fix_indentation(content)
        get_blacklist().check_or_raise(content)
        if self.remote:
            return self._execute_remotely(content)
        if self.sandbox_mode == "docker":
            logger.info("使用 Docker 沙箱执行 Python 代码")
            return self._execute_in_docker(content)
        # subprocess 回退模式：先审计再执行
        audit_err = self._audit_ast(content)
        if audit_err:
            return f"安全审计拦截: {audit_err}"
        logger.warning("Docker 不可用，以受限 subprocess 模式执行 Python 代码")
        return self._execute_locally(content)

    # ---- 本地执行 (subprocess) -----------------------------------------

    def _execute_locally(self, content: str) -> str:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/python.py','step':'_execute_locally','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    # ---- 本地执行 (Docker 沙箱) ---------------------------------------

    def _execute_in_docker(self, content: str) -> str:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/python.py','step':'_execute_in_docker','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    # ---- 远程执行 -----------------------------------------------------

    def _execute_remotely(self, content: str) -> str:
        temp_name = f"py_script_{int(time.time())}.py"
        try:
            self.ssh.write_file(temp_name, content)
            output = self.ssh.exec(f"python3 {temp_name}")
            return output
        finally:
            try:
                self.ssh.exec(f"rm -f {temp_name}")
            except Exception:
                pass

    # ---- 工具元数据 ---------------------------------------------------

    @property
    def function_config(self) -> Dict:
        if self.remote:
            tool_desc = (
                "在远程 Kali 执行 Python 代码片段（SSH 连接）。"
                "文件系统与 execute_shell_command 一致，可直接读写 /home/kali/、/tmp/ 等路径。"
                "编码处理: 对不确定编码的bytes, 先用 repr() 查看再决定编码;"
                " 尝试 .decode('utf-8') 失败时, 回退 latin-1 或指定 errors='replace';"
                " 二进制数据直接用 hex() 或 repr(), 不要强转字符串"
            )
            param_desc = "要执行的 Python 代码。运行在远程 Kali，可访问远程文件系统"
        else:
            tool_desc = (
                "在本地主机执行 Python 代码片段（subprocess/Docker）。"
                "无法访问远程文件如 /tmp/、/root/、/home/kali/ 等路径，"
                "需要在远程操作文件请用 execute_shell_command。"
                "编码处理: 对不确定编码的bytes, 先用 repr() 查看再决定编码;"
                " 尝试 .decode('utf-8') 失败时, 回退 latin-1 或指定 errors='replace';"
                " 二进制数据直接用 hex() 或 repr(), 不要强转字符串"
            )
            param_desc = "要执行的 Python 代码。运行在本地，不能访问远程服务器的文件系统"
        return {
            "type": "function",
            "function": {
                "name": "execute_python_code",
                "description": tool_desc,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": param_desc,
                        }
                    },
                    "required": ["content"],
                },
            },
        }
