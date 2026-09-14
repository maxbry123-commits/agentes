"""
工具基类和注册表
提供统一的工具接口和注册机制
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os
import subprocess
import shutil
import time
from datetime import datetime


class ToolCategory(Enum):
    """工具类别"""
    NETWORK = "network"
    WEB = "web"
    VULNERABILITY = "vulnerability"
    BRUTE_FORCE = "brute_force"
    POST_EXPLOIT = "post_exploit"
    MISC = "misc"


class ToolStatus(Enum):
    """工具状态"""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    raw_output: str = ""
    execution_time: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "raw_output": self.raw_output,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    category: ToolCategory
    description: str
    executable: str
    version: Optional[str] = None
    install_command: Optional[str] = None
    documentation_url: Optional[str] = None


class BaseTool(ABC):
    """
    工具基类
    所有安全工具继承此类
    """

    # 工具信息（子类必须覆盖）
    TOOL_INFO: ToolInfo = None

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.status = self._check_availability()

    def _check_availability(self) -> ToolStatus:
        """检查工具是否可用"""
        if not self.TOOL_INFO:
            return ToolStatus.ERROR

        executable = self.TOOL_INFO.executable
        if shutil.which(executable):
            return ToolStatus.AVAILABLE
        return ToolStatus.NOT_INSTALLED

    def is_available(self) -> bool:
        """工具是否可用"""
        return self.status == ToolStatus.AVAILABLE

    def get_version(self) -> Optional[str]:
        """获取工具版本"""
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [self.TOOL_INFO.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 提取版本号
                lines = result.stdout.strip().split('\n')
                if lines:
                    return lines[0]
        except Exception:
            pass
        return None

    # Kali工具路径映射
    KALI_TOOL_PATHS = {
        "nmap": "/usr/bin/nmap",
        "masscan": "/usr/bin/masscan",
        "nikto": "/usr/bin/nikto",
        "dirb": "/usr/bin/dirb",
        "whatweb": "/usr/bin/whatweb",
        "sqlmap": "/usr/bin/sqlmap",
        "hydra": "/usr/bin/hydra",
        "medusa": "/usr/bin/medusa",
        "john": "/usr/bin/john",
        "hashcat": "/usr/bin/hashcat",
        "searchsploit": "/usr/bin/searchsploit",
        "msfconsole": "/usr/bin/msfconsole",
        "msfvenom": "/usr/bin/msfvenom",
        "gobuster": "/usr/bin/gobuster",
        "ffuf": "/usr/bin/ffuf",
        "nuclei": "/usr/bin/nuclei",
        "wpscan": "/usr/bin/wpscan",
        "responder": "/usr/bin/responder",
        "crackmapexec": "/usr/bin/crackmapexec",
        "impacket-smbclient": "/usr/bin/impacket-smbclient",
        "secretsdump": "/usr/bin/secretsdump",
        "psexec": "/usr/bin/psexec",
        "netcat": "/usr/bin/nc",
        "netdiscover": "/usr/bin/netdiscover",
        "arp-scan": "/usr/bin/arp-scan",
        "whois": "/usr/bin/whois",
        "dig": "/usr/bin/dig",
        "nslookup": "/usr/bin/nslookup",
        "sublist3r": "/usr/bin/sublist3r",
        "amass": "/usr/bin/amass",
        "xsstrike": "/usr/bin/xsstrike",
        "dalfox": "/usr/bin/dalfox",
        "commix": "/usr/bin/commix",
        "wireshark": "/usr/bin/wireshark",
        "tshark": "/usr/bin/tshark",
        "aircrack-ng": "/usr/bin/aircrack-ng",
        "reaver": "/usr/bin/reaver",
        "cewl": "/usr/bin/cewl",
        "crunch": "/usr/bin/crunch",
    }

    def _get_tool_path(self, tool_name: str) -> str:
        """获取工具的完整路径"""
        # 先检查系统路径
        if shutil.which(tool_name):
            return tool_name
        
        # 再检查Kali路径
        kali_path = self.KALI_TOOL_PATHS.get(tool_name)
        if kali_path and os.path.exists(kali_path):
            return kali_path
        
        # 返回原始名称，让系统决定
        return tool_name

    def _run_command(
        self,
        command: List[str],
        timeout: int = 300,
        capture_output: bool = True,
        use_kali_path: bool = True
    ) -> subprocess.CompletedProcess:
        """
        执行命令

        Args:
            command: 命令列表
            timeout: 超时时间（秒）
            capture_output: 是否捕获输出
            use_kali_path: 是否使用Kali工具路径

        Returns:
            subprocess.CompletedProcess
        """
        start_time = time.time()
        
        # 如果启用Kali路径，替换工具名称
        if use_kali_path and command:
            tool_name = command[0]
            full_path = self._get_tool_path(tool_name)
            command[0] = full_path

        # 设置环境变量
        env = os.environ.copy()
        env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:' + env.get('PATH', '')

        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                env=env,
                cwd="/tmp"  # 在临时目录执行，避免污染工作目录
            )
            return result
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"命令执行超时: {' '.join(command)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到可执行文件: {command[0]}")
        except Exception as e:
            raise Exception(f"命令执行失败: {str(e)}")

    @abstractmethod
    def execute(self, target: str, options: Dict = None) -> ToolResult:
        """
        执行工具

        Args:
            target: 目标（IP、域名、URL等）
            options: 执行选项

        Returns:
            ToolResult
        """
        pass

    @abstractmethod
    def parse_output(self, raw_output: str) -> Any:
        """
        解析工具输出

        Args:
            raw_output: 原始输出

        Returns:
            解析后的结果
        """
        pass

    def get_info(self) -> Dict:
        """获取工具信息"""
        info = {
            "name": self.TOOL_INFO.name if self.TOOL_INFO else "Unknown",
            "category": self.TOOL_INFO.category.value if self.TOOL_INFO else "unknown",
            "description": self.TOOL_INFO.description if self.TOOL_INFO else "",
            "status": self.status.value,
            "version": self.get_version()
        }
        return info


class ToolRegistry:
    """
    工具注册表
    管理所有可用工具
    """

    _tools: Dict[str, type] = {}
    _instances: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool_class: type) -> type:
        """注册工具类"""
        if not issubclass(tool_class, BaseTool):
            raise TypeError("只能注册BaseTool的子类")

        tool_info = tool_class.TOOL_INFO
        if tool_info:
            cls._tools[tool_info.name] = tool_class
        return tool_class

    @classmethod
    def get_tool(cls, name: str, config: Dict = None) -> Optional[BaseTool]:
        """获取工具实例"""
        if name in cls._instances:
            return cls._instances[name]

        if name not in cls._tools:
            return None

        tool_class = cls._tools[name]
        instance = tool_class(config)
        cls._instances[name] = instance
        return instance

    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有已注册工具"""
        return list(cls._tools.keys())

    @classmethod
    def get_available_tools(cls) -> List[Dict]:
        """获取所有可用工具及其状态"""
        available = []
        for name, tool_class in cls._tools.items():
            instance = cls.get_tool(name)
            if instance:
                info = instance.get_info()
                available.append(info)
        return available

    @classmethod
    def get_tools_by_category(cls, category: ToolCategory) -> List[BaseTool]:
        """按类别获取工具"""
        tools = []
        for name, tool_class in cls._tools.items():
            if tool_class.TOOL_INFO and tool_class.TOOL_INFO.category == category:
                instance = cls.get_tool(name)
                if instance:
                    tools.append(instance)
        return tools
