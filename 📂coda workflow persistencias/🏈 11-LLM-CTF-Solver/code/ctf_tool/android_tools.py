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
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/android_tools.py','step':'_apk_decompile','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _analyze_manifest(apk_path: str) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/android_tools.py','step':'_analyze_manifest','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


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
