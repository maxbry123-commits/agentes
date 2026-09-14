"""
输入验证工具
"""
import re
import ipaddress
from typing import Optional


def is_valid_ip(ip: str) -> bool:
    """
    验证IP地址

    Args:
        ip: IP地址字符串

    Returns:
        是否有效
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_ipv4(ip: str) -> bool:
    """验证IPv4地址"""
    try:
        return ipaddress.ip_address(ip).version == 4
    except ValueError:
        return False


def is_valid_ipv6(ip: str) -> bool:
    """验证IPv6地址"""
    try:
        return ipaddress.ip_address(ip).version == 6
    except ValueError:
        return False


def is_valid_cidr(cidr: str) -> bool:
    """
    验证CIDR格式

    Args:
        cidr: CIDR字符串 (如 192.168.1.0/24)

    Returns:
        是否有效
    """
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def is_valid_domain(domain: str) -> bool:
    """
    验证域名

    Args:
        domain: 域名字符串

    Returns:
        是否有效
    """
    # RFC 1035 域名规则
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.){1,}[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def is_valid_url(url: str) -> bool:
    """
    验证URL

    Args:
        url: URL字符串

    Returns:
        是否有效
    """
    pattern = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(pattern.match(url))


def is_valid_port(port: int) -> bool:
    """
    验证端口号

    Args:
        port: 端口号

    Returns:
        是否有效
    """
    return isinstance(port, int) and 0 <= port <= 65535


def is_valid_service_port(port: int) -> bool:
    """验证服务端口（1-65535）"""
    return isinstance(port, int) and 1 <= port <= 65535


def is_valid_username(username: str) -> bool:
    """
    验证用户名

    Args:
        username: 用户名字符串

    Returns:
        是否有效
    """
    if not username or len(username) > 64:
        return False

    # 允许字母、数字、下划线、短横线
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))


def is_valid_cve(cve: str) -> bool:
    """
    验证CVE编号

    Args:
        cve: CVE编号字符串

    Returns:
        是否有效
    """
    pattern = r'^CVE-\d{4}-\d{4,}$'
    return bool(re.match(pattern, cve.upper()))


def sanitize_filename(filename: str) -> str:
    """
    清理文件名

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除危险字符
    dangerous = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    result = filename

    for char in dangerous:
        result = result.replace(char, '_')

    # 限制长度
    if len(result) > 255:
        result = result[:255]

    return result


def validate_target_list(targets: str) -> dict:
    """
    验证目标列表

    Args:
        targets: 目标字符串（逗号分隔）

    Returns:
        验证结果 {"valid": [...], "invalid": [...]}
    """
    result = {"valid": [], "invalid": []}

    for target in targets.split(','):
        target = target.strip()

        if not target:
            continue

        # 检查各种格式
        if is_valid_ip(target) or is_valid_cidr(target) or is_valid_domain(target) or is_valid_url(target):
            result["valid"].append(target)
        else:
            result["invalid"].append(target)

    return result


def check_private_ip(ip: str) -> bool:
    """
    检查是否为私有IP

    Args:
        ip: IP地址

    Returns:
        是否为私有IP
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


def check_loopback_ip(ip: str) -> bool:
    """检查是否为回环地址"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_loopback
    except ValueError:
        return False


def get_ip_version(ip: str) -> Optional[int]:
    """
    获取IP版本

    Args:
        ip: IP地址

    Returns:
        4 或 6，无效返回None
    """
    try:
        return ipaddress.ip_address(ip).version
    except ValueError:
        return None
