"""
辅助工具函数
"""
import os
import re
import ipaddress
import yaml
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path


def validate_target(target: str) -> Dict:
    """
    验证目标格式

    Args:
        target: 目标字符串（IP、域名、URL等）

    Returns:
        验证结果 {"valid": bool, "type": str, "normalized": str}
    """
    result = {"valid": False, "type": "unknown", "normalized": target}

    # 去除空白
    target = target.strip()

    # 检查URL
    if target.startswith(("http://", "https://")):
        result["valid"] = True
        result["type"] = "url"
        result["normalized"] = target
        return result

    # 检查IP地址
    try:
        ip = ipaddress.ip_address(target)
        result["valid"] = True
        result["type"] = "ipv4" if ip.version == 4 else "ipv6"
        result["normalized"] = str(ip)
        return result
    except ValueError:
        pass

    # 检查CIDR
    try:
        network = ipaddress.ip_network(target, strict=False)
        result["valid"] = True
        result["type"] = "network"
        result["normalized"] = str(network)
        return result
    except ValueError:
        pass

    # 检查域名
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.){1,}[a-zA-Z]{2,}$'
    if re.match(domain_pattern, target):
        result["valid"] = True
        result["type"] = "domain"
        result["normalized"] = target.lower()
        return result

    return result


def parse_ip_range(ip_range: str) -> List[str]:
    """
    解析IP范围

    Args:
        ip_range: IP范围 (如 192.168.1.1-10, 192.168.1.0/24)

    Returns:
        IP地址列表
    """
    ips = []

    # CIDR格式
    if '/' in ip_range:
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            ips = [str(ip) for ip in network.hosts()]
        except ValueError:
            pass

    # 范围格式 (192.168.1.1-10)
    elif '-' in ip_range:
        parts = ip_range.split('-')
        if len(parts) == 2:
            base_parts = parts[0].split('.')
            if len(base_parts) == 4:
                base_ip = '.'.join(base_parts[:3])
                start = int(base_parts[3])
                try:
                    end = int(parts[1])
                    for i in range(start, end + 1):
                        ips.append(f"{base_ip}.{i}")
                except ValueError:
                    pass

    # 单个IP
    else:
        try:
            ipaddress.ip_address(ip_range)
            ips = [ip_range]
        except ValueError:
            pass

    return ips


def format_timestamp(dt: datetime = None, format_str: str = None) -> str:
    """
    格式化时间戳

    Args:
        dt: datetime对象
        format_str: 格式字符串

    Returns:
        格式化后的时间字符串
    """
    if dt is None:
        dt = datetime.now()

    if format_str is None:
        format_str = "%Y-%m-%d %H:%M:%S"

    return dt.strftime(format_str)


def load_config(config_path: str = None) -> Dict:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    if config_path is None:
        # 默认配置路径
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config.yaml"
        )

    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 展开环境变量
    config = _expand_env_vars(config)

    return config or {}


def _expand_env_vars(config: Dict) -> Dict:
    """展开配置中的环境变量"""
    import re

    def expand_value(value):
        if isinstance(value, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, value)
            for var_name in matches:
                env_value = os.getenv(var_name, '')
                value = value.replace(f'${{{var_name}}}', env_value)
            return value
        elif isinstance(value, dict):
            return {k: expand_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand_value(item) for item in value]
        return value

    return expand_value(config)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    format_str: str = None
) -> logging.Logger:
    """
    设置日志

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        format_str: 日志格式

    Returns:
        Logger实例
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 创建根日志器
    logger = logging.getLogger("AI_Pentest")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(format_str)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_dir(path: str) -> str:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def sanitize_input(input_str: str) -> str:
    """
    清理输入字符串，防止命令注入

    Args:
        input_str: 输入字符串

    Returns:
        清理后的字符串
    """
    # 移除危险字符
    dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '<', '>', '\n', '\r']
    result = input_str

    for char in dangerous_chars:
        result = result.replace(char, '')

    return result.strip()


def print_banner():
    """打印程序Banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     ___    ____  ____   ____       _   _   _    ___  ____   ║
    ║    /   |  / __ \/  _/  / __ \     / \ | | | |  / _ \/ ___|  ║
    ║   / /| | / /_/ // /   / /_/ /    / _ \| | | | | | | \___ \  ║
    ║  / ___ |/ _, _// /   / _, _/    / ___ \ |_| | | |_| |___) | ║
    ║ /_/  |_/_/ |_/___/  /_/ |_|    /_/   \_\___/   \___/|____/  ║
    ║                                                              ║
    ║           AI-Powered Automated Penetration Testing           ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_progress(current: int, total: int, description: str = ""):
    """
    打印进度条

    Args:
        current: 当前进度
        total: 总数
        description: 描述
    """
    percent = 100 * (current / float(total)) if total > 0 else 0
    bar_length = 40
    filled_length = int(bar_length * current // total) if total > 0 else 0
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    print(f'\r{description}: |{bar}| {percent:.1f}%', end='\r')

    if current == total:
        print()


def get_os_type() -> str:
    """获取操作系统类型"""
    import platform
    system = platform.system().lower()
    return system


def check_dependencies() -> Dict[str, bool]:
    """
    检查依赖工具是否安装

    Returns:
        工具可用性字典
    """
    import shutil

    tools = ["nmap", "nikto", "hydra", "dirb", "searchsploit"]
    status = {}

    for tool in tools:
        status[tool] = shutil.which(tool) is not None

    return status
