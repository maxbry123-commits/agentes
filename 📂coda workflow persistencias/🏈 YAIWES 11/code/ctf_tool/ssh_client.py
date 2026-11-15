"""共享 SSH 客户端 — 封装连接/重连/文件上传，支持 WarningPolicy 主机密钥验证。"""

import os
import time
import logging
import paramiko
from typing import Optional
from utils.security import get_blacklist

logger = logging.getLogger(__name__)

# SSH 连接失败后冷却时间（秒），避免每次工具执行都阻塞 6s 等待超时
_RECONNECT_COOLDOWN = 30


class SSHClient:
    """轻量 SSH 客户端封装，供 ssh_shell / python 工具共用。"""

    def __init__(self, hostname: str, port: int = 22,
                 username: str = "", password: str = ""):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self._client: Optional[paramiko.SSHClient] = None
        self._last_connect_attempt: float = 0
        self._connect_failures: int = 0

    # ---- 连接管理 -----------------------------------------------------

    def connect(self):
        """建立连接。连续失败 3 次后进入冷却期，避免反复阻塞。"""
        now = time.time()
        if self._connect_failures >= 3:
            if now - self._last_connect_attempt < _RECONNECT_COOLDOWN:
                raise ConnectionError(
                    f"SSH {self.hostname}:{self.port} 连接连续失败 {self._connect_failures} 次，"
                    f"进入冷却期 ({int(_RECONNECT_COOLDOWN - (now - self._last_connect_attempt))}s 后重试)"
                )
            # 冷却期过后重置计数
            self._connect_failures = 0

        self._last_connect_attempt = now
        self.close()
        client = paramiko.SSHClient()

        # 抑制 paramiko transport 后台线程的 ERROR 日志（连接失败时 transport.run 会打印堆栈）
        transport_logger = logging.getLogger("paramiko.transport")
        old_level = transport_logger.level
        transport_logger.setLevel(logging.CRITICAL)

        try:
            # 使用 WarningPolicy：检查 known_hosts，未知主机记录警告但允许连接。
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            self._client = client
            client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=6,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=6,
            )
            self._connect_failures = 0
            logger.info(f"SSH 连接成功: {self.username}@{self.hostname}:{self.port}")
        except Exception:
            self._connect_failures += 1
            self.close()
            raise
        finally:
            transport_logger.setLevel(old_level)

    def close(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    @property
    def is_connected(self) -> bool:
        if not self._client:
            return False
        try:
            t = self._client.get_transport()
            return t is not None and t.is_active()
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        """快速检查 SSH 是否可用（不触发实际连接，仅检查冷却期）。"""
        if self._connect_failures >= 3:
            if time.time() - self._last_connect_attempt < _RECONNECT_COOLDOWN:
                return False
        return True

    def ensure_connected(self):
        """确保连接有效，必要时自动重连。"""
        if not self.is_connected:
            logger.info("SSH 会话断开，尝试重新连接 ...")
            self.connect()

    def exec(self, command: str, timeout: int = 30) -> str:
        """执行命令，返回 stdout+stderr 合并输出。timeout 秒后强制返回。"""
        get_blacklist().check_or_raise(command)
        self.ensure_connected()
        _, stdout, stderr = self._client.exec_command(command, timeout=timeout)  # type: ignore[union-attr]
        return self._safe_decode(stdout.read()) + self._safe_decode(stderr.read())

    # ---- SFTP 文件操作 ------------------------------------------------

    def upload_folder(self, local_path: str, remote_path: str):
        """递归上传本地目录到远程路径。"""
        self.ensure_connected()
        sftp: Optional[paramiko.SFTPClient] = None
        try:
            sftp = self._client.open_sftp()  # type: ignore[union-attr]
            self._sftp_mkdir_p(sftp, remote_path)

            for root, _, files in os.walk(local_path):
                rel = os.path.relpath(root, local_path).replace("\\", "/")
                target_dir = remote_path + "/" + rel if rel != "." else remote_path
                self._sftp_mkdir_p(sftp, target_dir)

                for file in files:
                    local_file = os.path.join(root, file)
                    remote_file = target_dir + "/" + file
                    sftp.put(local_file, remote_file)
                    logger.debug(f"上传: {local_file} -> {remote_file}")

            logger.info(f"文件夹上传完成: {local_path} -> {remote_path}")
        except Exception:
            logger.exception("文件夹上传失败")
            raise
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass

    def write_file(self, remote_path: str, content: str):
        """通过 SFTP 写入文件内容到远程（不经过 shell，无注入风险）。"""
        self.ensure_connected()
        sftp: Optional[paramiko.SFTPClient] = None
        try:
            sftp = self._client.open_sftp()  # type: ignore[union-attr]
            with sftp.file(remote_path, "w") as f:
                f.write(content)
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass

    @staticmethod
    def _sftp_mkdir_p(sftp: paramiko.SFTPClient, path: str):
        """递归创建远程目录（类似 mkdir -p）。"""
        import stat as stat_module
        try:
            sftp.stat(path)
        except IOError:
            parts = path.strip("/").split("/")
            acc = ""
            for part in parts:
                acc += "/" + part
                try:
                    sftp.stat(acc)
                except IOError:
                    sftp.mkdir(acc)

    # ---- 辅助方法 ----------------------------------------------------

    @staticmethod
    def _safe_decode(data: bytes) -> str:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")

    def __del__(self):
        self.close()
