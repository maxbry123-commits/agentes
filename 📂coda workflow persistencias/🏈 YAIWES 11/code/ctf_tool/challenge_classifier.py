"""题型自动识别 — 根据题目描述/附件后缀/连接特征判断 CTF 题目类型。"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ── 特征规则 ──────────────────────────────────────────────────────

# 附件后缀 → 题型映射
_EXTENSION_MAP: Dict[str, List[str]] = {
    # PWN / 二进制
    ".elf": ["pwn", "binary"],
    ".so": ["pwn", "binary"],
    ".o": ["pwn", "binary"],
    # 逆向
    ".apk": ["reverse", "mobile"],
    ".dex": ["reverse", "mobile"],
    ".jar": ["reverse"],
    ".class": ["reverse"],
    ".exe": ["reverse", "pwn"],
    ".dll": ["reverse"],
    ".sys": ["reverse"],
    ".bin": ["reverse", "pwn", "forensics"],
    # 密码学
    ".enc": ["crypto"],
    ".encrypted": ["crypto"],
    ".cipher": ["crypto"],
    ".key": ["crypto"],
    ".pem": ["crypto"],
    ".crt": ["crypto"],
    ".cer": ["crypto"],
    ".der": ["crypto"],
    ".asc": ["crypto"],
    ".gpg": ["crypto"],
    ".sage": ["crypto"],
    # 隐写
    ".png": ["stego", "forensics"],
    ".jpg": ["stego", "forensics"],
    ".jpeg": ["stego", "forensics"],
    ".bmp": ["stego", "forensics"],
    ".gif": ["stego", "forensics"],
    ".webp": ["stego", "forensics"],
    ".tiff": ["stego", "forensics"],
    ".wav": ["stego", "forensics"],
    ".mp3": ["stego", "forensics"],
    ".aac": ["stego", "forensics"],
    ".flac": ["stego", "forensics"],
    ".avi": ["stego", "forensics"],
    ".mp4": ["stego", "forensics"],
    ".mkv": ["stego", "forensics"],
    # 取证
    ".pcap": ["forensics"],
    ".pcapng": ["forensics"],
    ".dmp": ["forensics", "pwn"],
    ".mem": ["forensics"],
    ".raw": ["forensics", "stego"],
    ".img": ["forensics"],
    ".dd": ["forensics"],
    ".vhd": ["forensics"],
    ".vmdk": ["forensics"],
    ".e01": ["forensics"],
    ".log": ["forensics"],
    ".evtx": ["forensics"],
    ".reg": ["forensics"],
    ".hive": ["forensics"],
    # Web
    ".sql": ["web"],
    ".php": ["web", "reverse"],
    ".js": ["web", "reverse"],
    ".html": ["web"],
    ".tar": ["web", "forensics"],
    ".tar.gz": ["web", "forensics"],
    ".gz": ["web", "forensics"],
    ".zip": ["web", "stego", "forensics"],
    ".7z": ["web", "forensics"],
    ".rar": ["web", "forensics"],
    # 综合
    ".py": ["reverse", "crypto"],
    ".java": ["reverse"],
    ".c": ["reverse", "pwn"],
    ".cpp": ["reverse", "pwn"],
    ".go": ["reverse", "pwn"],
    ".rs": ["reverse", "pwn"],
    ".s": ["reverse", "pwn"],
    ".asm": ["reverse", "pwn"],
    ".txt": ["misc"],
    ".csv": ["misc", "forensics"],
    ".json": ["web", "misc"],
    ".xml": ["web", "misc"],
    ".yaml": ["web", "misc"],
    ".yml": ["web", "misc"],
    ".pdf": ["misc", "forensics", "stego"],
    ".docx": ["forensics", "misc"],
    ".xlsx": ["forensics", "misc"],
}

# 关键词 → 题型映射（来自题目描述）
_KEYWORD_MAP: List[Tuple[str, str, float]] = [
    # Web
    (r"sql\s*inject|sqli", "web", 0.9),
    (r"cross.?site|xss", "web", 0.9),
    (r"ssrf", "web", 0.9),
    (r"template\s*inject|ssti", "web", 0.9),
    (r"command\s*inject|rce", "web", 0.9),
    (r"file\s*include|lfi|rfi", "web", 0.9),
    (r"upload|文件上传", "web", 0.8),
    (r"bypass|绕过", "web", 0.6),
    (r"jwt|token", "web", 0.8),
    (r"xxe", "web", 0.9),
    (r"csrf", "web", 0.8),
    (r"ssp|sqlmap|burp", "web", 0.7),
    (r"php|jsp|asp\.net", "web", 0.5),
    (r"web|网页|网站|浏览器", "web", 0.6),
    (r"http|https?://|get|post|cookie|session", "web", 0.5),
    # PWN
    (r"buffer\s*overflow|bof|栈溢出|堆溢出|堆喷", "pwn", 0.9),
    (r"rop|ret2libc|ret2text|gadget", "pwn", 0.9),
    (r"format\s*string|格式化字符串", "pwn", 0.9),
    (r"shellcode|shell.?code", "pwn", 0.9),
    (r"integer\s*overflow|整型溢出", "pwn", 0.8),
    (r"use.?after.?free|uaf|释放后使用", "pwn", 0.9),
    (r"heap|堆", "pwn", 0.8),
    (r"canary|nx|pie|aslr|relro", "pwn", 0.8),
    (r"pwntools|checksec|gdb", "pwn", 0.8),
    (r"nc\s+\d+\.\d+\.\d+\.\d+|nc\s+\S+\s+\d+", "pwn", 0.7),
    (r"libc|libc\.so", "pwn", 0.8),
    (r"泄露地址|leak|信息泄露", "pwn", 0.6),
    (r"pwn|二进制利用|二进制漏洞", "pwn", 0.9),
    # Reverse
    (r"reverse|逆向|crackme|逆向分析", "reverse", 0.9),
    (r"flag\s*check|验证|注册|license", "reverse", 0.7),
    (r"反混淆|deobfuscate|obfuscated|混淆", "reverse", 0.8),
    (r"脱壳|unpack|加壳|packed", "reverse", 0.8),
    (r"angr|符号执行", "reverse", 0.9),
    (r"ida|radare2|rizin|ghidra", "reverse", 0.8),
    (r"apk|dex|smali|android", "reverse", 0.7),
    (r"算法分析|algorithm", "reverse", 0.6),
    # Crypto
    (r"rsa|公钥|私钥|加密|解密", "crypto", 0.9),
    (r"aes|des|rc4|blowfish|twofish", "crypto", 0.9),
    (r"md5|sha|哈希|hash", "crypto", 0.8),
    (r"xor|异或|xor加密", "crypto", 0.8),
    (r"维吉尼亚|vigenere|凯撒|caesar|仿射|affine", "crypto", 0.9),
    (r"离散对数|diffie|hellman|dh|椭圆曲线|ecc", "crypto", 0.9),
    (r"cbc|ecb|ctr|gcm|填充攻击|padding.oracle|padbuster", "crypto", 0.9),
    (r"base64|base32|base16|编码|decode|encode", "crypto", 0.6),
    (r"密码|密码学|crypto", "crypto", 0.8),
    (r"low.?exponent|wiener|fermat|hastad|共模|广播", "crypto", 0.9),
    (r"模运算|mod|模逆|欧拉|phi", "crypto", 0.7),
    (r"素数|质数|factor|分解|factorization", "crypto", 0.8),
    (r"openssl|ssl|tls|certificate", "crypto", 0.7),
    # Stego
    (r"隐写|stego|隐写术", "stego", 0.9),
    (r"lsb|最低有效位|bit.?plane|位平面", "stego", 0.9),
    (r"频谱|spectrum|spectrogram", "stego", 0.9),
    (r"exif|元数据|metadata", "stego", 0.7),
    (r"图片|image|png|jpg|gif|bmp", "stego", 0.5),
    (r"音频|audio|wav|mp3|声音", "stego", 0.6),
    (r"二维码|qrcode|qr.?code", "stego", 0.8),
    (r"水印|watermark", "stego", 0.8),
    # Forensics
    (r"取证|forensics|forensic", "forensics", 0.9),
    (r"流量|pcap|pcapng|抓包|数据包|packet", "forensics", 0.9),
    (r"内存|memory|mem|dump|volatility", "forensics", 0.9),
    (r"磁盘|disk|image|镜像|ntfs|fat|ext", "forensics", 0.8),
    (r"注册表|registry|hive|evtx|日志|log", "forensics", 0.8),
    (r"恢复|recover|carve|文件恢复", "forensics", 0.8),
    (r"tshark|wireshark|binwalk|foremost|strings", "forensics", 0.8),
    (r"固件|firmware", "forensics", 0.8),
    (r"文件系统|filesystem|fat|ntfs|ext\d", "forensics", 0.7),
    # Mobile
    (r"mobile|移动|android|ios|frida|objection", "mobile", 0.9),
    (r"apk|dex|smali|xposed|hook", "mobile", 0.9),
    # Misc
    (r"misc|杂项", "misc", 0.8),
    (r"问卷|survey|misc", "misc", 0.7),
    (r"签到|checkin|欢迎", "misc", 0.7),
]

# 连接信息 → 题型映射
_CONNECTION_MAP: List[Tuple[str, str, float]] = [
    (r"http://|https://", "web", 0.6),
    (r"nc\s+\S+\s+\d+", "pwn", 0.7),
    (r"ssh\s+\S+@\S+", "pwn", 0.5),
    (r"telnet", "pwn", 0.5),
    (r":22\b", "pwn", 0.4),
    (r":80\b|:443\b|:8080\b|:8443\b", "web", 0.5),
    (r":3306\b|:5432\b|:6379\b|:27017\b", "web", 0.5),
]


# ── 分类器核心 ────────────────────────────────────────────────────

def _classify_by_files(files: List[str]) -> Dict[str, float]:
    """根据附件后缀判断题型。"""
    scores: Dict[str, float] = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in _EXTENSION_MAP:
            for cat in _EXTENSION_MAP[ext]:
                scores[cat] = scores.get(cat, 0) + 0.4
    return scores


def _classify_by_description(description: str) -> Dict[str, float]:
    """根据题目描述关键词判断题型。"""
    scores: Dict[str, float] = {}
    for pattern, category, weight in _KEYWORD_MAP:
        if re.search(pattern, description, re.IGNORECASE):
            scores[category] = max(scores.get(category, 0), weight)
    return scores


def _classify_by_connection(connection: str) -> Dict[str, float]:
    """根据连接信息判断题型。"""
    scores: Dict[str, float] = {}
    for pattern, category, weight in _CONNECTION_MAP:
        if re.search(pattern, connection, re.IGNORECASE):
            scores[category] = max(scores.get(category, 0), weight)
    return scores


def classify(description: str = "", files: Optional[List[str]] = None,
             connection: str = "") -> Dict:
    """综合分类，返回各题型得分和推荐工具链。"""
    if files is None:
        files = []

    desc_scores = _classify_by_description(description)
    file_scores = _classify_by_files(files) if files else {}
    conn_scores = _classify_by_connection(connection) if connection else {}

    # 合并得分：描述 0.6 + 文件 0.3 + 连接 0.1
    all_categories = set(desc_scores) | set(file_scores) | set(conn_scores)
    combined: Dict[str, float] = {}
    for cat in all_categories:
        score = (
            desc_scores.get(cat, 0) * 0.6 +
            file_scores.get(cat, 0) * 0.3 +
            conn_scores.get(cat, 0) * 0.1
        )
        combined[cat] = round(score, 2)

    # 按得分排序
    sorted_cats = sorted(combined.items(), key=lambda x: -x[1])

    # 推荐工具链
    toolchain = {
        "web": "network_tool, file_analyzer, execute_shell_command (curl/sqlmap/nmap), exploit_templates",
        "pwn": "binary_analysis, execute_python_code (pwntools), execute_shell_command (nc/ROPgadget), python3",
        "reverse": "file_analyzer, binary_analysis, execute_python_code, execute_shell_command (strings/objdump/radare2)",
        "crypto": "codec_tool, crypto_attacks, execute_python_code, execute_shell_command (openssl/sage)",
        "stego": "stego_tools, file_analyzer, execute_shell_command (zsteg/steghide/binwalk/foremost)",
        "forensics": "forensics_tools, file_analyzer, execute_shell_command (tshark/binwalk/volatility/foremost)",
        "mobile": "execute_shell_command (apktool/jadx/dex2jar/frida), file_analyzer",
        "misc": "file_analyzer, codec_tool, execute_shell_command, forensics_tools",
    }

    result = {
        "classification": sorted_cats,
        "primary_type": sorted_cats[0][0] if sorted_cats else "unknown",
        "confidence": sorted_cats[0][1] if sorted_cats else 0,
        "toolchain": toolchain.get(sorted_cats[0][0] if sorted_cats else "", ""),
        "details": {
            "from_description": dict(sorted(desc_scores.items(), key=lambda x: -x[1])[:5]),
            "from_files": dict(sorted(file_scores.items(), key=lambda x: -x[1])[:5]),
            "from_connection": dict(sorted(conn_scores.items(), key=lambda x: -x[1])[:3]),
        },
    }
    return result


def _format_classification(result: Dict) -> str:
    """格式化分类结果。"""
    lines = [
        "=== 题型自动识别 ===",
        "",
        f"判定题型: {result['primary_type']} (置信度: {result['confidence']:.0%})",
        "",
        "得分详情:",
    ]
    for cat, score in result["classification"]:
        bar = "#" * int(score * 10) + "-" * (10 - int(score * 10))
        lines.append(f"  {cat:10s}  {bar}  {score:.2f}")

    lines.append("")
    lines.append("推荐工具链:")
    for tool in result["toolchain"].split(", "):
        lines.append(f"  • {tool}")

    lines.append("")
    lines.append("识别依据:")
    for source, items in result["details"].items():
        if items:
            source_cn = {"from_description": "题目描述", "from_files": "附件后缀",
                         "from_connection": "连接信息"}.get(source, source)
            top = list(items.items())[:3]
            lines.append(f"  [{source_cn}] {' / '.join(f'{k}({v:.2f})' for k, v in top)}")

    return "\n".join(lines)


# ── 工具类 ──────────────────────────────────────────────────────

class ChallengeClassifier(BaseTool):
    """题型自动识别 — 根据题目描述/附件后缀/连接特征自动判断 CTF 题目类型。"""
    modes = {"ctf"}

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "classify")
        description = arguments.get("description", "")

        if action == "classify":
            # 自动检测 attachments 目录中的文件
            files = arguments.get("files", [])
            if not files:
                attach_dir = "attachments"
                if os.path.isdir(attach_dir):
                    files = os.listdir(attach_dir)
                else:
                    files = []

            connection = arguments.get("connection", "")
            result = classify(description, files, connection)
            return _format_classification(result)

        elif action == "rules":
            # 列出所有分类规则供参考
            lines = [
                "=== 分类规则参考 ===",
                "",
                f"后缀规则: {len(_EXTENSION_MAP)} 种",
                f"关键词规则: {len(_KEYWORD_MAP)} 条",
                f"连接规则: {len(_CONNECTION_MAP)} 条",
                "",
                "后缀 → 题型示例:",
            ]
            ext_shown = set()
            for ext, cats in sorted(_EXTENSION_MAP.items()):
                if ext not in ext_shown:
                    lines.append(f"  {ext:8s} → {', '.join(cats)}")
                    ext_shown.add(ext)
                    if len(lines) > 40:
                        lines.append("  ... (截断)")
                        break
            return "\n".join(lines)

        else:
            return f"未知 action: {action}，可用: classify, rules"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "challenge_classifier",
                "description": (
                    "CTF 题目类型自动识别。根据题目描述、附件后缀、连接特征判断题型"
                    " (web/pwn/reverse/crypto/stego/forensics/mobile/misc)，"
                    "并推荐对应的工具链。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["classify", "rules"],
                            "description": "classify=分类, rules=查看规则",
                        },
                        "description": {
                            "type": "string",
                            "description": "题目描述文本",
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "附件文件名列表 (可选，不传则自动扫描 attachments/ 目录)",
                        },
                        "connection": {
                            "type": "string",
                            "description": "连接信息 (如 nc IP port, http://url, ssh user@host)",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
