"""PowerShell 渗透工具集 — Windows 系统侦查、提权、持久化、横向移动。"""

import base64
import logging
from typing import Dict

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

# PowerShell 命令模板库
_PS_COMMANDS = {
    # ── 侦查 ──
    "system_info": (
        "systeminfo | Select-Object -Property 'OS Name','OS Version','System Type','Total Physical Memory'"
    ),
    "users": (
        "Get-LocalUser | Select-Object Name,Enabled,LastLogon | Format-Table -AutoSize"
    ),
    "groups": (
        "Get-LocalGroup | Select-Object Name; Get-LocalGroupMember -Group 'Administrators' | Select-Object Name,ObjectClass"
    ),
    "processes": (
        "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 20 Name,Id,CPU,Path | Format-Table -AutoSize"
    ),
    "services": (
        "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name,DisplayName,StartType | Format-Table -AutoSize"
    ),
    "network": (
        "Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess | "
        "ForEach-Object { $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
        "[PSCustomObject]@{Address=$_.LocalAddress; Port=$_.LocalPort; Process=$proc.ProcessName} } | "
        "Format-Table -AutoSize"
    ),
    "scheduled_tasks": (
        "Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} | Select-Object TaskName,State,TaskPath | Format-Table -AutoSize"
    ),
    "installed_software": (
        "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | "
        "Select-Object DisplayName,DisplayVersion,Publisher,InstallDate | Where-Object {$_.DisplayName} | Format-Table -AutoSize"
    ),
    "environment": (
        "Get-ChildItem Env: | Select-Object Key,Value | Format-Table -AutoSize"
    ),

    # ── 凭据 ──
    "credential_vault": (
        "cmdkey /list"
    ),
    "saved_rdp": (
        "Get-ChildItem 'HKCU:\\Software\\Microsoft\\Terminal Server Client\\Servers' -ErrorAction SilentlyContinue"
    ),
    "stored_credentials": (
        "Get-ChildItem 'C:\\Users\\*\\AppData\\Local\\Microsoft\\Credentials\\*' -ErrorAction SilentlyContinue | Select-Object Name,Length"
    ),

    # ── 文件发现 ──
    "find_passwords": (
        "Get-ChildItem -Path C:\\ -Include *.txt,*.ini,*.cfg,*.conf,*.config,*.xml -File -Recurse "
        "-ErrorAction SilentlyContinue | Select-String -Pattern '(password|passwd|pwd|secret|key|token)' "
        "-SimpleMatch | Select-Object -First 30 Path,Line"
    ),
    "find_sensitive_files": (
        "Get-ChildItem -Path C:\\Users\\ -Include *.pem,*.ppk,*.key,*.pfx,*.p12,*.kdbx,*.rdp -File "
        "-Recurse -ErrorAction SilentlyContinue | Select-Object FullName,Length"
    ),

    # ── 持久化 ──
    "persistence_registry": (
        "Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run' | Format-List; "
        "Get-ItemProperty 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run' | Format-List"
    ),
    "persistence_wmi": (
        "Get-WmiObject __EventFilter -Namespace root\\subscription | Select-Object Name,Query | Format-List; "
        "Get-WmiObject CommandLineEventConsumer -Namespace root\\subscription | Select-Object Name,CommandLineTemplate | Format-List"
    ),

    # ── 防御检查 ──
    "av_check": (
        "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object displayName,productState"
    ),
    "firewall_check": (
        "Get-NetFirewallProfile | Select-Object Name,Enabled | Format-Table -AutoSize"
    ),
    "defender_settings": (
        "Get-MpPreference | Select-Object DisableRealtimeMonitoring,ExclusionPath,ExclusionExtension | Format-List"
    ),

    # ── 域环境 ──
    "domain_info": (
        "[System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain() | Select-Object Name,Forest,DomainControllers"
    ),
    "domain_users": (
        "Get-ADUser -Filter * -Properties * | Select-Object Name,SamAccountName,Enabled,LastLogonDate | Format-Table -AutoSize"
    ),
    "domain_groups": (
        "Get-ADGroup -Filter * | Select-Object Name,GroupScope,GroupCategory | Format-Table -AutoSize"
    ),
    "domain_trusts": (
        "nltest /domain_trusts"
    ),
}


def _encode_ps_command(cmd: str) -> str:
    """将 PowerShell 命令编码为 Base64（用于 -EncodedCommand 参数）。"""
    enc_bytes = cmd.encode("utf-16-le")
    return base64.b64encode(enc_bytes).decode()


def _get_command(name: str) -> str:
    """获取 PowerShell 命令模板。"""
    if name in _PS_COMMANDS:
        return _PS_COMMANDS[name]
    return ""


def _list_commands() -> str:
    """列出所有可用命令及分类。"""
    categories = {
        "侦查": ["system_info", "users", "groups", "processes", "services",
                  "network", "scheduled_tasks", "installed_software", "environment"],
        "凭据": ["credential_vault", "saved_rdp", "stored_credentials"],
        "文件发现": ["find_passwords", "find_sensitive_files"],
        "持久化": ["persistence_registry", "persistence_wmi"],
        "防御检查": ["av_check", "firewall_check", "defender_settings"],
        "域环境": ["domain_info", "domain_users", "domain_groups", "domain_trusts"],
    }

    lines = ["可用 PowerShell 命令模板:"]
    for cat, cmds in categories.items():
        lines.append(f"\n  [{cat}]")
        for cmd in cmds:
            desc = _PS_COMMANDS[cmd][:90]
            lines.append(f"    {cmd:24s} — {desc}...")
    return "\n".join(lines)


def _build_script(commands: list, method: str = "base64") -> str:
    """构建 PowerShell 执行脚本。"""
    cmd_str = "; ".join(_PS_COMMANDS.get(c, c) for c in commands)

    if method == "base64":
        encoded = _encode_ps_command(cmd_str)
        return (
            f"# 直接执行:\n"
            f"powershell -EncodedCommand {encoded}\n\n"
            f"# 或分步执行:\n"
            f"powershell -Command \"{cmd_str[:200]}...\"\n\n"
            f"# 完整命令:\n{cmd_str}"
        )
    else:
        return cmd_str


# ── 工具类 ──────────────────────────────────────────────────────

class PowerShellTools(BaseTool):
    """PowerShell 渗透工具 — Windows 系统侦查、凭据发现、防御检测。"""
    modes = {"pentest"}

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "list")

        if action == "list":
            return _list_commands()

        elif action == "get_command":
            name = arguments.get("name", "")
            cmd = _get_command(name)
            if not cmd:
                available = ", ".join(_PS_COMMANDS.keys())
                return f"未知命令: {name}\n可用命令: {available}"
            return f"[{name}]:\n{cmd}"

        elif action == "build_script":
            commands = arguments.get("commands", [])
            if isinstance(commands, str):
                commands = [c.strip() for c in commands.split(",") if c.strip()]
            if not commands:
                return "错误: 需要 commands 参数 (命令名列表)"
            method = arguments.get("method", "base64")
            return _build_script(commands, method)

        elif action == "encode":
            cmd = arguments.get("command", "")
            if not cmd:
                return "错误: 需要 command 参数"
            encoded = _encode_ps_command(cmd)
            return f"Base64 编码:\n{encoded}\n\n执行:\npowershell -EncodedCommand {encoded}"

        else:
            return (
                f"未知 action: {action}\n"
                "可用: list, get_command, build_script, encode"
            )

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "powershell_tools",
                "description": (
                    "PowerShell Windows 渗透工具。提供预定义命令模板，覆盖: "
                    "1) list — 列出所有可用命令模板; "
                    "2) get_command — 获取指定命令的完整 PowerShell 代码; "
                    "3) build_script — 组合多个命令生成完整脚本 (Base64/明文); "
                    "4) encode — 将命令编码为 Base64 格式。"
                    "类别: 系统侦查/凭据发现/文件发现/持久化检测/防御检查/域环境枚举。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "get_command", "build_script", "encode"],
                            "description": "操作类型",
                        },
                        "name": {
                            "type": "string",
                            "description": "get_command 的命令名称",
                        },
                        "commands": {
                            "type": "string",
                            "description": "build_script 的命令名列表 (逗号分隔, 如 'system_info,users,network')",
                        },
                        "command": {
                            "type": "string",
                            "description": "encode 的要编码的 PowerShell 命令",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["base64", "plain"],
                            "description": "build_script 编码方式 (默认 base64)",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
