"""本地文件分析工具 — Magic Byte 识别、字符串提取、文件格式解析。"""

import os
import re
import struct
import zipfile
import tarfile
import hashlib
import logging
import concurrent.futures
from math import log2
from typing import Dict, List, Optional, Tuple

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ReDoS 风险检测 — 识别可能引发灾难性回溯的模式（嵌套量词）
_REDOS_RISK_RE = re.compile(
    r"(\((?:[^()]|\([^()]*\))*[+*?][+*?])"  # 嵌套量词，如 (a+)+, (a*)*
    r"|(\([^)]*[+*?][^)]*\)[+*?])"          # 组后紧跟量词且组内有量词
    r"|((?:\|\|)+)"                          # 大量空交替
)
_REGEX_SEARCH_TIMEOUT = 5  # 秒
_REGEX_TEXT_LIMIT = 512 * 1024  # 512KB — 防止过大文本导致正则引擎慢


def _has_redos_risk(pattern: str) -> bool:
    """简单检测正则是否存在灾难性回溯风险。"""
    try:
        return bool(_REDOS_RISK_RE.search(pattern))
    except re.error:
        return True  # 无法分析的pattern按有风险处理

# ── Magic Byte 签名库 ───────────────────────────────────────────

MAGIC_SIGNATURES: List[Tuple[bytes, int, str, str]] = [
    # (magic_bytes, offset, file_extension, description)
    (b"\x89PNG\r\n\x1a\n", 0, ".png", "PNG 图像"),
    (b"\xff\xd8\xff", 0, ".jpg", "JPEG 图像"),
    (b"GIF87a", 0, ".gif", "GIF 图像"),
    (b"GIF89a", 0, ".gif", "GIF 图像"),
    (b"BM", 0, ".bmp", "BMP 图像"),
    (b"RIFF", 0, ".webp", "WebP 图像"),
    (b"%PDF", 0, ".pdf", "PDF 文档"),
    (b"PK\x03\x04", 0, ".zip", "ZIP 压缩包 / Office 文档"),
    (b"PK\x05\x06", 0, ".zip", "ZIP 空压缩包"),
    (b"Rar!\x1a\x07", 0, ".rar", "RAR 压缩包"),
    (b"Rar!\x1a\x07\x01\x00", 0, ".rar", "RAR5 压缩包"),
    (b"\x1f\x8b\x08", 0, ".gz", "GZIP 压缩文件"),
    (b"BZh", 0, ".bz2", "BZIP2 压缩文件"),
    (b"\xfd7zXZ\x00", 0, ".xz", "XZ 压缩文件"),
    (b"7z\xbc\xaf\x27\x1c", 0, ".7z", "7z 压缩包"),
    (b"\xca\xfe\xba\xbe", 0, ".class", "Java Class 文件"),
    (b"\xcf\xfa\xed\xfe", 0, "", "Mach-O 可执行文件 (32位)"),
    (b"\xce\xfa\xed\xfe", 0, "", "Mach-O 可执行文件 (反向 32位)"),
    (b"\xfe\xed\xfa\xcf", 0, "", "Mach-O 可执行文件 (64位)"),
    (b"\xfe\xed\xfa\xce", 0, "", "Mach-O 可执行文件 (反向 64位)"),
    (b"\x7fELF", 0, "", "ELF 可执行文件"),
    (b"MZ", 0, ".exe", "PE 可执行文件 (Windows)"),
    (b"\x4d\x53\x43\x46", 0, ".cab", "CAB 压缩包"),
    (b"\x1a\x45\xdf\xa3", 0, ".mkv", "MKV 视频"),
    (b"\x00\x00\x00\x18ftyp", 0, ".mp4", "MP4 视频"),
    (b"\x00\x00\x00\x20ftyp", 0, ".mp4", "MP4 视频"),
    (b"\x00\x00\x00\x1cftyp", 0, ".mp4", "MP4 视频"),
    (b"ID3", 0, ".mp3", "MP3 音频 (ID3 标签)"),
    (b"\xff\xfb", 0, ".mp3", "MP3 音频"),
    (b"\xff\xf3", 0, ".mp3", "MP3 音频"),
    (b"\xff\xf2", 0, ".mp3", "MP3 音频"),
    (b"OggS", 0, ".ogg", "OGG 音频"),
    (b"\x00\x01\x00\x00\x00", 0, ".ttf", "TTF 字体"),
    (b"OTTO", 0, ".otf", "OTF 字体"),
    (b"d8a5f8c6", 0, ".swf", "SWF 文件"),
    (b"CWS", 0, ".swf", "SWF 文件 (压缩)"),
    (b"FWS", 0, ".swf", "SWF 文件 (未压缩)"),
    (b"\xef\xbb\xbf", 0, "", "UTF-8 BOM 文本"),
    (b"\xff\xfe", 0, "", "UTF-16 LE 文本"),
    (b"\xfe\xff", 0, "", "UTF-16 BE 文本"),
    (b"\x00\x00\xfe\xff", 0, "", "UTF-32 BE 文本"),
    (b"\xff\xfe\x00\x00", 0, "", "UTF-32 LE 文本"),
]

# 最大读取字节数
_MAX_READ = 8192


def _identify_file(path: str) -> Dict:
    """识别文件类型，返回 {'extension', 'description', 'magic_hex', 'size', 'md5'}。"""
    result = {"extension": "", "description": "未知类型", "magic_hex": "", "size": 0, "md5": ""}
    try:
        size = os.path.getsize(path)
        result["size"] = size
        with open(path, "rb") as f:
            head = f.read(min(size, _MAX_READ))
    except OSError as e:
        result["description"] = f"读取失败: {e}"
        return result

    result["md5"] = hashlib.md5(head).hexdigest()
    result["md5_note"] = f"仅计算前 {min(size, _MAX_READ)} 字节的部分哈希" if size > _MAX_READ else ""
    result["magic_hex"] = " ".join(f"{b:02x}" for b in head[:16])

    for magic, offset, ext, desc in MAGIC_SIGNATURES:
        if len(head) >= offset + len(magic):
            if head[offset : offset + len(magic)] == magic:
                result["extension"] = ext
                result["description"] = desc
                break

    return result


def _list_archive(path: str) -> str:
    """列出压缩包内容（ZIP / TAR）。"""
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, "r") as z:
                info = z.infolist()
                lines = [f"ZIP 压缩包 — {len(info)} 个文件:", ""]
                for f in info:
                    flag = "✓" if not f.flag_bits & 0x1 else "🔒"
                    lines.append(f"  {flag}  {f.file_size:>10}B  {f.filename}")
                return "\n".join(lines)
        elif tarfile.is_tarfile(path):
            with tarfile.open(path, "r") as t:
                members = t.getmembers()
                lines = [f"TAR 压缩包 — {len(members)} 个文件:", ""]
                for m in members:
                    lines.append(f"  {m.size:>10}B  {m.name}")
                return "\n".join(lines)
        else:
            return "不是 ZIP 或 TAR 格式的压缩包"
    except Exception as e:
        return f"读取压缩包失败: {e}"


def extract_strings(path: str, min_length: int = 4, encoding: str = "all") -> str:
    """从文件中提取可读字符串。"""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(min(size, 1024 * 1024))  # 最多 1MB
    except OSError as e:
        return f"读取失败: {e}"

    results = {"ascii": [], "utf16": []}
    # ASCII strings
    if encoding in ("all", "ascii"):
        pattern = re.compile(rb"[\x20-\x7e]{" + str(min_length).encode() + rb",}")
        for match in pattern.finditer(data):
            s = match.group().decode("ascii")
            results["ascii"].append(s)
    # UTF-16 strings
    if encoding in ("all", "utf16"):
        pattern = re.compile(
            rb"(?:[\x20-\x7e]\x00){" + str(min_length).encode() + rb",}"
        )
        for match in pattern.finditer(data):
            s = match.group().decode("utf-16-le", errors="replace")
            results["utf16"].append(s)

    output = []
    total = 0
    if results["ascii"]:
        output.append(f"--- ASCII 字符串 (最小长度 {min_length}) ---")
        for s in results["ascii"][:200]:
            output.append(f"  {s}")
            total += 1
    if results["utf16"]:
        output.append(f"--- UTF-16 字符串 (最小长度 {min_length}) ---")
        for s in results["utf16"][:100]:
            output.append(f"  {s}")
            total += 1
    if total == 0:
        return "未找到可读字符串"
    return "\n".join(output) + f"\n--- 共 {total} 条字符串 ---"


def _entropy(data: bytes) -> float:
    """计算字节熵值（越高越可能是加密/压缩数据）。"""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / len(data)
            entropy -= p * log2(p)
    return entropy


def _analyze_binary(path: str, skip_entropy: bool = False) -> str:
    """详细分析二进制文件。"""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            head = f.read(min(size, 4096))
    except OSError as e:
        return f"读取失败: {e}"

    lines = []
    lines.append(f"文件大小: {size:,} 字节 ({size} B)")

    # Magic byte 分析
    info = _identify_file(path)
    lines.append(f"文件类型: {info['description']}")
    if info['magic_hex']:
        lines.append(f"Magic Hex: {info['magic_hex']}")

    # 熵值
    if not skip_entropy and size > 0:
        e = _entropy(head)
        lines.append(f"熵值 (前 4096 字节): {e:.2f}  (0-8, 越高越随机)")
        if e > 7.5:
            lines.append("  提示: 熵值很高, 可能是加密/压缩/已打包数据")
        elif e < 4.0:
            lines.append("  提示: 熵值较低, 可能是文本或结构化数据")

    # PE 头分析
    if head[:2] == b"MZ":
        lines.extend(_parse_pe_header(head))
    elif head[:4] == b"\x7fELF":
        lines.extend(_parse_elf_header(head))

    return "\n".join(lines)


def _parse_pe_header(head: bytes) -> List[str]:
    """解析 PE 文件头基本信息。"""
    lines = ["[PE 可执行文件结构]"]
    try:
        # 从 DOS 头获取 PE 偏移
        pe_offset = struct.unpack_from("<I", head, 0x3C)[0]
        if head[pe_offset:pe_offset+4] == b"PE\x00\x00":
            machine = struct.unpack_from("<H", head, pe_offset + 4)[0]
            archs = {0x14c: "x86 (32位)", 0x8664: "x64 (64位)", 0x1c0: "ARM", 0xaa64: "ARM64"}
            lines.append(f"  架构: {archs.get(machine, f'未知 (0x{machine:04x})')}")
            characteristics = struct.unpack_from("<H", head, pe_offset + 22)[0]
            if characteristics & 0x2000:
                lines.append("  DLL: 是")
            else:
                lines.append("  EXE: 可执行文件")
    except Exception:
        lines.append("  解析失败 (文件可能不完整)")
    return lines


def _parse_elf_header(head: bytes) -> List[str]:
    """解析 ELF 文件头基本信息。"""
    lines = ["[ELF 可执行文件结构]"]
    try:
        elf_class = head[4]
        if elf_class == 1:
            lines.append("  架构: 32 位")
            endian = "小端" if head[5] == 1 else "大端"
            osabi_map = {0: "System V", 3: "Linux", 9: "FreeBSD"}
            lines.append(f"  字节序: {endian}")
            lines.append(f"  ABI: {osabi_map.get(head[7], f'未知 (0x{head[7]:02x})')}")
            e_type = {0: "NONE", 1: "REL (可重定位)", 2: "EXEC (可执行)", 3: "DYN (共享库)", 4: "CORE"}
            lines.append(f"  类型: {e_type.get(struct.unpack_from('<H', head, 16)[0], '未知')}")
        elif elf_class == 2:
            lines.append("  架构: 64 位")
            endian = "小端" if head[5] == 1 else "大端"
            lines.append(f"  字节序: {endian}")
            e_type = {0: "NONE", 1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}
            lines.append(f"  类型: {e_type.get(struct.unpack_from('<H', head, 16)[0], '未知')}")
    except Exception:
        lines.append("  解析失败")
    return lines


def _search_in_file(path: str, pattern: str, encoding: str = "utf-8") -> str:
    """在文件中搜索文本模式（正则）。"""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(min(size, 5 * 1024 * 1024))  # 最多 5MB
    except OSError as e:
        return f"读取失败: {e}"

    try:
        text = data.decode(encoding, errors="replace")
    except LookupError:
        return f"不支持的编码: {encoding}"

    # 校验正则语法
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"正则表达式错误: {e}"

    # 限制正则处理的文本长度，防止过大文本导致引擎变慢
    truncated = False
    if len(text) > _REGEX_TEXT_LIMIT:
        text = text[:_REGEX_TEXT_LIMIT]
        truncated = True

    def _do_match():
        return list(compiled.finditer(text))

    # 若模式存在 ReDoS 风险，使用线程超时保护
    redos_risk = _has_redos_risk(pattern)
    if redos_risk:
        logger.warning("正则模式存在 ReDoS 风险，启用超时保护: %s", pattern)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_do_match)
            try:
                matches = future.result(timeout=_REGEX_SEARCH_TIMEOUT)
            except concurrent.futures.TimeoutExpired:
                return (f"正则匹配超时 ({_REGEX_SEARCH_TIMEOUT}s) — 模式可能存在灾难性回溯 (ReDoS):\n"
                        f"  {pattern}\n"
                        f"建议简化正则或缩小搜索范围。")
    else:
        matches = _do_match()

    if not matches:
        suffix = "（文本已被截断）" if truncated else ""
        return f"未找到匹配 '{pattern}' 的内容{suffix}"

    # 去重并截断上下文
    seen = set()
    results = []
    for m in matches:
        start = max(0, m.start() - 30)
        end = min(len(text), m.end() + 30)
        ctx = text[start:end].replace("\n", "\\n").replace("\r", "")
        if ctx not in seen:
            seen.add(ctx)
            results.append(f"  位置 {m.start()}: ...{ctx}...")
            if len(results) >= 50:
                results.append(f"  ... 以及更多 (共 {len(matches)} 个匹配)")
                break

    suffix = "\n（注: 搜索文本已被截断至 512KB）" if truncated else ""
    return f"找到 {len(matches)} 个匹配 '{pattern}':\n" + "\n".join(results) + suffix


# ── 工具类 ──────────────────────────────────────────────────────

class FileAnalyzer(BaseTool):
    """本地文件分析工具 — 类型识别、字符串提取、二进制分析、压缩包浏览。"""

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "identify")
        path = arguments.get("path", "")

        if not path or not os.path.exists(path):
            # 尝试在 attachments 中查找
            alt = os.path.join("attachments", path)
            if os.path.exists(alt):
                path = alt
            else:
                return f"文件不存在: {path} (当前目录: {os.getcwd()})"

        if action == "identify":
            info = _identify_file(path)
            return (
                f"文件: {path}\n"
                f"大小: {info['size']:,} 字节\n"
                f"类型: {info['description']}\n"
                f"Magic: {info['magic_hex']}\n"
                f"MD5(前缀): {info['md5']}"
            )
        elif action == "strings":
            return extract_strings(
                path, min_length=arguments.get("min_length", 4),
                encoding=arguments.get("encoding", "all"),
            )
        elif action == "analyze":
            return _analyze_binary(
                path, skip_entropy=arguments.get("skip_entropy", False),
            )
        elif action == "archive_list":
            return _list_archive(path)
        elif action == "search":
            return _search_in_file(
                path, pattern=arguments.get("pattern", ""),
                encoding=arguments.get("encoding", "utf-8"),
            )
        else:
            return f"未知 action: {action}"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "file_analyzer",
                "description": (
                    "本地文件分析工具。支持: "
                    "1) identify — Magic Byte 识别文件类型; "
                    "2) strings — 提取文件中可读字符串 (支持 ASCII/UTF-16); "
                    "3) analyze — 二进制文件详细分析 (PE/ELF 头结构 + 熵值); "
                    "4) archive_list — 列出 ZIP/TAR 压缩包内容; "
                    "5) search — 在文件中搜索文本或正则模式。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["identify", "strings", "analyze", "archive_list", "search"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "文件路径 (相对或绝对, 在 attachments/ 下可直接写文件名)",
                        },
                        "min_length": {
                            "type": "integer",
                            "description": "strings 的最小字符串长度 (默认 4)",
                        },
                        "encoding": {
                            "type": "string",
                            "enum": ["all", "ascii", "utf16", "utf-8", "latin-1"],
                            "description": "字符串搜索/提取的编码",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "search 操作的正则表达式",
                        },
                        "skip_entropy": {
                            "type": "boolean",
                            "description": "analyze 时是否跳过熵值计算",
                        },
                    },
                    "required": ["action", "path"],
                },
            },
        }
