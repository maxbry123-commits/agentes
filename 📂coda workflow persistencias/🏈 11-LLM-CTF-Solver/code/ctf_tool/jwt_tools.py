"""JWT 工具集 — 解析、伪造、密钥爆破、漏洞检测。"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Dict

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


def _fmt_jwt_ts(ts) -> str:
    """格式化 JWT 时间戳，兼容 int/float/str 三种类型。"""
    try:
        ts_int = int(ts)
    except (TypeError, ValueError):
        return f"{ts} (无法解析为时间戳)"
    from datetime import datetime
    try:
        return str(datetime.fromtimestamp(ts_int))
    except (OSError, OverflowError, ValueError):
        return f"{ts_int} (时间戳超出可表示范围)"


def _b64url_decode(data: str) -> bytes:
    """URL-safe base64 解码。"""
    data = data.replace("-", "+").replace("_", "/")
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.b64decode(data)


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 编码。"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _jwt_decode(token: str) -> str:
    """解码 JWT 的 header 和 payload（不验证签名）。"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return "错误: 不是有效的 JWT 格式（应为 header.payload.signature）"

        header_json = _b64url_decode(parts[0])
        payload_json = _b64url_decode(parts[1])
        header = json.loads(header_json)
        payload = json.loads(payload_json)

        lines = [
            "=== JWT Header ===",
            json.dumps(header, indent=2, ensure_ascii=False),
            "",
            "=== JWT Payload ===",
            json.dumps(payload, indent=2, ensure_ascii=False),
            "",
            "=== 签名 ===",
            parts[2][:50] + ("..." if len(parts[2]) > 50 else ""),
        ]

        # 算法分析
        alg = header.get("alg", "未知")
        lines.append(f"\n算法: {alg}")
        if alg == "none":
            lines.append("⚠ 警告: 使用 'none' 算法，可以伪造任意 payload！")
        elif alg == "HS256":
            lines.append("提示: HS256 使用对称密钥，可尝试爆破弱密钥。")
        elif alg in ("RS256", "RS384", "RS512"):
            lines.append("提示: 非对称算法，检查是否可获取公钥进行验证/伪造。")

        # 时间戳分析
        if "iat" in payload:
            lines.append(f"签发时间: {_fmt_jwt_ts(payload['iat'])}")
        if "exp" in payload:
            lines.append(f"过期时间: {_fmt_jwt_ts(payload['exp'])}")
        if "nbf" in payload:
            lines.append(f"生效时间: {_fmt_jwt_ts(payload['nbf'])}")

        return "\n".join(lines)
    except Exception as e:
        return f"JWT 解码失败: {e}"


def _jwt_forge(payload_str: str, secret: str = "", alg: str = "HS256") -> str:
    """伪造 JWT — 使用指定密钥和算法生成新 token。"""
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        return f"Payload JSON 格式错误: {e}"

    header = {"alg": alg, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}"

    if alg == "none":
        signature = ""
    elif alg.startswith("HS"):
        hash_func = alg.replace("HS", "sha").lower()
        hash_obj = getattr(hashlib, hash_func, None)
        if hash_obj is None:
            return f"错误: 不支持的哈希算法 {hash_func} (来自 JWT 算法 {alg})"
        sig = hmac.new(
            secret.encode(), message.encode(), hash_obj
        ).digest()
        signature = _b64url_encode(sig)
    else:
        return f"不支持的算法: {alg}（仅支持 HS256/HS384/HS512 和 none）"

    token = f"{message}.{signature}" if signature else f"{message}."
    return f"伪造的 JWT:\n{token}"


# 爆破上限 — 防止过大的字典或过慢的循环导致 agent 卡死
_MAX_BRUTE_ATTEMPTS = 200000
_BRUTE_TIMEOUT = 300  # 秒


def _jwt_brute_force(token: str, wordlist_path: str) -> str:
    """爆破 JWT HS256 弱密钥。"""
    if not os.path.exists(wordlist_path):
        return f"错误: 字典文件不存在: {wordlist_path}"

    parts = token.split(".")
    if len(parts) != 3:
        return "错误: 无效 JWT 格式"
    message = f"{parts[0]}.{parts[1]}"
    target_sig = _b64url_decode(parts[2])

    total = 0
    start = time.monotonic()
    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                secret = line.strip()
                if not secret:
                    continue
                total += 1
                sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
                if sig == target_sig:
                    return f"找到密钥: {secret}\n(尝试了 {total} 个密码)"

                if total % 10000 == 0:
                    logger.info(f"JWT 爆破中... 已尝试 {total} 个密码")
                # 上限检查
                if total >= _MAX_BRUTE_ATTEMPTS:
                    return (f"已达到爆破上限 ({_MAX_BRUTE_ATTEMPTS} 个)，停止爆破。\n"
                            f"未找到密钥（尝试了 {total} 个密码）")
                if time.monotonic() - start > _BRUTE_TIMEOUT:
                    elapsed = int(time.monotonic() - start)
                    return (f"爆破超时 ({_BRUTE_TIMEOUT}s)，停止爆破。\n"
                            f"未找到密钥（尝试了 {total} 个密码，用时 {elapsed}s）")
    except Exception as e:
        return f"读取字典文件失败: {e}"

    return f"未找到密钥（已尝试 {total} 个密码）"


def _jwt_vulnerability_scan(token: str) -> str:
    """扫描 JWT 常见漏洞。"""
    parts = token.split(".")
    if len(parts) != 3:
        return "错误: 无效 JWT 格式"

    try:
        header = json.loads(_b64url_decode(parts[0]))
        payload = json.loads(_b64url_decode(parts[1]))
    except Exception as e:
        return f"解析失败: {e}"

    findings = []
    alg = header.get("alg", "")

    # 1. none 算法
    if alg.lower() == "none":
        findings.append("严重: 使用 'none' 算法，签名可被绕过")

    # 2. HS256 暴力破解
    if alg.startswith("HS"):
        findings.append(f"中危: {alg} 使用对称密钥，可尝试字典爆破")

    # 3. 密钥混淆 (alg confusion)
    if alg.startswith("RS") or alg.startswith("ES"):
        findings.append("提示: 非对称算法 — 检查是否可用公钥作为 HS256 密钥（算法混淆攻击）")

    # 4. kid 注入
    if "kid" in header:
        findings.append(f"提示: 包含 kid 字段 ({header['kid']}) — 检查是否存在路径遍历/SQL 注入")

    # 5. jku/jwk 头
    if "jku" in header:
        findings.append(f"提示: 包含 jku 字段 ({header['jku']}) — 检查是否指向可控 URL")
    if "jwk" in header:
        findings.append("提示: 包含嵌入式 jwk 密钥")

    # 6. 过期 token
    if "exp" in payload:
        from time import time
        if payload["exp"] < time():
            findings.append("信息: Token 已过期")
    else:
        findings.append("信息: Token 无过期时间（永不过期）")

    if not findings:
        findings.append("未发现已知漏洞模式")

    return "\n".join(f"  {f}" for f in findings)


# ── 工具类 ──────────────────────────────────────────────────────

class JwtTools(BaseTool):
    """JWT 工具集 — 解析、伪造、密钥爆破、漏洞检测。"""

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "decode")
        token = arguments.get("token", "")

        if action == "decode":
            if not token:
                return "错误: 需要 token 参数"
            return _jwt_decode(token)

        elif action == "forge":
            payload = arguments.get("payload", "{}")
            secret = arguments.get("secret", "")
            alg = arguments.get("alg", "HS256")
            return _jwt_forge(payload, secret, alg)

        elif action == "brute_force":
            if not token:
                return "错误: 需要 token 参数"
            wordlist = arguments.get("wordlist", "")
            if not wordlist:
                return "错误: 需要 wordlist 参数（字典文件路径）"
            return _jwt_brute_force(token, wordlist)

        elif action == "scan":
            if not token:
                return "错误: 需要 token 参数"
            return _jwt_vulnerability_scan(token)

        else:
            return f"未知 action: {action}\n可用: decode, forge, brute_force, scan"

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "jwt_tools",
                "description": (
                    "JWT 分析与攻击工具。支持: "
                    "1) decode — 解码 JWT header/payload (不验证签名) 并分析算法和时间戳; "
                    "2) forge — 使用指定密钥和算法伪造 JWT; "
                    "3) brute_force — 字典爆破 HS256 弱密钥; "
                    "4) scan — JWT 漏洞扫描 (none算法/密钥混淆/kid注入/jku/jwk/过期检测)。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["decode", "forge", "brute_force", "scan"],
                            "description": "操作类型",
                        },
                        "token": {
                            "type": "string",
                            "description": "JWT token 字符串",
                        },
                        "payload": {
                            "type": "string",
                            "description": "forge 操作的新 payload (JSON字符串)",
                        },
                        "secret": {
                            "type": "string",
                            "description": "forge 操作的签名密钥",
                        },
                        "alg": {
                            "type": "string",
                            "description": "forge 操作的算法 (默认 HS256, 也支持 HS384/HS512/none)",
                        },
                        "wordlist": {
                            "type": "string",
                            "description": "brute_force 操作的字典文件路径",
                        },
                    },
                    "required": ["action"],
                },
            },
        }
