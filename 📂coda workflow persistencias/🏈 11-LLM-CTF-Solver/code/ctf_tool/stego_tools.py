"""隐写分析工具集 — LSB 提取、图片分析、频谱图、频域分析。"""

import logging
import os
import struct
from typing import Dict, List, Optional
from io import BytesIO

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

# ── LSB 提取 ──────────────────────────────────────────────────────

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _lsb_extract(path: str, channel: str = "rgb", bit_plane: int = 0,
                 msb_first: bool = True) -> str:
    """从图片中提取 LSB 数据。"""
    if not HAS_PIL:
        return "错误: 需要 PIL 库 (pip install Pillow)"

    try:
        img = Image.open(path)
    except Exception as e:
        return f"打开图片失败: {e}"

    pixels = list(img.getdata())
    mode = img.mode

    channel_map = {"r": 0, "g": 1, "b": 2}
    chan_idx = channel_map.get(channel.lower(), None)

    bits = []
    for pixel in pixels:
        if isinstance(pixel, int):
            # 灰度图
            bits.append((pixel >> bit_plane) & 1)
        elif chan_idx is not None and len(pixel) >= chan_idx + 1:
            bits.append((pixel[chan_idx] >> bit_plane) & 1)
        else:
            for c in range(min(3, len(pixel))):
                bits.append((pixel[c] >> bit_plane) & 1)

    # 转换为字节 — msb_first 控制每个字节内的 bit 排列顺序
    bytes_data = []
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8):
            if msb_first:
                byte = (byte << 1) | bits[i + j]
            else:
                byte |= bits[i + j] << j  # LSB first
        bytes_data.append(byte)

    # 尝试检测文本
    text_result = ""
    try:
        raw = bytes(bytes_data)
        text = raw.decode("utf-8", errors="replace")
        # 过滤可读部分
        readable = "".join(c if 32 <= ord(c) <= 126 else "" for c in text)
        if len(readable) > 10:
            text_result += f"\n提取的文本内容:\n{readable[:2000]}"
    except Exception:
        pass

    # 检查 PNG IHDR 等文件头
    raw = bytes(bytes_data)
    magic_checks = [
        (b"\x89PNG", "PNG 图片"),
        (b"\xff\xd8\xff", "JPEG 图片"),
        (b"PK\x03\x04", "ZIP 压缩包"),
        (b"%PDF", "PDF 文档"),
    ]
    extra = ""
    for magic, desc in magic_checks:
        if raw[:len(magic)] == magic:
            extra = f"\n检测到嵌入式文件: {desc} ({len(raw)} 字节)"

    result = [
        f"图片尺寸: {img.size}, 模式: {mode}",
        f"通道: {channel}, 位平面: {bit_plane}",
        f"提取数据量: {len(bytes_data)} 字节",
    ]
    if extra:
        result.append(extra)
    if text_result:
        result.append(text_result)

    # 显示前 200 字节 hex
    hex_preview = " ".join(f"{b:02x}" for b in bytes_data[:64])
    result.append(f"\nHex 预览 (前 64 字节):\n{hex_preview}")

    return "\n".join(result)


def _lsb_extract_all(path: str) -> str:
    """自动尝试多种 LSB 提取组合。"""
    if not HAS_PIL:
        return "错误: 需要 PIL 库 (pip install Pillow)"

    channels = ["r", "g", "b", "rgb"]
    planes = [0, 1]

    results = []
    for ch in channels:
        for bp in planes:
            try:
                output = _lsb_extract(path, channel=ch, bit_plane=bp)
                if "提取的文本" in output or "嵌入式文件" in output:
                    results.append(f"\n--- {ch.upper()} 通道, bit {bp} ---\n{output}")
            except Exception:
                pass

    if not results:
        return "各通道 LSB 提取均无可读结果"
    return "LSB 自动扫描结果:" + "".join(results)


# ── 图片元数据分析 ────────────────────────────────────────────────

def _image_metadata(path: str) -> str:
    """提取图片 EXIF 等元数据。"""
    if not HAS_PIL:
        return "错误: 需要 PIL 库 (pip install Pillow)"

    try:
        img = Image.open(path)
    except Exception as e:
        return f"打开图片失败: {e}"

    lines = [
        f"文件名: {path}",
        f"格式: {img.format}",
        f"尺寸: {img.size[0]} × {img.size[1]}",
        f"模式: {img.mode}",
        f"调色板: {'有' if img.palette else '无'}",
    ]

    # EXIF 数据
    exif_data = img.getexif()
    if exif_data:
        exif_tags = {
            271: "制造商", 272: "型号", 306: "拍摄时间",
            36867: "原始时间", 33434: "曝光时间", 33437: "F 值",
            34855: "ISO 速度", 37377: "快门速度", 37378: "光圈值",
            40961: "颜色空间", 40962: "像素 X 尺寸", 40963: "像素 Y 尺寸",
        }
        lines.append("\nEXIF 元数据:")
        for tag_id, tag_name in exif_tags.items():
            val = exif_data.get(tag_id)
            if val:
                lines.append(f"  {tag_name}: {val}")

        # 显示所有 EXIF
        remaining = [(k, v) for k, v in exif_data.items() if k not in exif_tags]
        if remaining and len(remaining) <= 30:
            for k, v in remaining:
                lines.append(f"  Tag(0x{k:04x}): {v}")

    # 像素数据分析
    pixels = list(img.getdata())
    total = len(pixels)
    unique_colors = len(set(pixels[:10000]))  # 前 10000 像素
    lines.append(f"\n像素分析:")
    lines.append(f"  总像素: {total}")
    lines.append(f"  前 10000 像素中的独特颜色数: {unique_colors}")
    if unique_colors <= 2 and total > 100:
        lines.append("  提示: 仅 2 种颜色，可能是二维码/二值图！")
    if unique_colors < 100:
        lines.append("  提示: 颜色数较少，可能存在隐藏信息")

    # 检查是否有透明通道
    if img.mode == "RGBA":
        bands = img.split()
        alpha = bands[3]
        alpha_pixels = list(alpha.getdata())
        varied_alpha = len(set(alpha_pixels[:10000]))
        if varied_alpha > 2:
            lines.append(f"  Alpha 通道有 {varied_alpha} 种不同值，可能隐藏数据")
        # 全透明/全不透明检查
        unique_alpha = set(alpha_pixels)
        if len(unique_alpha) == 2 and 0 in unique_alpha and 255 in unique_alpha:
            lines.append(f"  Alpha 通道含透明/不透明两种值，可能是二维码掩码")

    return "\n".join(lines)


# ── 频域分析 ──────────────────────────────────────────────────────

def _frequency_analysis(path: str) -> str:
    """对图片数据进行简单的字节频率分析，检测隐藏数据。"""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        return f"读取文件失败: {e}"

    # 字节频率分布
    freq = [0] * 256
    for b in data:
        freq[b] += 1

    # 找出高频和低频字节
    total = len(data)
    entropy = 0.0
    for c in freq:
        if c > 0:
            p = c / total
            import math
            entropy -= p * math.log2(p)

    sorted_bytes = sorted(range(256), key=lambda i: freq[i], reverse=True)

    lines = [
        f"文件大小: {total} 字节",
        f"熵值: {entropy:.4f} (0-8, 越高越随机)",
    ]

    # 低熵提示
    if entropy < 6.0:
        lines.append("提示: 低熵值，数据可能有结构化冗余（如隐写嵌入）")

    lines.append("\n最常见字节 (Top 20):")
    for i in range(20):
        b = sorted_bytes[i]
        pct = freq[b] / total * 100
        c = chr(b) if 32 <= b <= 126 else "."
        lines.append(f"  0x{b:02x} ({c}): {freq[b]:>8} 次 ({pct:.2f}%)")

    # 检查文件末尾附加数据
    # 对于常见图片格式，查找文件结束标记后的额外数据
    end_markers = [
        (b"\xff\xd9", "JPEG (FFD9)", 0),
        (b"\x00\x00\x00\x00IEND", "PNG (IEND)", 4),  # +4 跳过 CRC
    ]
    for marker, fmt_name, extra in end_markers:
        pos = data.rfind(marker)
        if pos >= 0:
            trailing = data[pos + len(marker) + extra:]
            if len(trailing) > 16:
                lines.append(f"\n在 {fmt_name} 结束标记后发现 {len(trailing)} 字节额外数据!")
                lines.append(f"  前 64 字节: {' '.join(f'{b:02x}' for b in trailing[:64])}")
                try:
                    text = trailing.decode("utf-8", errors="replace")
                    readable = "".join(c if 32 <= ord(c) <= 126 else "" for c in text)
                    if len(readable) > 10:
                        lines.append(f"  可读文本: {readable[:200]}")
                except Exception:
                    pass

    return "\n".join(lines)


# ── 工具类 ──────────────────────────────────────────────────────

class StegoTool(BaseTool):
    """隐写分析工具 — LSB 提取、图片元数据、频域分析、频谱图提示。"""
    modes = {"ctf"}

    @property
    def tags(self):
        return ("stego", "image", "audio")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "")
        path = arguments.get("path", "")
        params = arguments.get("params", {})

        if not path:
            return "错误: 需要文件路径参数"
        if not os.path.exists(path):
            alt = os.path.join("attachments", path)
            if os.path.exists(alt):
                path = alt

        if action == "lsb":
            return _lsb_extract(
                path,
                channel=params.get("channel", "rgb"),
                bit_plane=params.get("bit_plane", 0),
                msb_first=params.get("msb_first", True),
            )

        elif action == "lsb_all":
            return _lsb_extract_all(path)

        elif action == "metadata":
            return _image_metadata(path)

        elif action == "freq":
            return _frequency_analysis(path)

        elif action == "entropy":
            return _frequency_analysis(path)

        elif action == "zsteg":
            return (
                "zsteg 是一个外部工具，用于检测 PNG/BMP 的 LSB 隐写。\n"
                "请在远程服务器上安装: gem install zsteg\n"
                "用法: zsteg <filename>\n"
                "或者使用本工具的 lsb/lsb_all 动作进行基本 LSB 提取。"
            )

        else:
            return (
                f"未知 action: {action}\n"
                "可用: lsb, lsb_all, metadata, freq, zsteg"
            )

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "stego_tools",
                "description": (
                    "隐写分析工具。支持: "
                    "1) lsb — 从图片指定通道/位平面提取 LSB 数据; "
                    "2) lsb_all — 自动扫描所有 LSB 组合; "
                    "3) metadata — 提取图片 EXIF 元数据和像素分析; "
                    "4) freq — 字节频率分析 + 文件尾附加数据检测; "
                    "5) zsteg — 外部工具 zsteg 使用说明。"
                    "需要 Pillow 库 (pip install Pillow)。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["lsb", "lsb_all", "metadata", "freq", "zsteg"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "文件路径",
                        },
                        "params": {
                            "type": "object",
                            "description": (
                                "LSB 参数: {channel: 'r'/'g'/'b'/'rgb'(默认), "
                                "bit_plane: 0(默认)/1, msb_first: true(默认)/false}"
                            ),
                        },
                    },
                    "required": ["action", "path"],
                },
            },
        }
