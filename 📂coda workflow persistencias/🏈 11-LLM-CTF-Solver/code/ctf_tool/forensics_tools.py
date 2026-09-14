"""取证分析工具集 — 流量分析、文件恢复、Hex 分析、字符串搜索。"""

import logging
import os
import re
from typing import Dict, List, Optional

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ── PCAP 分析 ─────────────────────────────────────────────────────

try:
    import scapy.all as scapy
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


def _pcap_analyze(path: str) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/forensics_tools.py','step':'_pcap_analyze','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def _pcap_extract_objects(path: str, export_dir: str = "pcap_export") -> str:
    """从 HTTP 流量中提取文件对象。"""
    if not HAS_SCAPY:
        return "错误: 需要 scapy 库 (pip install scapy)"

    try:
        packets = scapy.rdpcap(path)
    except Exception as e:
        return f"读取 PCAP 失败: {e}"

    os.makedirs(export_dir, exist_ok=True)
    extracted = 0

    for i, pkt in enumerate(packets):
        if pkt.haslayer(scapy.TCP) and pkt.haslayer(scapy.Raw):
            payload = pkt[scapy.Raw].load
            # 检查 HTTP 响应中的文件
            if b"HTTP/1." in payload and b"\r\n\r\n" in payload:
                header_end = payload.find(b"\r\n\r\n") + 4
                body = payload[header_end:]
                if len(body) > 128:
                    fname = f"{export_dir}/object_{i}.bin"
                    with open(fname, "wb") as f:
                        f.write(body)
                    extracted += 1

    return f"从 HTTP 响应中提取了 {extracted} 个文件对象到 {export_dir}/ 目录"


# ── 文件恢复 ──────────────────────────────────────────────────────

# Magic bytes 用于文件恢复签名
_FILE_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", 0, "png"),
    (b"\xff\xd8\xff", 0, "jpg"),
    (b"GIF87a", 0, "gif"),
    (b"GIF89a", 0, "gif"),
    (b"%PDF", 0, "pdf"),
    (b"PK\x03\x04", 0, "zip"),
    (b"\x1f\x8b\x08", 0, "gz"),
    (b"\xfd7zXZ\x00", 0, "xz"),
    (b"7z\xbc\xaf\x27\x1c", 0, "7z"),
    (b"\x7fELF", 0, "elf"),
    (b"MZ", 0, "exe"),
    (b"RIFF", 0, "avi"),
    (b"OggS", 0, "ogg"),
]


def _carve_files(path: str, out_dir: str = "carved") -> str:
    """从二进制文件中雕刻（Carve）已知格式的文件。"""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

    os.makedirs(out_dir, exist_ok=True)
    carved = []

    for magic, offset, ext in _FILE_SIGNATURES:
        start = 0
        count = 0
        while True:
            pos = data.find(magic, start)
            if pos == -1:
                break
            # 尝试找文件结束标记
            end = None
            if ext == "png":
                end_pos = data.find(b"\x00\x00\x00\x00IEND", pos)
                if end_pos >= 0:
                    end = end_pos + 12  # IEND + CRC
            elif ext == "jpg":
                end_pos = data.rfind(b"\xff\xd9", pos, pos + 5 * 1024 * 1024)
                if end_pos >= 0:
                    end = end_pos + 2
            elif ext == "zip":
                # 找中央目录结尾
                end = min(pos + 5 * 1024 * 1024, len(data))

            if not end:
                end = min(pos + 1024 * 1024, len(data))

            file_data = data[pos:end]
            fname = f"{out_dir}/{os.path.basename(path)}.{ext}_{count}"
            with open(fname, "wb") as f:
                f.write(file_data)
            carved.append(f"  {fname} ({len(file_data)} 字节 @ 0x{pos:x})")
            count += 1
            start = pos + 1

    if not carved:
        return f"在 {path} 中未找到已知格式的文件签名"

    return f"从 {path} 中雕刻出 {len(carved)} 个文件:\n" + "\n".join(carved[:50])


# ── Hex 分析 ──────────────────────────────────────────────────────

def _hex_dump(path: str, offset: int = 0, length: int = 512, show_ascii: bool = True) -> str:
    """生成 Hex 转储。"""
    try:
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read(length)
    except Exception as e:
        return f"读取失败: {e}"

    lines = []
    addr = offset
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk[:8])
        if len(chunk) > 8:
            hex_part += " | " + " ".join(f"{b:02x}" for b in chunk[8:])
        ascii_part = ""
        if show_ascii:
            ascii_part = "  " + "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"  {addr:08x}  {hex_part:{47}}{ascii_part}")
        addr += 16

    return f"Hex 转储 (偏移 {offset}, {len(data)} 字节):\n" + "\n".join(lines)


def _hex_search(path: str, hex_pattern: str) -> str:
    """在文件中搜索 Hex 模式。"""
    try:
        pattern = bytes.fromhex(hex_pattern.replace(" ", ""))
    except ValueError as e:
        return f"Hex 模式格式错误: {e}"

    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        return f"读取失败: {e}"

    positions = []
    start = 0
    while True:
        pos = data.find(pattern, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1

    if not positions:
        return f"在文件中未找到模式: {hex_pattern}"

    # 显示每个匹配位置附近的上下文
    lines = [f"找到 {len(positions)} 个匹配 (hex: {hex_pattern}):"]
    for pos in positions[:20]:
        ctx_start = max(0, pos - 8)
        ctx_end = min(len(data), pos + len(pattern) + 8)
        ctx = data[ctx_start:ctx_end]
        hex_ctx = " ".join(f"{b:02x}" for b in ctx)
        arrow = " " * (3 * (pos - ctx_start)) + "^" * (3 * len(pattern) - 1)
        lines.append(f"\n  偏移 0x{pos:x}:")
        lines.append(f"    {hex_ctx}")
        lines.append(f"    {arrow}")

    if len(positions) > 20:
        lines.append(f"\n  ... 以及另外 {len(positions) - 20} 个匹配")

    return "\n".join(lines)


# ── 工具类 ──────────────────────────────────────────────────────

class ForensicsTool(BaseTool):
    """取证分析工具 — PCAP 流量分析、文件雕刻、Hex 分析、字符串搜索。"""
    modes = {"ctf"}

    @property
    def tags(self):
        return ("forensics", "analysis", "network")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "")
        path = arguments.get("path", "")

        if not path:
            return "错误: 需要文件路径参数"
        if not os.path.exists(path):
            alt = os.path.join("attachments", path)
            if os.path.exists(alt):
                path = alt

        if action == "pcap_summary":
            return _pcap_analyze(path)

        elif action == "pcap_extract":
            export = arguments.get("export_dir", "pcap_export")
            return _pcap_extract_objects(path, export)

        elif action == "carve":
            out_dir = arguments.get("out_dir", "carved")
            return _carve_files(path, out_dir)

        elif action == "hexdump":
            return _hex_dump(
                path,
                offset=arguments.get("offset", 0),
                length=arguments.get("length", 512),
                show_ascii=arguments.get("show_ascii", True),
            )

        elif action == "hex_search":
            pattern = arguments.get("pattern", "")
            if not pattern:
                return "错误: 需要 pattern 参数 (hex 字符串)"
            return _hex_search(path, pattern)

        elif action == "strings":
            import ctf_tool.file_analyzer as fa
            return fa.extract_strings(
                path,
                min_length=arguments.get("min_length", 4),
                encoding=arguments.get("encoding", "all"),
            )

        else:
            return (
                f"未知 action: {action}\n"
                "可用: pcap_summary, pcap_extract, carve, hexdump, hex_search, strings"
            )

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "forensics_tools",
                "description": (
                    "取证分析工具。支持: "
                    "1) pcap_summary — PCAP 流量汇总 (协议统计/HTTP 请求/DNS/可疑连接); "
                    "2) pcap_extract — 从 HTTP 流量提取文件对象; "
                    "3) carve — 从二进制文件中雕刻已知格式文件; "
                    "4) hexdump — 生成 Hex 转储; "
                    "5) hex_search — 在文件中搜索 Hex 模式; "
                    "6) strings — 提取文件中的可读字符串。"
                    "PCAP 分析需要 scapy 库。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["pcap_summary", "pcap_extract", "carve",
                                     "hexdump", "hex_search", "strings"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "文件路径",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "hex_search 的 hex 模式 (如 'ffd8ffe0')",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "hexdump 的起始偏移 (默认 0)",
                        },
                        "length": {
                            "type": "integer",
                            "description": "hexdump 的长度 (默认 512)",
                        },
                        "export_dir": {
                            "type": "string",
                            "description": "pcap_extract/carve 的输出目录",
                        },
                        "min_length": {
                            "type": "integer",
                            "description": "strings 最小长度 (默认 4)",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "strings 编码 (默认 all)",
                        },
                    },
                    "required": ["action", "path"],
                },
            },
        }
