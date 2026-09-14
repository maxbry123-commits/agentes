"""Android 逆向工具集 — APK 反编译、清单分析、证书检查。"""

import logging
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict, List

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


def _find_tool(name: str) -> bool:
    """检查系统是否安装了指定命令行工具。"""
    return shutil.which(name) is not None


def _apk_decompile(apk_path: str, output_dir: str = "apk_output") -> str:
    """反编译 APK 文件。"""
    if not os.path.exists(apk_path):
        return f"错误: APK 文件不存在: {apk_path}"

    lines = [f"APK 反编译: {apk_path}", ""]

    # jadx
    if _find_tool("jadx"):
        try:
            os.makedirs(output_dir, exist_ok=True)
            jadx_out = os.path.join(output_dir, "jadx_output")
            result = subprocess.run(
                ["jadx", "-d", jadx_out, apk_path],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                lines.append(f"jadx 反编译成功: {jadx_out}/")
            else:
                lines.append(f"jadx 反编译失败: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            lines.append("jadx 反编译超时 (300s)")
        except Exception as e:
            lines.append(f"jadx 执行错误: {e}")
    else:
        lines.append("提示: 未安装 jadx (brew install jadx / apt install jadx)")

    # apktool
    if _find_tool("apktool"):
        try:
            os.makedirs(output_dir, exist_ok=True)
            apktool_out = os.path.join(output_dir, "apktool_output")
            result = subprocess.run(
                ["apktool", "d", apk_path, "-o", apktool_out, "-f"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                lines.append(f"apktool 反编译成功: {apktool_out}/")
                # 检查 smali
                smali_dir = os.path.join(apktool_out, "smali")
                if os.path.isdir(smali_dir):
                    smali_count = sum(1 for f in os.listdir(smali_dir) if f.endswith(".smali"))
                    lines.append(f"  smali 文件数: {smali_count}")
            else:
                lines.append(f"apktool 反编译失败: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            lines.append("apktool 反编译超时 (300s)")
        except Exception as e:
            lines.append(f"apktool 执行错误: {e}")
    else:
        lines.append("提示: 未安装 apktool (apt install apktool)")

    if not _find_tool("jadx") and not _find_tool("apktool"):
        return "错误: 未安装 jadx 或 apktool，无法反编译 APK"

    return "\n".join(lines)


def _analyze_manifest(apk_path: str) -> str:
    """提取并分析 AndroidManifest.xml。"""
    if not os.path.exists(apk_path):
        return f"错误: APK 文件不存在: {apk_path}"

    manifest_xml = None
    try:
        with zipfile.ZipFile(apk_path, "r") as z:
            names = z.namelist()
            # 查找 AndroidManifest.xml
            if "AndroidManifest.xml" in names:
                manifest_xml = z.read("AndroidManifest.xml")
    except zipfile.BadZipFile:
        return "错误: 不是有效的 ZIP/APK 文件"
    except Exception as e:
        return f"读取 APK 失败: {e}"

    if not manifest_xml:
        return "错误: APK 中未找到 AndroidManifest.xml"

    lines = ["=== APK 基本信息 ===", f"文件名: {os.path.basename(apk_path)}"]

    # 尝试用 aapt 解析
    if _find_tool("aapt") or _find_tool("aapt2"):
        try:
            aapt_bin = "aapt2" if _find_tool("aapt2") else "aapt"
            result = subprocess.run(
                [aapt_bin, "dump", "badging", apk_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "package:" in line:
                        # 提取包名和版本
                        match = re.search(r"name='([^']+)'.*versionCode='(\d+)'.*versionName='([^']+)'", line)
                        if match:
                            lines.append(f"包名: {match.group(1)}")
                            lines.append(f"版本号: {match.group(2)} (名称: {match.group(3)})")
                    elif "sdkVersion:" in line:
                        lines.append(f"SDK: {line.split(':', 1)[1].strip()}")
                    elif "uses-permission:" in line:
                        perm = line.split(":", 1)[1].strip()
                        lines.append(f"权限: {perm}")
                    elif "application:" in line:
                        lines.append(f"应用: {line.split(':', 1)[1].strip()}")
                    elif "launchable-activity:" in line:
                        match = re.search(r"name='([^']+)'", line)
                        if match:
                            lines.append(f"入口 Activity: {match.group(1)}")
        except Exception:
            pass

    # 纯 Python 解析二进制 manifest（axml）
    if len(lines) <= 2:
        lines.append("(aapt/aapt2 未安装，使用基本分析)")
        # 搜索压缩包中的 manifest 文件
        try:
            with zipfile.ZipFile(apk_path, "r") as z:
                for name in sorted(z.namelist()):
                    lines.append(f"  {name}")
        except Exception:
            pass

    # 检查常见安全配置（二进制 AXML 使用字符串池存储，完整属性语法不连续出现）
    lines.append("\n=== 安全检查 ===")
    manifest_str = manifest_xml.decode("utf-8", errors="replace")
    checks = [
        ("debuggable", "true", "⚠ debuggable=true — APK 可调试"),
        ("allowBackup", "true", "⚠ allowBackup=true — 允许备份"),
        ("usesCleartextTraffic", "true", "⚠ 允许明文 HTTP 流量"),
        ("exported", "true", "提示: 存在导出组件 — 检查可能被外部调用"),
        ("networkSecurityConfig", None, "提示: 使用自定义网络安全配置"),
        ("protectionLevel", "normal", "提示: 低保护级别权限"),
    ]
    for attr, val, desc in checks:
        if attr in manifest_str:
            if val is None or val in manifest_str:
                lines.append(f"  {desc}")

    return "\n".join(lines)


def _extract_resources(apk_path: str, pattern: str = "", output_dir: str = "apk_resources") -> str:
    """从 APK 中提取资源文件。"""
    if not os.path.exists(apk_path):
        return f"错误: APK 文件不存在: {apk_path}"

    os.makedirs(output_dir, exist_ok=True)
    extracted = []
    all_files = []

    try:
        with zipfile.ZipFile(apk_path, "r") as z:
            all_files = z.namelist()

            # 搜索感兴趣的文件
            targets = set()
            interesting_exts = {".dex", ".so", ".p12", ".pem", ".key", ".keystore",
                              ".jks", ".bks", ".json", ".xml", ".properties", ".yaml", ".yml"}
            interesting_dirs = {"assets/", "res/raw/", "lib/", "META-INF/"}

            for fname in all_files:
                low = fname.lower()
                # 按扩展名
                for ext in interesting_exts:
                    if low.endswith(ext):
                        targets.add(fname)
                        break
                # 按目录
                for d in interesting_dirs:
                    if low.startswith(d.lower()):
                        targets.add(fname)
                        break

            # 可选的 pattern 过滤
            if pattern:
                for fname in all_files:
                    if pattern.lower() in fname.lower() or re.search(pattern, fname, re.IGNORECASE):
                        targets.add(fname)

            for fname in targets:
                try:
                    dest = os.path.join(output_dir, fname.replace("/", "_"))
                    with open(dest, "wb") as f:
                        f.write(z.read(fname))
                    extracted.append(f"  {fname} ({os.path.getsize(dest)}B)")
                except Exception:
                    pass

    except Exception as e:
        return f"提取失败: {e}"

    if not extracted:
        return f"未找到匹配的资源（APK 共 {len(all_files)} 个文件）"

    return f"提取了 {len(extracted)} 个文件到 {output_dir}/:\n" + "\n".join(extracted[:50])


# ── 工具类 ──────────────────────────────────────────────────────

class AndroidTools(BaseTool):
    """Android 逆向工具 — APK 反编译、清单分析、资源提取。"""
    modes = {"ctf"}

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "decompile")
        path = arguments.get("path", "")

        if not path:
            return "错误: 需要 path 参数 (APK 文件路径)"

        if not os.path.exists(path):
            return f"错误: 文件不存在: {path}"

        if action == "decompile":
            output = arguments.get("output_dir", "apk_output")
            return _apk_decompile(path, output)

        elif action == "manifest":
            return _analyze_manifest(path)

        elif action == "extract":
            pattern = arguments.get("pattern", "")
            output = arguments.get("output_dir", "apk_resources")
            return _extract_resources(path, pattern, output)

        else:
            return f"未知 action: {action}\n可用: decompile, manifest, extract"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "android_tools",
                "description": (
                    "Android APK 逆向分析工具。支持: "
                    "1) decompile — 反编译 APK (使用 jadx/apktool); "
                    "2) manifest — 提取并分析 AndroidManifest.xml (权限/入口Activity/安全配置); "
                    "3) extract — 从 APK 中提取资源文件 (dex/so/证书/配置文件)。"
                    "需要安装: jadx, apktool, aapt (可选, 缺失时会提示)。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["decompile", "manifest", "extract"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "APK 文件路径",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "decompile/extract 的输出目录",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "extract 操作的文件名过滤 (支持正则)",
                        },
                    },
                    "required": ["action", "path"],
                },
            },
        }
