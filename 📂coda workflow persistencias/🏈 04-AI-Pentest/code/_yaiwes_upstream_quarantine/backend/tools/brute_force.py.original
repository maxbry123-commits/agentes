"""
暴力破解工具
集成Hydra、Medusa等暴力破解工具
"""
from typing import Dict, List, Optional, Any
import re
import subprocess
import shutil
from .base import BaseTool, ToolResult, ToolCategory, ToolInfo, ToolRegistry


@ToolRegistry.register
class BruteForceTool(BaseTool):
    """
    暴力破解工具
    集成Hydra、Medusa等工具
    """

    TOOL_INFO = ToolInfo(
        name="brute_force",
        category=ToolCategory.BRUTE_FORCE,
        description="密码暴力破解工具集",
        executable="hydra"
    )

    # 默认用户名列表
    DEFAULT_USERS = [
        "admin", "administrator", "root", "user", "test", "guest",
        "mysql", "postgres", "ftp", "www", "www-data", "nginx",
        "oracle", "sa", "sysadmin", "operator"
    ]

    # 默认密码列表
    DEFAULT_PASSWORDS = [
        "admin", "password", "123456", "root", "administrator",
        "guest", "test", "12345678", "123456789", "qwerty",
        "abc123", "password123", "admin123", "letmein", "welcome",
        "monkey", "dragon", "master", "login", "pass"
    ]

    # 服务默认端口
    SERVICE_PORTS = {
        "ssh": 22,
        "ftp": 21,
        "telnet": 23,
        "smtp": 25,
        "pop3": 110,
        "imap": 143,
        "mysql": 3306,
        "mssql": 1433,
        "rdp": 3389,
        "postgresql": 5432,
        "vnc": 5900,
        "smb": 445
    }

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.max_tasks = config.get("max_tasks", 16) if config else 16
        self.timeout = config.get("timeout", 300) if config else 300

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """
        执行暴力破解

        Args:
            target: 目标IP/域名
            options: 破解选项
                - service: 服务类型 (ssh, ftp, http, etc.)
                - port: 端口
                - users: 用户名列表
                - passwords: 密码列表
                - user_file: 用户名字典文件
                - pass_file: 密码字典文件
        """
        options = options or {}
        service = options.get("service", "ssh")
        port = options.get("port", self.SERVICE_PORTS.get(service, 22))

        results = {
            "target": target,
            "service": service,
            "port": port,
            "credentials": [],
            "attempts": 0,
            "success": False
        }

        # 使用Hydra进行破解
        hydra_result = self._hydra_attack(target, service, port, options)
        if hydra_result["credentials"]:
            results["credentials"].extend(hydra_result["credentials"])
            results["success"] = True

        results["attempts"] = hydra_result.get("attempts", 0)

        return ToolResult(
            success=results["success"],
            output=results,
            metadata={"service": service}
        )

    def _hydra_attack(
        self,
        target: str,
        service: str,
        port: int,
        options: Dict
    ) -> Dict:
        """使用Hydra进行攻击"""
        result = {"credentials": [], "attempts": 0}

        if not shutil.which("hydra"):
            result["error"] = "Hydra不可用"
            return result

        # 构建命令
        command = ["hydra", "-t", str(self.max_tasks)]

        # 用户名
        if options.get("user_file"):
            command.extend(["-L", options["user_file"]])
        elif options.get("users"):
            command.extend(["-l", ",".join(options["users"])])
        else:
            # 使用默认用户名列表
            command.extend(["-L", self._create_temp_wordlist(
                self.DEFAULT_USERS, "users"
            )])

        # 密码
        if options.get("pass_file"):
            command.extend(["-P", options["pass_file"]])
        elif options.get("passwords"):
            command.extend(["-p", ",".join(options["passwords"])])
        else:
            # 使用默认密码列表
            command.extend(["-P", self._create_temp_wordlist(
                self.DEFAULT_PASSWORDS, "passwords"
            )])

        # 特定服务选项
        if service == "http":
            # HTTP表单破解
            path = options.get("path", "/login")
            command.extend([
                "-m", f"{path}:username=^USER^&password=^PASS^:F=failed"
            ])

        command.extend([
            "-s", str(port),
            "-f",  # 找到有效凭据后停止
            target,
            service
        ])

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # 解析结果
            result = self._parse_hydra_output(proc.stdout)

        except subprocess.TimeoutExpired:
            result["error"] = "攻击超时"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _parse_hydra_output(self, output: str) -> Dict:
        """解析Hydra输出"""
        result = {"credentials": [], "attempts": 0}

        for line in output.split('\n'):
            # 匹配成功行: [22][ssh] host: 192.168.1.1   login: root   password: toor
            match = re.search(
                r'\[(\d+)\]\[(\w+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)',
                line
            )
            if match:
                port, service, host, user, password = match.groups()
                result["credentials"].append({
                    "username": user,
                    "password": password,
                    "service": service,
                    "port": int(port)
                })

            # 统计尝试次数
            if "attempting" in line.lower():
                result["attempts"] += 1

        return result

    def _create_temp_wordlist(self, wordlist: List[str], prefix: str) -> str:
        """创建临时字典文件"""
        import tempfile

        fd, path = tempfile.mkstemp(prefix=f"{prefix}_", suffix=".txt")
        with open(fd, 'w') as f:
            f.write('\n'.join(wordlist))

        return path

    def parse_output(self, raw_output: str) -> Any:
        return {"raw": raw_output}


@ToolRegistry.register
class HydraTool(BaseTool):
    """Hydra暴力破解工具"""

    TOOL_INFO = ToolInfo(
        name="hydra",
        category=ToolCategory.BRUTE_FORCE,
        description="快速网络登录破解器",
        executable="hydra",
        install_command="apt install hydra -y"
    )

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.tasks = config.get("tasks", 16) if config else 16

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """执行Hydra攻击"""
        options = options or {}

        if not self.is_available():
            return ToolResult(success=False, error="Hydra不可用")

        service = options.get("service", "ssh")
        port = options.get("port")
        users = options.get("users", [])
        passwords = options.get("passwords", [])
        user_file = options.get("user_file")
        pass_file = options.get("pass_file")

        # 构建命令
        command = ["hydra"]

        # 并发任务
        command.extend(["-t", str(self.tasks)])

        # 用户名
        if user_file:
            command.extend(["-L", user_file])
        elif users:
            command.extend(["-l", users[0] if len(users) == 1 else ",".join(users)])

        # 密码
        if pass_file:
            command.extend(["-P", pass_file])
        elif passwords:
            command.extend(["-p", passwords[0] if len(passwords) == 1 else ",".join(passwords)])

        # 端口
        if port:
            command.extend(["-s", str(port)])

        # 找到后停止
        command.append("-f")

        # 目标和服务
        command.extend([target, service])

        try:
            result = self._run_command(command, timeout=options.get("timeout", 600))
            parsed = self.parse_output(result.stdout)

            return ToolResult(
                success=len(parsed.get("credentials", [])) > 0,
                output=parsed,
                raw_output=result.stdout
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def parse_output(self, raw_output: str) -> Dict:
        """解析Hydra输出"""
        result = {
            "credentials": [],
            "attempts": 0
        }

        for line in raw_output.split('\n'):
            # 匹配成功的凭据
            match = re.search(
                r'\[(\d+)\]\[(\w+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)',
                line
            )
            if match:
                port, service, host, user, password = match.groups()
                result["credentials"].append({
                    "port": int(port),
                    "service": service,
                    "host": host,
                    "username": user,
                    "password": password
                })

        return result


@ToolRegistry.register
class MedusaTool(BaseTool):
    """Medusa暴力破解工具"""

    TOOL_INFO = ToolInfo(
        name="medusa",
        category=ToolCategory.BRUTE_FORCE,
        description="并行网络登录审计工具",
        executable="medusa",
        install_command="apt install medusa -y"
    )

    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """执行Medusa攻击"""
        options = options or {}

        if not self.is_available():
            return ToolResult(success=False, error="Medusa不可用")

        service = options.get("service", "ssh")
        port = options.get("port")
        user = options.get("user")
        password = options.get("password")
        user_file = options.get("user_file")
        pass_file = options.get("pass_file")

        # 构建命令
        command = [
            "medusa",
            "-h", target,
            "-M", service
        ]

        # 用户名
        if user:
            command.extend(["-u", user])
        elif user_file:
            command.extend(["-U", user_file])

        # 密码
        if password:
            command.extend(["-p", password])
        elif pass_file:
            command.extend(["-P", pass_file])

        # 端口
        if port:
            command.extend(["-n", str(port)])

        # 详细输出
        command.extend(["-v", "6"])

        try:
            result = self._run_command(command, timeout=options.get("timeout", 600))
            parsed = self.parse_output(result.stdout)

            return ToolResult(
                success=len(parsed.get("credentials", [])) > 0,
                output=parsed,
                raw_output=result.stdout
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def parse_output(self, raw_output: str) -> Dict:
        """解析Medusa输出"""
        result = {
            "credentials": [],
            "attempts": 0
        }

        for line in raw_output.split('\n'):
            # 匹配成功
            if "SUCCESS" in line:
                match = re.search(
                    r'host:\s+(\S+).*login:\s+(\S+).*password:\s+(\S+)',
                    line
                )
                if match:
                    host, user, password = match.groups()
                    result["credentials"].append({
                        "host": host,
                        "username": user,
                        "password": password
                    })

        return result
