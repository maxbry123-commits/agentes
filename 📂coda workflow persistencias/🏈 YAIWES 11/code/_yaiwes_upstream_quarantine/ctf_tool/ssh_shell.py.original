import os
import logging
from typing import Dict
from config import Config
from ctf_tool.base_tool import BaseTool
from ctf_tool.ssh_client import SSHClient

logger = logging.getLogger(__name__)


class SSHShell(BaseTool):
    """在远程 Linux 服务器上执行 Shell 命令。"""

    _attachments_uploaded = False  # 类级别标记，避免重复上传

    def __init__(self, tool_config: dict = None):
        ssh_config: dict = Config.get_tool_config("ssh_shell")
        self.client = SSHClient(
            hostname=ssh_config.get("host", "127.0.0.1"),
            port=ssh_config.get("port", 22),
            username=ssh_config.get("username", ""),
            password=ssh_config.get("password", ""),
        )
        # 附件上传延迟到首次 execute 时触发（此时才有连接）
        self._attachments_pending = (
            bool(os.listdir("./attachments")) if os.path.isdir("./attachments") else False
        ) and not SSHShell._attachments_uploaded
        # 不在 __init__ 时连接 — 延迟到首次 execute，避免启动时阻塞

    def execute(self, tool_name: str, arguments: dict) -> str:
        command = arguments.get("content", "")
        if not command:
            return "错误：未提供命令内容"

        # 快速失败：如果 SSH 处于冷却期，直接返回错误而不是阻塞 6s
        if not self.client.is_available:
            return (
                f"错误: SSH 服务器 {self.client.hostname}:{self.client.port} 不可用"
                f"（已连续失败 {self.client._connect_failures} 次，请检查服务是否启动）"
            )

        try:
            # 延迟上传附件（首次成功连接后）
            if self._attachments_pending and self.client.is_connected:
                logger.info("检测到附件，正在上传至远程服务器 ...")
                self.client.upload_folder("./attachments", ".")
                SSHShell._attachments_uploaded = True
                self._attachments_pending = False

            return self.client.exec(command)
        except (ConnectionError, OSError) as e:
            return f"SSH 连接失败: {str(e)}"
        except Exception as e:
            logger.exception("命令执行失败")
            return f"命令执行错误: {str(e)}"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "execute_shell_command",
                "description": "在 Linux 服务器上执行 Shell 命令，可用 curl, sqlmap, nmap, openssl 等工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "要执行的 Shell 命令",
                        }
                    },
                    "required": ["content"],
                },
            },
        }
