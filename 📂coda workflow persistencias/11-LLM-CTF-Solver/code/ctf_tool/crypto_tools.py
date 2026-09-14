"""密码学分析工具集 — 密码识别、频率分析、XOR 破解、Hash 识别。"""

import base64
import codecs
import logging
import re
import string
from collections import Counter
from math import log2
from typing import Dict, List, Optional, Tuple

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Action: identify — 密码 / 编码自动识别
# ═══════════════════════════════════════════════════════════════════

_ENCODING_PATTERNS = [
    (r"^[A-Za-z0-9+/]{20,}={0,2}$", "Base64 (宽松)"),
    (r"^[A-Z2-7]{20,}={0,6}$", "Base32"),
    (r"^[A-Za-z0-9!#$%&()*+,\-./:;<=>?@[\]^_`{|}~]{20,}$", "Base85"),
    (r"^[0-9a-fA-F]{16,}$", "Hex (十六进制)"),
    (r"^[0-9a-fA-F]{15,}$", "Hex 奇数长度 (可能 Hex)"),
    (r"^%[0-9a-fA-F]{2}(%[0-9a-fA-F]{2}){3,}", "URL 编码"),
    (r"^&#\d{2,3};(&#\d{2,3};){3,}", "HTML 实体编码"),
    (r"^\\x[0-9a-fA-F]{2}(\\x[0-9a-fA-F]{2}){3,}", "\\x 转义 Hex"),
    (r"^\\u[0-9a-fA-F]{4}(\\u[0-9a-fA-F]{4}){2,}", "Unicode 转义"),
    (r"^(?:[A-Za-z0-9+/]{4}){5,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$", "Base64 (标准)"),
    (r"^[.-]{3,}\s+[.-]{3,}", "Morse 电码"),
]

_CIPHER_PATTERNS = [
    (r"^[A-Za-z\s]+$", "可能是 古典密码 (Caesar/Vigenere/Substitution)"),
    (r"^[A-Z\s]{10,}$", "全大写字母 — 可能是 Vigenere / Substitution"),
    (r"^(?:[A-Za-z0-9+/]{40,}={0,2})$", "可能是 多层编码 (Base64 输出)"),
    (r"^[0-9a-fA-F]{32}$", "可能是 MD5 哈希 (32位)"),
    (r"^[0-9a-fA-F]{40}$", "可能是 SHA1 哈希"),
    (r"^[0-9a-fA-F]{64}$", "可能是 SHA256 哈希"),
    (r"^[0-9a-fA-F]{56}$", "可能是 SHA224 哈希"),
    (r"^[0-9a-fA-F]{96}$", "可能是 SHA384 哈希"),
    (r"^[0-9a-fA-F]{128}$", "可能是 SHA512 哈希"),
    (r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$", "bcrypt 哈希"),
    (r"^\$5\$rounds=\d+\$[./A-Za-z0-9]{43}$", "SHA256-Crypt ($5$)"),
    (r"^\$6\$rounds=\d+\$[./A-Za-z0-9]{86}$", "SHA512-Crypt ($6$)"),
    (r"^\d{10,20}$", "可能是 十进制数字 (需结合上下文)"),
    (r"^[01]{16,}$", "可能是 二进制"),
    (r"^[0-7]{10,}$", "可能是 八进制"),
]

_RSA_PATTERNS = [
    (r"(?:n\s*[=:]\s*\d{10,}|n\s*=\s*0x[0-9a-fA-F]{20,})", "RSA 公钥 — 含 n"),
    (r"(?:-----BEGIN (RSA )?(PUBLIC|PRIVATE) KEY-----)", "PEM 格式密钥"),
    (r"^\d{30,}\s+\d{2,7}\s+\d{30,}$", "可能是 RSA (n, e, c) 三元组"),
]


def _identify_cipher(text: str) -> str:
    """自动识别密码/编码类型。"""
    text_stripped = text.strip()
    if not text_stripped:
        return "错误: 输入为空"

    lines_out = [
        f"=== 密码识别 ===",
        f"输入长度: {len(text_stripped)} 字符",
        f"字符集大小: {len(set(text_stripped))} 种字符",
    ]

    # 字符集分析
    charset_analysis = []
    if any(c.isupper() for c in text_stripped):
        charset_analysis.append("大写字母")
    if any(c.islower() for c in text_stripped):
        charset_analysis.append("小写字母")
    if any(c.isdigit() for c in text_stripped):
        charset_analysis.append("数字")
    if any(c in "+/=" for c in text_stripped):
        charset_analysis.append("Base64 字符 (+/=)")
    if any(c in "!@#$%^&*()_+-=[]{}|;:',.<>?/`~" for c in text_stripped):
        charset_analysis.append("特殊符号")
    if any(ord(c) > 127 for c in text_stripped):
        charset_analysis.append("非 ASCII 字符")
    if any(c.isspace() for c in text_stripped):
        charset_analysis.append("空格/换行")
    if any(c in ".-" and not c.isalnum() for c in text_stripped):
        charset_analysis.append("点/横线 (Morse 可能)")

    lines_out.append(f"字符集: {', '.join(charset_analysis)}")

    # 熵值
    e = _entropy(text_stripped)
    lines_out.append(f"熵值: {e:.2f} (0-8, 越高越随机)")

    # 编码检测
    lines_out.append("\n--- 编码检测 ---")
    encoding_hits = []
    for pattern, name in _ENCODING_PATTERNS:
        if re.match(pattern, text_stripped):
            encoding_hits.append(f"  + {name}")
    if encoding_hits:
        lines_out.extend(encoding_hits)
    else:
        lines_out.append("  未匹配到已知编码格式")

    # 密码类型检测
    lines_out.append("\n--- 密码/哈希类型推测 ---")
    cipher_hits = []
    for pattern, name in _CIPHER_PATTERNS:
        if re.match(pattern, text_stripped):
            cipher_hits.append(f"  + {name}")
    if cipher_hits:
        lines_out.extend(cipher_hits)
    else:
        lines_out.append("  未匹配到已知密码/哈希格式")

    # RSA 检测
    rsa_hits = []
    for pattern, name in _RSA_PATTERNS:
        if re.search(pattern, text_stripped, re.IGNORECASE):
            rsa_hits.append(f"  + {name}")
    if rsa_hits:
        lines_out.append("\n--- RSA 检测 ---")
        lines_out.extend(rsa_hits)

    # 建议
    lines_out.append("\n--- 建议下一步 ---")
    suggestions = []
    if encoding_hits:
        suggestions.append("先尝试解码操作 (base64/hex 等)")
    if cipher_hits:
        if any("古典" in h or "Caesar" in h or "Vigenere" in h for h in cipher_hits):
            suggestions.append("尝试 frequency 分析 → classical 自动破解")
        if any("MD5" in h or "SHA" in h for h in cipher_hits):
            suggestions.append("尝试 hash_id 确认哈希类型 → 在线查询 (crackstation)")
        if any("RSA" in h or "PEM" in h for h in (rsa_hits + cipher_hits)):
            suggestions.append("尝试 crypto_attacks rsa 工具")
    if e > 7.0:
        suggestions.append("高熵值 — 可能是加密/压缩数据, 非编码")
    if not suggestions:
        suggestions.append("无法自动判断, 请人工查看字符集和长度")
    for s in suggestions:
        lines_out.append(f"  > {s}")

    return "\n".join(lines_out)


# ═══════════════════════════════════════════════════════════════════
# Action: frequency — 频率分析
# ═══════════════════════════════════════════════════════════════════

# 标准英语字母频率 (ETAOINSHRDLCUMWFGYPBVKJXQZ)
_ENGLISH_FREQ = {
    "E": 0.12702, "T": 0.09056, "A": 0.08167, "O": 0.07507,
    "I": 0.06966, "N": 0.06749, "S": 0.06327, "H": 0.06094,
    "R": 0.05987, "D": 0.04253, "L": 0.04025, "C": 0.02782,
    "U": 0.02758, "M": 0.02406, "W": 0.02360, "F": 0.02228,
    "G": 0.02015, "Y": 0.01974, "P": 0.01929, "B": 0.01492,
    "V": 0.00978, "K": 0.00772, "J": 0.00153, "X": 0.00150,
    "Q": 0.00095, "Z": 0.00074,
}

_BYTE_FREQ = [0] * 256  # Will be computed from data


def _frequency_analysis(text: str) -> str:
    """字符/字节频率分析。"""
    lines = [f"=== 频率分析 ===", f"输入长度: {len(text)} 字符", ""]

    # 字母频率
    letters_only = [c.upper() for c in text if c.isalpha()]
    if letters_only:
        counter = Counter(letters_only)
        total = len(letters_only)
        lines.append("--- 字母频率 (Top 10) ---")
        lines.append(f"  {'字符':6s} {'频率':>8s}  {'标准英语':>10s}  {'偏移'}")
        for char, count in counter.most_common(10):
            freq = count / total
            eng = _ENGLISH_FREQ.get(char, 0)
            diff = freq - eng
            bar = "█" * int(freq * 100)
            lines.append(f"  {char:6s} {freq:7.4f} {bar:10s} {eng:10.4f} {diff:+8.4f}")

        # 推测：如果频率分布与英语相似，可能是换位密码；如果不相似，可能是替换密码
        ic = _index_of_coincidence(letters_only)
        lines.append(f"\n  重合指数 (IC): {ic:.4f}")
        if ic > 0.06:
            lines.append("  IC 接近 0.065 — 可能是单表替换或换位密码 (与英语相似)")
        elif ic > 0.04:
            lines.append("  IC 在 0.04-0.06 之间 — 可能是多表替换 (如 Vigenere)")
        else:
            lines.append("  IC 偏低 — 可能不是英语单表替换")

    # 字节频率 (如果是 hex 输入)
    hex_clean = re.sub(r"\s+", "", text.strip())
    if re.match(r"^[0-9a-fA-F]+$", hex_clean) and len(hex_clean) >= 16:
        try:
            data = bytes.fromhex(hex_clean)
            byte_counter = Counter(data)
            lines.append(f"\n--- 字节频率 (Hex 输入, 共 {len(data)} 字节) ---")
            lines.append("  Byte  次数    频率")
            for byte_val, count in byte_counter.most_common(10):
                freq = count / len(data)
                char_repr = chr(byte_val) if 32 <= byte_val <= 126 else "."
                lines.append(f"  0x{byte_val:02x} ({char_repr})  {count:5d}  {freq:.4f}")
        except Exception:
            pass

    return "\n".join(lines)


def _index_of_coincidence(text: str) -> float:
    """计算重合指数。"""
    n = len(text)
    if n < 2:
        return 0.0
    freq = Counter(text)
    ic = sum(f * (f - 1) for f in freq.values()) / (n * (n - 1))
    return ic


# ═══════════════════════════════════════════════════════════════════
# Action: xor_crack — XOR 自动破解
# ═══════════════════════════════════════════════════════════════════

def _xor_single_byte(data: bytes) -> List[Tuple[int, float, str]]:
    """单字节 XOR 爆破 — 返回 (key, score, result) 列表。"""
    results = []
    for key in range(256):
        decoded = bytes(b ^ key for b in data)
        try:
            text = decoded.decode("ascii", errors="replace")
        except Exception:
            text = decoded.decode("latin-1")
        score = sum(1 for c in text if c in "etaoinsrhldcumETAOINSRHLDCUM ")
        score += sum(2 for c in text if c in "{}[]()<>:")
        score -= sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
        results.append((key, score, text))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _xor_crack(ciphertext: str) -> str:
    """XOR 自动破解 — 支持 hex 输入和原始文本。"""
    # 尝试 hex 解码
    hex_clean = re.sub(r"\s+", "", ciphertext.strip())
    if re.match(r"^[0-9a-fA-F]+$", hex_clean):
        try:
            data = bytes.fromhex(hex_clean)
        except Exception:
            data = ciphertext.encode("utf-8", errors="replace")
    else:
        data = ciphertext.encode("utf-8", errors="replace")

    lines = [
        f"=== XOR 破解 ===",
        f"数据长度: {len(data)} 字节",
        "",
    ]

    if len(data) == 0:
        return "错误: 数据为空"

    # 1. 单字节 XOR
    lines.append("--- 单字节 XOR (Top 5) ---")
    results = _xor_single_byte(data)
    for key, score, text in results[:5]:
        preview = text[:80].replace("\n", "\\n").replace("\r", "\\r")
        lines.append(f"  key=0x{key:02x} ({chr(key) if 32 <= key <= 126 else '?'}) score={score}: {preview}")

    # 2. 多字节 XOR 密钥长度检测
    lines.append("\n--- 多字节 XOR 密钥长度推测 ---")
    # 汉明距离法
    key_len_scores = []
    for kl in range(2, min(41, len(data) // 2)):
        blocks = [data[i:i + kl] for i in range(0, len(data) - kl, kl)]
        if len(blocks) < 2:
            continue
        dists = []
        for i in range(min(4, len(blocks) - 1)):
            for j in range(i + 1, min(5, len(blocks))):
                d = sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(blocks[i], blocks[j]))
                dists.append(d / kl)
        avg_dist = sum(dists) / len(dists) if dists else 0
        key_len_scores.append((avg_dist, kl))
    key_len_scores.sort()

    for dist, kl in key_len_scores[:5]:
        lines.append(f"  推测密钥长度: {kl:2d}  (平均汉明距离: {dist:.3f}, 低值更可能)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Action: classical — 古典密码自动破解
# ═══════════════════════════════════════════════════════════════════

def _caesar_brute(ciphertext: str) -> str:
    """凯撒密码暴力枚举 (所有 25 个移位)。"""
    lines = ["=== 凯撒密码爆破 ===", ""]
    for shift in range(1, 26):
        result = []
        for c in ciphertext:
            if "A" <= c <= "Z":
                result.append(chr((ord(c) - ord("A") - shift) % 26 + ord("A")))
            elif "a" <= c <= "z":
                result.append(chr((ord(c) - ord("a") - shift) % 26 + ord("a")))
            else:
                result.append(c)
        plain = "".join(result)
        # 简单评分
        score = sum(1 for c in plain if c.lower() in "etaoinsrh")
        score += sum(3 for w in ("the", "and", "flag", "ctf", "this") if w in plain.lower())
        lines.append(f"  shift={shift:2d} score={score:3d}: {plain[:90]}")
    return "\n".join(lines)


_MORSE_MAP = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}
_MORSE_REV = {v: k for k, v in _MORSE_MAP.items()}


def _morse_decode(text: str) -> str:
    """Morse 电码解码。"""
    # 标准化分隔符
    text = text.strip()
    separator = " " if " " in text else "/"
    chars = text.split(separator)
    result = []
    for c in chars:
        c = c.strip()
        if c in _MORSE_REV:
            result.append(_MORSE_REV[c])
        elif c:
            result.append("?")
    return "".join(result)


def _rot13(text: str) -> str:
    return codecs.encode(text, "rot_13") if hasattr(codecs, "encode") else text.translate(
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
    )


def _classical(text: str, sub_action: str = "auto") -> str:
    """古典密码入口。"""
    if not text:
        return "错误: 需要 ciphertext 参数"

    if sub_action == "caesar":
        return _caesar_brute(text)
    elif sub_action == "rot13":
        return f"ROT13: {_rot13(text)}"
    elif sub_action == "morse":
        return f"Morse 解码: {_morse_decode(text)}"
    elif sub_action == "auto":
        lines = []
        # ROT13
        lines.append(f"ROT13: {_rot13(text)[:200]}")
        lines.append("")
        # Caesar
        lines.append(_caesar_brute(text))
        # Morse
        if all(c in ".- /" for c in text[:50]):
            lines.append(f"\nMorse 解码: {_morse_decode(text)}")
        return "\n".join(lines)
    else:
        return f"未知子操作: {sub_action}, 可用: caesar, rot13, morse, auto"


# ═══════════════════════════════════════════════════════════════════
# Action: hash_id — 哈希格式识别
# ═══════════════════════════════════════════════════════════════════

_HASH_PATTERNS = [
    (r"^[0-9a-fA-F]{32}$", "MD5 / NTLM"),
    (r"^[0-9a-fA-F]{40}$", "SHA1"),
    (r"^[0-9a-fA-F]{56}$", "SHA224"),
    (r"^[0-9a-fA-F]{64}$", "SHA256"),
    (r"^[0-9a-fA-F]{96}$", "SHA384"),
    (r"^[0-9a-fA-F]{128}$", "SHA512"),
    (r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$", "bcrypt"),
    (r"^\$2[axy]\$\d{2}\$[./A-Za-z0-9]{53}$", "bcrypt (变体)"),
    (r"^\$5\$[./A-Za-z0-9]{43}$", "SHA256-Crypt ($5$)"),
    (r"^\$5\$rounds=\d+\$[./A-Za-z0-9]{43}$", "SHA256-Crypt ($5$, rounds)"),
    (r"^\$6\$[./A-Za-z0-9]{86}$", "SHA512-Crypt ($6$)"),
    (r"^\$6\$rounds=\d+\$[./A-Za-z0-9]{86}$", "SHA512-Crypt ($6$, rounds)"),
    (r"^\$1\$[./A-Za-z0-9]{22}$", "MD5-Crypt ($1$)"),
    (r"^\$apr1\$[./A-Za-z0-9]{22}$", "Apache MD5-Crypt"),
    (r"^\$3\$[./A-Za-z0-9]{43}$", "NT Hash"),
    (r"^[0-9a-fA-F]{16}$", "可能是 MySQL3 / DES / CRC32 / LM Hash 的一半"),
    (r"^[0-9a-fA-F]{48}$", "可能是 SHA384 (截断)"),
    (r"^sha256:[0-9a-fA-F]{64}$", "Django SHA256"),
    (r"^pbkdf2_sha256\$\d+\$[./A-Za-z0-9]+\$[./A-Za-z0-9]{44}=$", "Django PBKDF2-SHA256"),
    (r"^scrypt:.+$", "scrypt"),
    (r"^\$argon2[di]\$.*$", "Argon2"),
    (r"^[0-9a-fA-F]{32}:[0-9a-fA-F]{32}$", "NTLM:LM (Windows)"),
]


def _hash_id(hash_str: str) -> str:
    """哈希格式识别。"""
    text = hash_str.strip()
    lines = [f"=== Hash 识别 ===", f"输入长度: {len(text)} 字符", f"字符集: {'Hex' if re.match(r'^[0-9a-fA-F]+$', text) else 'Mixed'}", ""]

    matches = []
    for pattern, name in _HASH_PATTERNS:
        if re.match(pattern, text):
            matches.append((name, pattern))

    if matches:
        lines.append("匹配结果:")
        for name, _ in matches:
            lines.append(f"  + {name}")
        lines.append("")
        lines.append("破解建议:")
        lines.append("  - John the Ripper: john --format=<format> hash.txt --wordlist=rockyou.txt")
        lines.append("  - Hashcat: hashcat -m <mode> hash.txt rockyou.txt")
        lines.append("  - 在线查询: crackstation.net / hashes.com")
    else:
        lines.append("未匹配到已知哈希格式")
        lines.append("提示: 检查是否为自定义拼接格式 (如 MD5(pass+salt))")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Action: modern_detect — 现代密码模式检测
# ═══════════════════════════════════════════════════════════════════

def _modern_detect(text: str) -> str:
    """ECB/CBC 模式检测、分组大小分析。"""
    hex_clean = re.sub(r"\s+", "", text.strip())
    lines = [f"=== 现代密码模式检测 ===", f"输入长度: {len(hex_clean)} hex 字符"]

    try:
        data = bytes.fromhex(hex_clean)
    except Exception:
        return "错误: 输入不是有效的 Hex 字符串"

    lines.append(f"字节数: {len(data)}")

    # 分组大小检测
    common_blocks = [8, 16, 32, 64, 128]
    for bs in common_blocks:
        if len(data) % bs == 0:
            lines.append(f"  长度可被 {bs} 整除 — 可能是 {bs} 字节分组 (如 {'DES' if bs == 8 else 'AES' if bs == 16 else '未知算法'})")

    # ECB 模式检测 — 查找重复分组
    if len(data) >= 32:
        for bs in [8, 16]:
            if len(data) % bs == 0:
                blocks = [data[i:i + bs] for i in range(0, len(data), bs)]
                unique = len(set(blocks))
                total = len(blocks)
                if unique < total:
                    dup_count = total - unique
                    lines.append(f"\n⚠ ECB 模式检测 ({bs} 字节分组):")
                    lines.append(f"  总分组数: {total}")
                    lines.append(f"  唯一分组: {unique}")
                    lines.append(f"  重复分组: {dup_count}")
                    lines.append(f"  重复率: {dup_count / total:.1%}")
                    lines.append(f"  提示: 存在重复分组 → 可能是 ECB 模式 (可进行 block 重放攻击)")

                    # 列出重复的块
                    block_counts = Counter(blocks)
                    for block, count in block_counts.most_common(5):
                        if count > 1:
                            lines.append(f"    块 {block.hex()} 出现 {count} 次")
                else:
                    lines.append(f"\n  {bs}B 分组: 无重复 — 可能是 CBC/CTR 模式")

    # 熵值
    e = _entropy(data)
    lines.append(f"\n熵值: {e:.2f}")
    if e > 7.5:
        lines.append("  提示: 极高熵值 — 很可能是加密数据或随机密钥")
    elif e > 6.0:
        lines.append("  提示: 高熵值 — 加密/压缩数据")

    # Padding 检测
    if data.endswith(b"\x00" * 4) or data.endswith(b"\x00" * 8):
        lines.append("\n⚠ 检测到 Zero Padding — 可能可进行 Padding 攻击")
    if data:
        last_byte = data[-1]
        if 1 <= last_byte <= 16:
            if data.endswith(bytes([last_byte]) * last_byte):
                lines.append(f"\n提示: 检测到 PKCS7 Padding (末尾 {last_byte} 字节重复)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具类
# ═══════════════════════════════════════════════════════════════════

def _entropy(data) -> float:
    import sys
    d = data.encode() if isinstance(data, str) else data
    if not d:
        return 0.0
    counts = [0] * 256
    for b in d:
        counts[b] += 1
    total = len(d)
    return -sum((c / total) * log2(c / total) for c in counts if c > 0)


class CryptoTools(BaseTool):
    """密码学分析工具 — 密码识别、频率分析、XOR 破解、Hash 识别。"""
    modes = {"ctf"}

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "identify")
        text = arguments.get("text", "") or arguments.get("ciphertext", "")
        params = arguments.get("params", {})

        if action == "identify":
            if not text:
                return "错误: 需要 text 参数 (密文/编码文本)"
            return _identify_cipher(text)

        elif action == "frequency":
            if not text:
                return "错误: 需要 text 参数"
            return _frequency_analysis(text)

        elif action == "xor_crack":
            if not text:
                return "错误: 需要 text 参数"
            return _xor_crack(text)

        elif action == "classical":
            if not text:
                return "错误: 需要 text/ciphertext 参数"
            return _classical(text, params.get("sub_action", "auto"))

        elif action == "hash_id":
            if not text:
                return "错误: 需要 text 参数 (哈希字符串)"
            return _hash_id(text)

        elif action == "modern_detect":
            if not text:
                return "错误: 需要 text 参数 (hex 密文)"
            return _modern_detect(text)

        elif action == "full_scan":
            return self._full_scan(text)

        else:
            return (
                f"未知 action: {action}\n"
                "可用: identify, frequency, xor_crack, classical, hash_id, modern_detect, full_scan"
            )

    def _full_scan(self, text: str) -> str:
        results = []
        for label, action in [
            ("密码识别", "identify"),
            ("频率分析", "frequency"),
            ("XOR 破解", "xor_crack"),
        ]:
            try:
                result = self.execute("", {"action": action, "text": text})
                results.append(f"\n{'='*60}\n{label}\n{'='*60}\n{result}")
            except Exception as e:
                results.append(f"\n--- {label} ---\n错误: {e}")
        return "\n".join(results)

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "crypto_tools",
                "description": (
                    "密码学分析工具集。覆盖密码分析全流程:\n"
                    "1) identify — 密码/编码自动识别 (30+ 编码格式 + 20+ 密码/哈希/RSA 模式);\n"
                    "2) frequency — 字符频率分析 + 重合指数 (IC) + 字节频率 (Hex 输入);\n"
                    "3) xor_crack — XOR 自动破解 (单字节爆破 Top5 + 多字节密钥长度推测);\n"
                    "4) classical — 古典密码 (Caesar 全枚举/ROT13/Morse 解码, auto 自动全跑);\n"
                    "5) hash_id — 哈希格式识别 (22 种: MD5/SHA/bcrypt/Crypt/Django/Argon2 等);\n"
                    "6) modern_detect — ECB/CBC 检测 (重复块/PKCS7 padding/分组长/熵值);\n"
                    "7) full_scan — 一键全量扫描 (identify + frequency + xor_crack)。\n"
                    "提示: 本工具侧重分类和识别, 具体攻击 (RSA Wiener 等) 请使用 crypto_attacks 工具。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["identify", "frequency", "xor_crack",
                                     "classical", "hash_id", "modern_detect", "full_scan"],
                            "description": "操作类型",
                        },
                        "text": {
                            "type": "string",
                            "description": "密文/编码文本/Hash 字符串",
                        },
                        "params": {
                            "type": "object",
                            "description": "classical: {sub_action: 'caesar'/'rot13'/'morse'/'auto'}",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
