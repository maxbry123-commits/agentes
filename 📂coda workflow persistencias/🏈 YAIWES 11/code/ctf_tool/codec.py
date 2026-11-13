"""编码/解码工具集 — 支持常见 CTF 编码格式的自动检测与互转。"""

import base64
import binascii
import re
import urllib.parse
import logging
from typing import Dict, List, Optional

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

# ── 摩斯电码表 ──────────────────────────────────────────────────

MORSE_TO_CHAR = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",", "..--..": "?", ".----.": "'",
    "-.-.--": "!", "-..-.": "/", "-.--.": "(", "-.--.-": ")",
    ".-...": "&", "---...": ":", "-.-.-.": ";", "-...-": "=",
    ".-.-.": "+", "-....-": "-", "..--.-": "_", ".-..-.": '"',
    "...--..": "$", ".--.-.": "@",
}

CHAR_TO_MORSE = {v: k for k, v in MORSE_TO_CHAR.items()}


# ── 核心编解码函数 ──────────────────────────────────────────────

def _decode_base64(s: str) -> Optional[str]:
    try:
        s = s.strip()
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except Exception:
        return None


def _encode_base64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _decode_base32(s: str) -> Optional[str]:
    try:
        s = s.strip()
        return base64.b32decode(s).decode("utf-8", errors="replace")
    except Exception:
        return None


def _encode_base32(s: str) -> str:
    return base64.b32encode(s.encode("utf-8")).decode("ascii")


def _decode_hex(s: str) -> Optional[str]:
    try:
        s = s.strip().replace(" ", "").replace("0x", "").replace("0X", "")
        return bytes.fromhex(s).decode("utf-8", errors="replace")
    except Exception:
        return None


def _encode_hex(s: str) -> str:
    return s.encode("utf-8").hex()


def _decode_url(s: str) -> Optional[str]:
    try:
        return urllib.parse.unquote(s.strip())
    except Exception:
        return None


def _encode_url(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def _decode_unicode_escape(s: str) -> Optional[str]:
    try:
        # 仅替换 \uXXXX / \UXXXXXXXX / \xNN 转义序列，保留原文多字节字符
        # （s.encode("utf-8").decode("unicode_escape") 会把中文等多字节字符按
        #   Latin-1 逐字节解释，产生乱码）
        return re.sub(
            r'\\(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2})',
            lambda m: chr(int(m.group(0)[2:], 16)),
            s,
        )
    except Exception:
        return None


def _encode_unicode_escape(s: str) -> str:
    return "".join(f"\\u{ord(c):04x}" for c in s)


def _rot13(s: str) -> str:
    result = []
    for c in s:
        if "a" <= c <= "z":
            result.append(chr((ord(c) - ord("a") + 13) % 26 + ord("a")))
        elif "A" <= c <= "Z":
            result.append(chr((ord(c) - ord("A") + 13) % 26 + ord("A")))
        else:
            result.append(c)
    return "".join(result)


def _caesar(s: str, shift: int = 3) -> str:
    """凯撒密码，支持自定义移位（默认 ROT3）。"""
    result = []
    for c in s:
        if "a" <= c <= "z":
            result.append(chr((ord(c) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= c <= "Z":
            result.append(chr((ord(c) - ord("A") + shift) % 26 + ord("A")))
        else:
            result.append(c)
    return "".join(result)


def _caesar_bruteforce(s: str) -> str:
    """尝试所有凯撒移位（0-25），返回可读性最好的结果。"""
    candidates = []
    for shift in range(26):
        decoded = _caesar(s, shift)
        score = sum(1 for c in decoded if c in "aeiouAEIOU ")
        candidates.append((score, shift, decoded))
    candidates.sort(key=lambda x: x[0], reverse=True)
    lines = []
    for _, shift, text in candidates[:5]:
        lines.append(f"  shift={shift:2d}: {text[:120]}")
    return "Top 5 凯撒结果:\n" + "\n".join(lines)


def _decode_morse(s: str) -> Optional[str]:
    """摩斯电码 → 文本。支持空格分隔的 . - 字符。"""
    try:
        s = s.strip().replace("_", "-")
        words = re.split(r"\s{2,}|/", s)
        result = []
        for word in words:
            letters = word.strip().split()
            decoded_word = ""
            for letter in letters:
                if letter in MORSE_TO_CHAR:
                    decoded_word += MORSE_TO_CHAR[letter]
                else:
                    return None
            result.append(decoded_word)
        return " ".join(result)
    except Exception:
        return None


def _encode_morse(s: str) -> str:
    """文本 → 摩斯电码。"""
    s = s.upper()
    words = s.split()
    encoded_words = []
    for word in words:
        letters = []
        for c in word:
            if c in CHAR_TO_MORSE:
                letters.append(CHAR_TO_MORSE[c])
            else:
                letters.append(c)
        encoded_words.append(" ".join(letters))
    return " / ".join(encoded_words)


def _decode_binary(s: str) -> Optional[str]:
    """二进制 → 文本。支持空格分隔的 8 位二进制。"""
    try:
        s = s.strip()
        parts = re.split(r"\s+", s)
        chars = []
        for p in parts:
            if set(p) <= {"0", "1"}:
                chars.append(chr(int(p, 2)))
            else:
                return None
        return "".join(chars)
    except Exception:
        return None


def _encode_binary(s: str) -> str:
    return " ".join(format(ord(c), "08b") for c in s)


def _decode_octal(s: str) -> Optional[str]:
    """八进制 → 文本。"""
    try:
        s = s.strip()
        parts = re.split(r"\s+", s.replace("\\", " "))
        chars = []
        for p in parts:
            p = p.strip()
            if p and set(p) <= set("01234567"):
                chars.append(chr(int(p, 8)))
        return "".join(chars) if chars else None
    except Exception:
        return None


def _encode_octal(s: str) -> str:
    return " ".join(format(ord(c), "03o") for c in s)


def _decode_decimal(s: str) -> Optional[str]:
    """十进制 ASCII → 文本。"""
    try:
        s = s.strip()
        parts = re.split(r"\s+|,", s)
        chars = []
        for p in parts:
            p = p.strip()
            if p:
                chars.append(chr(int(p)))
        return "".join(chars) if chars else None
    except Exception:
        return None


def _encode_decimal(s: str) -> str:
    return " ".join(str(ord(c)) for c in s)


def _reverse(s: str) -> str:
    return s[::-1]


def _decode_xor(s: str, key: int = 0) -> str:
    """单字节 XOR 解码。"""
    try:
        data = s.encode("utf-8") if isinstance(s, str) else s
        if key > 0:
            return bytes(b ^ key for b in data).decode("utf-8", errors="replace")
        # key=0 时自动爆破单字节 XOR
        results = []
        for k in range(256):
            decoded = bytes(b ^ k for b in data)
            score = sum(1 for c in decoded if 32 <= c <= 126 or c in (10, 13))
            if score > len(data) * 0.8:
                text = decoded.decode("utf-8", errors="replace").strip()
                if text and all(32 <= ord(c) <= 126 or c in "\n\r\t" for c in text):
                    results.append((score, k, text))
        results.sort(key=lambda x: x[0], reverse=True)
        if results:
            lines = [f"  key=0x{k:02x} ({k}): {text[:120]}" for _, k, text in results[:5]]
            return "Top 5 XOR 结果:\n" + "\n".join(lines)
        return "未找到可读的单字节 XOR 结果"
    except Exception as e:
        return f"XOR 解码失败: {e}"


_WILDCARD_KEY = object()  # sentinel for "key not provided"


# ── 格式自动检测 ────────────────────────────────────────────────

class _FormatMatcher:
    """启发式检测字符串的编码格式。"""

    @staticmethod
    def score(s: str) -> List[tuple]:
        candidates = []

        # base64 — 只含 A-Za-z0-9+/=，长度是 4 的倍数
        b64_pat = re.sub(r"\s", "", s)
        if re.fullmatch(r"[A-Za-z0-9+/=]+", b64_pat) and len(b64_pat) % 4 == 0:
            candidates.append(("base64", 90))

        # base32 — 只含 A-Z2-7=
        b32_pat = re.sub(r"\s", "", s)
        if re.fullmatch(r"[A-Z2-7=]+", b32_pat) and len(b32_pat) % 8 == 0:
            candidates.append(("base32", 85))

        # hex string — 只含 0-9a-fA-F，可能带 0x 前缀
        hex_raw = s.strip().replace("0x", "").replace("0X", "").replace(" ", "")
        if re.fullmatch(r"[0-9a-fA-F]+", hex_raw) and len(hex_raw) % 2 == 0 and len(hex_raw) >= 2:
            try:
                bytes.fromhex(hex_raw)
                candidates.append(("hex", 80))
            except ValueError:
                pass

        # URL encoded
        if "%" in s and re.search(r"%[0-9a-fA-F]{2}", s):
            candidates.append(("url", 75))

        # Unicode escape
        if re.search(r"\\u[0-9a-fA-F]{4}", s):
            candidates.append(("unicode_escape", 75))

        # Morse — 只有 . - 和空格 /
        if re.fullmatch(r"[.\- /\n]+", s.strip()):
            letters = [w for w in s.strip().split() if w != "/"]
            if letters and all(set(w) <= {".", "-"} for w in letters):
                candidates.append(("morse", 85))

        # Binary — 只有 0 1 和空格
        if re.fullmatch(r"[01\s]+", s.strip()):
            parts = s.strip().split()
            if parts and all(len(p) == 8 for p in parts):
                candidates.append(("binary", 80))

        # 八进制 — 只有 0-7 且空格分隔
        if re.fullmatch(r"[0-7\s]+", s.strip()):
            parts = s.strip().split()
            if parts and all(len(p) <= 3 for p in parts):
                candidates.append(("octal", 70))

        # 十进制 — 只有 0-9 且空格/逗号分隔
        if re.fullmatch(r"[0-9,\s]+", s.strip()):
            parts = re.split(r"[\s,]+", s.strip())
            if parts and any(len(p) >= 2 for p in parts):
                candidates.append(("decimal", 70))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates


# ── 工具类 ──────────────────────────────────────────────────────

class CodecTool(BaseTool):
    """编码/解码工具集 — 支持 base64/base32/hex/url/unicode/rot13/
    凯撒/摩斯电码/二进制/八进制/十进制/XOR/反转等操作。"""
    modes = {"ctf"}

    @property
    def tags(self):
        return ("crypto", "encoding", "misc")

    def execute(self, tool_name: str, arguments: dict) -> str:
        operation = arguments.get("operation", "decode")
        content = arguments.get("content", "")
        fmt = arguments.get("format", "auto")
        key = arguments.get("key", _WILDCARD_KEY)
        # 兼容旧参数名
        if key is _WILDCARD_KEY:
            key = arguments.get("shift", 0)

        if not content:
            return "错误: 未提供输入内容"

        if operation == "encode":
            return self._handle_encode(content, fmt)
        elif operation == "detect":
            return self._handle_detect(content)
        else:
            return self._handle_decode(content, fmt, key)

    def _handle_detect(self, content: str) -> str:
        matches = _FormatMatcher.score(content)
        if not matches:
            return "无法自动检测编码格式"
        lines = [f"  {fmt}: score={score}" for fmt, score in matches]
        return "自动检测结果:\n" + "\n".join(lines)

    def _handle_decode(self, content: str, fmt: str, key: int = 0) -> str:
        if fmt == "auto":
            matches = _FormatMatcher.score(content)
            if not matches:
                return "无法自动检测编码格式，请手动指定 format"
            results = []
            seen = set()
            for enc_fmt, _score in matches:
                if enc_fmt in seen:
                    continue
                seen.add(enc_fmt)
                try:
                    result = self._try_decode(content, enc_fmt, key)
                    if result and result != content:
                        results.append((enc_fmt, result))
                except Exception:
                    pass
            if not results:
                return "自动检测失败，所有格式均无法解码"
            lines = [f"  [{fmt}]: {text[:200]}" for fmt, text in results]
            return "自动解码结果 (按匹配度排序):\n" + "\n".join(lines)
        else:
            result = self._try_decode(content, fmt, key)
            if result is None:
                return f"解码失败：无法识别为 {fmt} 格式"
            return result

    def _try_decode(self, content: str, fmt: str, key: int = 0) -> Optional[str]:
        dispatch = {
            "base64": _decode_base64,
            "base32": _decode_base32,
            "hex": _decode_hex,
            "url": _decode_url,
            "unicode_escape": _decode_unicode_escape,
            "rot13": lambda s: _rot13(s),
            "morse": _decode_morse,
            "binary": _decode_binary,
            "octal": _decode_octal,
            "decimal": _decode_decimal,
        }
        handler = dispatch.get(fmt)
        if handler:
            return handler(content)
        if fmt in ("xor", "caesar"):
            if key is not None and key != 0 and key is not _WILDCARD_KEY:
                if fmt == "caesar":
                    return _caesar(content, key)
                return _decode_xor(content, key)
            if fmt == "caesar":
                return _caesar_bruteforce(content)
            return _decode_xor(content, 0)
        return None

    def _handle_encode(self, content: str, fmt: str) -> str:
        dispatch = {
            "base64": _encode_base64,
            "base32": _encode_base32,
            "hex": _encode_hex,
            "url": _encode_url,
            "unicode_escape": _encode_unicode_escape,
            "rot13": _rot13,
            "morse": _encode_morse,
            "binary": _encode_binary,
            "octal": _encode_octal,
            "decimal": _encode_decimal,
            "reverse": _reverse,
        }
        handler = dispatch.get(fmt)
        if not handler:
            return f"不支持的编码格式: {fmt}。可用: {', '.join(dispatch.keys())}"
        return handler(content)

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "codec_tool",
                "description": (
                    "编码/解码工具。支持 base64/base32/hex/url/unicode_escape/"
                    "rot13/caesar/morse/binary/octal/decimal/xor/reverse。"
                    "可用 operation: decode（解码）, encode（编码）, detect（检测格式）。"
                    "format=auto 时自动检测编码格式。xor/caesar 解码时可用 key 指定密钥。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["decode", "encode", "detect"],
                            "description": "操作类型: decode(解码), encode(编码), detect(自动检测)",
                        },
                        "content": {
                            "type": "string",
                            "description": "要处理的文本内容",
                        },
                        "format": {
                            "type": "string",
                            "enum": [
                                "auto", "base64", "base32", "hex", "url",
                                "unicode_escape", "rot13", "caesar", "morse",
                                "binary", "octal", "decimal", "xor", "reverse",
                            ],
                            "description": "编码格式（auto=自动检测）",
                        },
                        "key": {
                            "type": "integer",
                            "description": "XOR 密钥或凯撒移位值。XOR 不指定时自动爆破所有单字节",
                        },
                    },
                    "required": ["operation", "content"],
                },
            },
        }
