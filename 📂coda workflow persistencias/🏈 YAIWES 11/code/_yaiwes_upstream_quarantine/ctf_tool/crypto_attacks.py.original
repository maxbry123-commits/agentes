"""密码学攻击工具集 — RSA 攻击、哈希长度扩展、CBC 翻转、古典密码破解。"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from math import isqrt, gcd

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)

# ── 数论辅助 ──────────────────────────────────────────────────────

def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    """扩展欧几里得算法，返回 (g, x, y) 满足 ax + by = g = gcd(a,b)。"""
    if a == 0:
        return b, 0, 1
    g, x1, y1 = _egcd(b % a, a)
    return g, y1 - (b // a) * x1, x1


def _modinv(a: int, m: int) -> int:
    """模逆。"""
    g, x, _ = _egcd(a, m)
    if g != 1:
        raise ValueError(f"{a} 在模 {m} 下不可逆")
    return x % m


# ── RSA 攻击 ──────────────────────────────────────────────────────

def _rsa_wiener(n: int, e: int) -> Optional[int]:
    """Wiener 攻击：d < N^0.25 时通过连分数分解。"""
    def _continued_fraction(num: int, den: int):
        while den:
            a = num // den
            yield a
            num, den = den, num - a * den

    def _convergents(cf):
        h_prev, k_prev = 0, 1
        h_cur, k_cur = 1, 0
        for a in cf:
            h_next = a * h_cur + h_prev
            k_next = a * k_cur + k_prev
            yield h_next, k_next
            h_prev, k_prev = h_cur, k_cur
            h_cur, k_cur = h_next, k_next

    cf = list(_continued_fraction(e, n))
    for k, d in _convergents(cf):
        if k == 0:
            continue
        if (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        # 解方程 p+q = n - phi + 1, p*q = n
        b = n - phi + 1
        discriminant = b * b - 4 * n
        if discriminant < 0:
            continue
        sqrt_disc = isqrt(discriminant)
        if sqrt_disc * sqrt_disc == discriminant:
            p = (b + sqrt_disc) // 2
            q = (b - sqrt_disc) // 2
            if p * q == n:
                return d
    return None


def _rsa_fermat(n: int) -> Optional[Tuple[int, int]]:
    """Fermat 分解：p 和 q 接近时有效。"""
    a = isqrt(n)
    if a * a < n:
        a += 1
    for _ in range(1 << 20):
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            return (a + b, a - b)
        a += 1
    return None


def _rsa_common_modulus(n: int, e1: int, e2: int, c1: int, c2: int) -> Optional[int]:
    """共模攻击：相同 n，不同 e。要求 gcd(e1, e2) == 1。"""
    g, s1, s2 = _egcd(e1, e2)
    if g != 1:
        return None  # gcd(e1,e2)≠1，共模攻击不成立
    if s1 < 0:
        c1 = _modinv(c1, n)
        s1 = -s1
    if s2 < 0:
        c2 = _modinv(c2, n)
        s2 = -s2
    return (pow(c1, s1, n) * pow(c2, s2, n)) % n


def _iroot(n: int, k: int) -> int:
    """整数 k 次方根（向下取整）— 纯整数牛顿迭代，无浮点精度损失。"""
    if n == 0:
        return 0
    if k == 1:
        return n
    guess = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        new = ((k - 1) * guess + n // (guess ** (k - 1))) // k
        if new >= guess:
            break
        guess = new
    return guess


def _rsa_hastad(ciphertexts: List[Tuple[int, int, int]]) -> Optional[int]:
    """Hastad 广播攻击：相同 e，不同 n。（CRT，e 一般=3 或更小）。"""
    e = ciphertexts[0][1]
    if not all(ct[1] == e for ct in ciphertexts):
        return None

    # CRT 组合
    N = 1
    for n_i, _, _ in ciphertexts:
        N *= n_i

    result = 0
    for n_i, _, c_i in ciphertexts:
        N_i = N // n_i
        inv = _modinv(N_i, n_i)
        result += c_i * N_i * inv

    result %= N
    # 开 e 次方根 — 纯整数牛顿迭代，避免浮点精度丢失
    m = _iroot(result, e)
    if pow(m, e) == result:
        return m
    # 安全网：理论上 CRT 后 m^e==result 必然成立，此循环仅作防御
    for test in range(max(m - 2, 0), m + 3):
        if pow(test, e, ciphertexts[0][0]) == ciphertexts[0][2]:
            return test
    return None


def _rsa_attack(action: str, params: dict) -> str:
    """RSA 攻击统一入口。"""
    n = params.get("n")
    e = params.get("e")
    if not n or not e:
        return "错误: RSA 攻击需要 n 和 e 参数"

    result = []

    if action in ("wiener", "auto"):
        d = _rsa_wiener(n, e)
        if d:
            c = params.get("c")
            m = pow(c, d, n) if c else None
            result.append(f"[Wiener] d = {d}")
            if m:
                # 尝试将 m 解码为文本
                try:
                    text = bytes.fromhex(hex(m)[2:]).decode("utf-8", errors="replace")
                    result.append(f"[Wiener] 明文: {text}")
                except Exception:
                    result.append(f"[Wiener] 明文(十进制): {m}")
        else:
            result.append("[Wiener] 攻击失败（d 可能不够小）")

    if action in ("fermat", "auto"):
        factors = _rsa_fermat(n)
        if factors:
            p, q = factors
            result.append(f"[Fermat] p = {p}")
            result.append(f"[Fermat] q = {q}")
            phi = (p - 1) * (q - 1)
            d = _modinv(e, phi)
            result.append(f"[Fermat] d = {d}")
            c = params.get("c")
            if c:
                m = pow(c, d, n)
                try:
                    text = bytes.fromhex(hex(m)[2:]).decode("utf-8", errors="replace")
                    result.append(f"[Fermat] 明文: {text}")
                except Exception:
                    result.append(f"[Fermat] 明文(十进制): {m}")
        else:
            result.append("[Fermat] 分解失败（p 和 q 可能不够接近）")

    if action in ("common_modulus",):
        e2 = params.get("e2")
        c1 = params.get("c1")
        c2 = params.get("c2")
        if e2 and c1 is not None and c2 is not None:
            m = _rsa_common_modulus(n, e, e2, c1, c2)
            if m:
                try:
                    text = bytes.fromhex(hex(m)[2:]).decode("utf-8", errors="replace")
                    result.append(f"[共模] 明文: {text}")
                except Exception:
                    result.append(f"[共模] 明文(十进制): {m}")
            else:
                result.append("[共模] 攻击失败")
        else:
            result.append("[共模] 缺少 e2/c1/c2 参数")

    if action in ("hastad",):
        ciphertexts = params.get("ciphertexts")
        if ciphertexts:
            ct_list = []
            for item in ciphertexts:
                ct_list.append((item["n"], item["e"], item["c"]))
            m = _rsa_hastad(ct_list)
            if m:
                try:
                    text = bytes.fromhex(hex(m)[2:]).decode("utf-8", errors="replace")
                    result.append(f"[Hastad] 明文: {text}")
                except Exception:
                    result.append(f"[Hastad] 明文(十进制): {m}")
            else:
                result.append("[Hastad] 攻击失败")
        else:
            result.append("[Hastad] 缺少 ciphertexts 参数")

    if not result:
        return "未执行任何攻击，请指定攻击类型 (wiener/fermat/common_modulus/hastad)"

    return "\n".join(result)


# ── 哈希长度扩展攻击 ──────────────────────────────────────────────

def _sha256_pad(message_len: int) -> bytes:
    """计算 SHA256 的填充。"""
    ml_bits = message_len * 8
    padding = b"\x80"
    padding += b"\x00" * ((55 - message_len) % 64)
    padding += ml_bits.to_bytes(8, "big")
    return padding


def _hash_length_extension(params: dict) -> str:
    """模拟哈希长度扩展攻击（针对 SHA256 的 Merkle-Damgård 结构）。

    注意：此函数的 padding 需要在不知道原始密钥的情况下构造，
    实际利用时需要绕过服务器端验证。
    返回扩展后的消息和对应的 padding 信息。
    """
    original_data = params.get("original_data", b"")
    if isinstance(original_data, str):
        original_data = original_data.encode()
    append_data = params.get("append_data", b"")
    if isinstance(append_data, str):
        append_data = append_data.encode()
    known_hash = params.get("known_hash", "")
    key_length = params.get("key_length", 8)

    padding = _sha256_pad(key_length + len(original_data))

    new_message_hex = (original_data + padding + append_data).hex()

    result = [
        "=== 哈希长度扩展攻击 ===",
        f"假设密钥长度: {key_length}",
        f"原始数据: {original_data[:50]}",
        f"追加数据: {append_data[:50]}",
        f"已知哈希: {known_hash}",
        "",
        f"扩展后的消息 (hex): {new_message_hex}",
        f"扩展后的消息长度: {len(original_data) + len(padding) + len(append_data)} 字节",
        "",
        "注意: 实际的哈希扩展需要修改 SHA256 内部状态，",
        "此处仅演示消息构造。完整实现需使用 hlextend 库或",
        "hashpumpy (pip install hlextend)。",
    ]
    return "\n".join(result)


# ── CBC 比特翻转 ──────────────────────────────────────────────────

def _cbc_bit_flip(params: dict) -> str:
    """CBC 模式比特翻转攻击：修改密文块以影响解密后的明文。"""
    ciphertext_hex = params.get("ciphertext", "")
    block_index = params.get("block_index", 0)
    original_text = params.get("original_text", "")
    target_text = params.get("target_text", "")

    if not ciphertext_hex or not original_text or not target_text:
        return "错误: 需要 ciphertext(hex)、original_text、target_text 参数"

    ct = bytes.fromhex(ciphertext_hex)
    if len(original_text) != len(target_text):
        return f"错误: original_text 和 target_text 长度必须相同 ({len(original_text)} != {len(target_text)})"
    if len(original_text) > 16:
        return "错误: original_text/target_text 长度不能超过块大小 (16 字节)，请用 block_index 定位目标块"

    # 修改的是目标块的前一个块
    target_block_start = block_index * 16
    if target_block_start < 16 or target_block_start >= len(ct):
        return f"错误: block_index={block_index} 超出范围"

    prev_block_start = target_block_start - 16
    prev_block = bytearray(ct[prev_block_start:prev_block_start + 16])

    for i in range(len(original_text)):
        prev_block[i] ^= ord(original_text[i]) ^ ord(target_text[i])

    new_ct = ct[:prev_block_start] + bytes(prev_block) + ct[target_block_start:]

    result = [
        "=== CBC 比特翻转 ===",
        f"原始明文: {original_text}",
        f"目标明文: {target_text}",
        f"修改块索引: {block_index} (修改前一个块)",
        "",
        f"原始密文 (hex): {ciphertext_hex}",
        f"修改后密文 (hex): {new_ct.hex()}",
    ]
    return "\n".join(result)


# ── 古典密码 ──────────────────────────────────────────────────────

def _vigenere_decrypt(ciphertext: str, key: str) -> str:
    """维吉尼亚密码解密。"""
    result = []
    key_idx = 0
    for c in ciphertext:
        if "A" <= c <= "Z":
            shift = ord(key[key_idx % len(key)].upper()) - ord("A")
            result.append(chr((ord(c) - ord("A") - shift) % 26 + ord("A")))
            key_idx += 1
        elif "a" <= c <= "z":
            shift = ord(key[key_idx % len(key)].upper()) - ord("A")
            result.append(chr((ord(c) - ord("a") - shift) % 26 + ord("a")))
            key_idx += 1
        else:
            result.append(c)
    return "".join(result)


_ENGLISH_FREQ = [  # 英文字母频率（百分比），A-Z
    8.167, 1.492, 2.782, 4.253, 12.702, 2.228, 2.015, 6.094, 6.966, 0.153,
    0.772, 4.025, 2.406, 6.749, 7.507, 1.929, 0.095, 5.987, 6.327, 9.056,
    2.758, 0.978, 2.360, 0.150, 1.974, 0.074,
]


def _best_shift_chi(group: List[str]) -> int:
    """卡方检验：找到使分组频率最接近英语分布的移位量。"""
    n = len(group)
    if n == 0:
        return 0
    best_shift, best_chi = 0, float("inf")
    for shift in range(26):
        chi = 0.0
        for i in range(26):
            observed = sum(1 for c in group if (ord(c) - 65 - shift) % 26 == i)
            expected = _ENGLISH_FREQ[i] / 100 * n
            if expected > 0:
                chi += (observed - expected) ** 2 / expected
        if chi < best_chi:
            best_chi = chi
            best_shift = shift
    return best_shift


def _vigenere_crack(ciphertext: str) -> str:
    """自动破解维吉尼亚密码（使用重合指数法找密钥长度 + 频率分析找密钥）。"""
    import string

    # 只保留字母
    letters = [c.upper() for c in ciphertext if c.isalpha()]
    if not letters:
        return "错误: 输入中没有字母"

    # 1. 用 Kasiski 测试 / 重合指数找密钥长度
    best_key_len = 1
    best_ic = 0

    for key_len in range(1, min(20, len(letters) // 2) + 1):
        ics = []
        for i in range(key_len):
            group = letters[i::key_len]
            if len(group) < 2:
                continue
            freq = {}
            for c in group:
                freq[c] = freq.get(c, 0) + 1
            n = len(group)
            ic = sum(f * (f - 1) for f in freq.values()) / (n * (n - 1))
            ics.append(ic)
        if ics:
            avg_ic = sum(ics) / len(ics)
            if abs(avg_ic - 0.065) < abs(best_ic - 0.065):
                best_ic = avg_ic
                best_key_len = key_len

    # 2. 频率分析找密钥 — 卡方检验（利用全部 26 字母分布，比单字母法鲁棒）
    key = ""
    for i in range(best_key_len):
        group = letters[i::best_key_len]
        key += chr(_best_shift_chi(group) + ord("A"))

    plaintext = _vigenere_decrypt(ciphertext, key)

    result = [
        "=== 维吉尼亚密码自动破解 ===",
        f"检测到的密钥长度: {best_key_len} (IC={best_ic:.4f})",
        f"推测密钥: {key}",
        "",
        f"解密结果 (前 500 字符):",
        plaintext[:500],
    ]
    if len(plaintext) > 500:
        result.append("... (截断)")
    return "\n".join(result)


def _affine_decrypt(ciphertext: str, a: int, b: int) -> Optional[str]:
    """仿射密码解密：E(x) = (ax + b) mod 26。"""
    try:
        a_inv = _modinv(a % 26, 26)
    except ValueError:
        return None
    result = []
    for c in ciphertext:
        if "A" <= c <= "Z":
            y = ord(c) - ord("A")
            x = (a_inv * (y - b)) % 26
            result.append(chr(x + ord("A")))
        elif "a" <= c <= "z":
            y = ord(c) - ord("a")
            x = (a_inv * (y - b)) % 26
            result.append(chr(x + ord("a")))
        else:
            result.append(c)
    return "".join(result)


def _atbash(ciphertext: str) -> str:
    """Atbash 密码：A<->Z, B<->Y, ..."""
    result = []
    for c in ciphertext:
        if "A" <= c <= "Z":
            result.append(chr(ord("Z") - (ord(c) - ord("A"))))
        elif "a" <= c <= "z":
            result.append(chr(ord("z") - (ord(c) - ord("a"))))
        else:
            result.append(c)
    return "".join(result)


# ── 工具类 ──────────────────────────────────────────────────────

class CryptoAttacksTool(BaseTool):
    """密码学攻击工具 — RSA 攻击 / 哈希扩展 / CBC 翻转 / 古典密码破解。"""
    modes = {"ctf"}

    @property
    def tags(self):
        return ("crypto", "attack")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "")
        params = arguments.get("params", {})

        if action == "rsa":
            sub_action = params.get("type", "auto")
            return _rsa_attack(sub_action, params)

        elif action == "hash_extend":
            return _hash_length_extension(params)

        elif action == "cbc_flip":
            return _cbc_bit_flip(params)

        elif action == "vigenere":
            ciphertext = params.get("ciphertext", "")
            key = params.get("key", "")
            if key:
                plain = _vigenere_decrypt(ciphertext, key)
                return f"解密结果:\n{plain[:1000]}"
            else:
                return _vigenere_crack(ciphertext)

        elif action == "affine":
            ciphertext = params.get("ciphertext", "")
            a = params.get("a", 0)
            b = params.get("b", 0)
            if not ciphertext:
                return "错误: 需要 ciphertext 参数"
            if a == 0:
                # 自动爆破 a, b
                results = []
                for aa in [1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]:
                    for bb in range(26):
                        plain = _affine_decrypt(ciphertext, aa, bb)
                        if plain:
                            score = sum(1 for c in plain if c in "AEIOUaeiou ")
                            results.append((score, aa, bb, plain))
                results.sort(key=lambda x: x[0], reverse=True)
                lines = ["仿射密码自动爆破结果 (Top 5):"]
                for score, aa, bb, plain in results[:5]:
                    lines.append(f"  a={aa:2d}, b={bb:2d} (score={score}): {plain[:120]}")
                return "\n".join(lines)
            else:
                plain = _affine_decrypt(ciphertext, a, b)
                if plain is None:
                    return f"错误: a={a} 在模 26 下不可逆"
                return f"解密结果:\n{plain[:1000]}"

        elif action == "atbash":
            ciphertext = params.get("ciphertext", "")
            if not ciphertext:
                return "错误: 需要 ciphertext 参数"
            return f"Atbash 解密结果:\n{_atbash(ciphertext)[:1000]}"

        elif action == "modular":
            return self._modular_math(params)

        else:
            return (
                f"未知 action: {action}\n"
                "可用: rsa, hash_extend, cbc_flip, vigenere, affine, atbash, modular"
            )

    def _modular_math(self, params: dict) -> str:
        """数论计算工具。"""
        lines = ["=== 数论计算 ==="]
        op = params.get("op", "")

        if op == "gcd":
            a, b = params.get("a", 0), params.get("b", 0)
            g, x, y = _egcd(a, b)
            lines.append(f"gcd({a}, {b}) = {g}")
            lines.append(f"Bezout 系数: x={x}, y={y}")
            lines.append(f"验证: {a}*{x} + {b}*{y} = {a*x + b*y}")

        elif op == "modinv":
            a, m = params.get("a", 0), params.get("m", 0)
            try:
                inv = _modinv(a, m)
                lines.append(f"{a}^-1 mod {m} = {inv}")
                lines.append(f"验证: {a} * {inv} mod {m} = {(a * inv) % m}")
            except ValueError as e:
                lines.append(f"错误: {e}")

        elif op == "factor":
            n = params.get("n", 0)
            fermat = _rsa_fermat(n)
            if fermat:
                p, q = fermat
                lines.append(f"Fermat 分解: {n} = {p} × {q}")
            else:
                lines.append(f"Fermat 分解失败（p 和 q 不够接近）")
                # 简单试除
                temp = n
                factors = []
                for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]:
                    while temp % p == 0:
                        factors.append(p)
                        temp //= p
                    if temp == 1:
                        break
                if factors:
                    lines.append(f"小因子分解: {' × '.join(str(f) for f in factors)}")

        else:
            return f"未知数论操作: {op}，可用: gcd, modinv, factor"

        return "\n".join(lines)

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "crypto_attacks",
                "description": (
                    "密码学攻击工具集。支持: "
                    "1) rsa — RSA 攻击 (wiener/fermat/common_modulus/hastad/auto); "
                    "2) hash_extend — SHA256 哈希长度扩展攻击; "
                    "3) cbc_flip — CBC 模式比特翻转攻击; "
                    "4) vigenere — 维吉尼亚密码解密/自动破解; "
                    "5) affine — 仿射密码解密/自动爆破; "
                    "6) atbash — Atbash 密码解密; "
                    "7) modular — 数论计算 (gcd/modinv/factor)。"
                    "RSA 参数: n/e(必需), c/p/q/e2/c1/c2(可选), ciphertexts(Hastad)。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["rsa", "hash_extend", "cbc_flip",
                                     "vigenere", "affine", "atbash", "modular"],
                            "description": "攻击类型",
                        },
                        "params": {
                            "type": "object",
                            "description": (
                                "参数字典。RSA: {n,e,type,c,p,q,e2,c1,c2,ciphertexts}"
                                "Vigenere: {ciphertext,key(可选,空则自动破解)}"
                                "Affine: {ciphertext,a,b}"
                                "CBC flip: {ciphertext,block_index,original_text,target_text}"
                                "Hash extend: {original_data,append_data,known_hash,key_length}"
                                "Modular: {op,a,b,m,n}"
                            ),
                        },
                    },
                    "required": ["action"],
                },
            },
        }
