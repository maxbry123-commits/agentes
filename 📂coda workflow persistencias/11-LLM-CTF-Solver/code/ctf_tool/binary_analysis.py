"""二进制/PWN 分析工具 — ELF 保护检测、pwntools 封装、架构识别。"""

import logging
import os
import struct
from typing import Dict, List, Optional, Tuple

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ── ELF 保护检测 ──────────────────────────────────────────────────

def _check_elf_protections(path: str) -> str:
    """分析 ELF 文件的保护机制（类似 checksec）。"""
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except Exception as e:
        return f"读取失败: {e}"

    if head[:4] != b"\x7fELF":
        return "不是 ELF 文件"

    lines = [f"文件: {path}"]
    elf_class = "32-bit" if head[4] == 1 else "64-bit" if head[4] == 2 else "未知"
    endian = "小端" if head[5] == 1 else "大端" if head[5] == 2 else "未知"
    osabi_map = {0: "System V", 3: "Linux", 9: "FreeBSD"}
    osabi = osabi_map.get(head[7], f"未知(0x{head[7]:02x})")

    lines.append(f"架构: {elf_class}, {endian}, {osabi}")

    # 读取程序头
    e_phoff = struct.unpack_from("<I", head, 0x1C)[0] if elf_class.startswith("32") else struct.unpack_from("<Q", head, 0x20)[0]
    e_phentsize = struct.unpack_from("<H", head, 0x2A if elf_class.startswith("32") else 0x36)[0]
    e_phnum = struct.unpack_from("<H", head, 0x2C if elf_class.startswith("32") else 0x38)[0]

    head_size = 64 if elf_class.startswith("64") else 52
    try:
        with open(path, "rb") as f:
            f.seek(0)
            data = f.read()
    except Exception:
        data = head

    protections = {
        "NX": {"enabled": False, "desc": "栈不可执行"},
        "Canary": {"enabled": False, "desc": "栈保护"},
        "PIE": {"enabled": False, "desc": "位置无关"},
        "RELRO": {"enabled": False, "desc": "只读重定位"},
        "RPATH": {"enabled": False, "desc": "RPATH 风险"},
    }

    # 检查 PT_GNU_STACK (NX)
    # 检查 PT_GNU_RELRO (RELRO)
    # 检查 PT_DYNAMIC 中的 DT_DEBUG (PIE 提示)

    # 通过程序头检测
    ph_offset = e_phoff
    for i in range(min(e_phnum, 64)):
        if ph_offset + e_phentsize > len(data):
            break
        if elf_class.startswith("64"):
            p_type = struct.unpack_from("<I", data, ph_offset)[0]
            p_flags = struct.unpack_from("<I", data, ph_offset + 4)[0]
        else:
            p_type = struct.unpack_from("<I", data, ph_offset)[0]
            p_flags = struct.unpack_from("<I", data, ph_offset + 24)[0]

        # PT_GNU_STACK = 0x6474e551
        if p_type == 0x6474e551:
            protections["NX"]["enabled"] = not bool(p_flags & 1)  # PF_X=1, 无可执行=NX
        # PT_GNU_RELRO = 0x6474e552
        if p_type == 0x6474e552:
            protections["RELRO"]["enabled"] = True
        ph_offset += e_phentsize

    # PIE 检测: 通过 e_type (ET_DYN = 3 表示 PIE)
    e_type = struct.unpack_from("<H", data, 16)[0]
    protections["PIE"]["enabled"] = (e_type == 3)

    # Canary 检测: 搜索 __stack_chk_fail 字符串
    if b"__stack_chk_fail" in data:
        protections["Canary"]["enabled"] = True

    # RPATH/RUNPATH 检测
    if b"RPATH" in data or b"RUNPATH" in data:
        protections["RPATH"]["enabled"] = True

    lines.append("")
    lines.append("保护机制:")
    for key, val in protections.items():
        status = "✅ 启用" if val["enabled"] else "❌ 未启用"
        lines.append(f"  {key:8s}  {status}  ({val['desc']})")

    # 安全评分
    score = sum(1 for v in protections.values() if v["enabled"])
    lines.append(f"\n安全评分: {score}/5")
    if score >= 4:
        lines.append("提示: 保护全开，可能需要信息泄露配合利用")
    elif score <= 1:
        lines.append("提示: 几乎没有保护，可利用性较高")

    return "\n".join(lines)


# ── Pwntools 封装 ─────────────────────────────────────────────────

def _pwntools_wrapper(action: str, params: dict) -> str:
    """封装 pwntools 常用操作（如果可用）。"""
    try:
        import pwn
        HAS_PWN = True
    except ImportError:
        HAS_PWN = False

    if not HAS_PWN:
        # 输出 Python 代码模板代替
        templates = {
            "checksec": (
                "from pwn import *\n"
                "elf = ELF('./binary')\n"
                "print(elf.checksec())"
            ),
            "cyclic": (
                "from pwn import *\n"
                "pattern = cyclic(200)\n"
                "print(pattern)\n"
                "# 查找偏移: cyclic_find('kaaa')"
            ),
            "offset": (
                "from pwn import *\n"
                "# 给定 crash 地址，查找 cyclic 偏移\n"
                "offset = cyclic_find(0x6161616b)\n"
                "print(f'Offset: {offset}')"
            ),
            "elf_symbols": (
                "from pwn import *\n"
                "elf = ELF('./binary')\n"
                "print(elf.symbols)\n"
                "print(elf.got)\n"
                "print(elf.plt)"
            ),
        }
        code = templates.get(action, "")
        if code:
            return (
                f"当前环境未安装 pwntools。请安装: pip install pwntools\n\n"
                f"参考代码模板 ({action}):\n{code}"
            )
        return (
            "当前环境未安装 pwntools。请安装: pip install pwntools\n"
            "或使用远程服务器执行 Python 代码。"
        )

    # pwntools 已安装，直接执行
    try:
        if action == "cyclic":
            length = params.get("length", 200)
            pattern = pwn.cyclic(length)
            return f"Cyclic 模式 ({length} 字节):\n{pattern.decode('ascii', errors='replace')}"

        elif action == "offset":
            value = params.get("value", "")
            if value.startswith("0x"):
                val = int(value, 16)
            else:
                try:
                    val = pwn.pack(int(value))
                except Exception:
                    val = value.encode() if isinstance(value, str) else value
            offset = pwn.cyclic_find(val)
            return f"偏移: {offset}"

        elif action == "pack":
            value = int(params.get("value", "0"))
            bits = params.get("bits", 64)
            endian = params.get("endian", "little")
            packed = pwn.pack(value, bits=bits, endian=endian)
            return f"p64({value}) = {packed.hex()}"

        elif action == "unpack":
            data_hex = params.get("data", "")
            bits = params.get("bits", 64)
            data = bytes.fromhex(data_hex)
            val = pwn.unpack(data, bits=bits)
            return f"unpack({data_hex}) = {val} (0x{val:x})"

        else:
            return f"未知 pwntools 操作: {action}"

    except Exception as e:
        return f"pwntools 执行失败: {e}"


# ── 架构识别 ──────────────────────────────────────────────────────

def _identify_arch(path: str) -> str:
    """识别二进制文件的架构信息。"""
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except Exception as e:
        return f"读取失败: {e}"

    lines = [f"文件: {path}"]

    # ELF
    if head[:4] == b"\x7fELF":
        cls = "32-bit" if head[4] == 1 else "64-bit" if head[4] == 2 else "未知"
        endian = "小端" if head[5] == 1 else "大端"
        osabi_map = {0: "System V", 1: "HP-UX", 2: "NetBSD", 3: "Linux",
                     6: "Solaris", 9: "FreeBSD", 12: "AROS"}
        osabi = osabi_map.get(head[7], f"未知(0x{head[7]:02x})")
        e_type_map = {0: "NONE", 1: "REL (可重定位)", 2: "EXEC (可执行)",
                      3: "DYN (共享库/PIE)", 4: "CORE"}
        e_type = e_type_map.get(struct.unpack_from("<H", head, 16)[0], "未知")

        # 指令集 (e_machine)
        e_machine = struct.unpack_from("<H", head, 18)[0]
        machine_map = {
            0: "无", 2: "SPARC", 3: "x86", 8: "MIPS", 20: "PowerPC",
            21: "PowerPC64", 40: "ARM", 43: "SPARC v9", 50: "IA-64",
            62: "x86-64", 183: "AArch64", 243: "RISC-V",
            0xF7: "BPF", 0x28: "SuperH"
        }
        machine = machine_map.get(e_machine, f"未知 (0x{e_machine:04x})")

        lines.extend([
            f"格式: ELF {cls}",
            f"字节序: {endian}",
            f"ABI: {osabi}",
            f"类型: {e_type}",
            f"指令集: {machine}",
        ])

        # 入口点
        if cls.startswith("64"):
            entry = struct.unpack_from("<Q", head, 0x18)[0]
        else:
            entry = struct.unpack_from("<I", head, 0x18)[0]
        lines.append(f"入口点: 0x{entry:x}")

    # PE
    elif head[:2] == b"MZ":
        pe_offset = struct.unpack_from("<I", head, 0x3C)[0]
        if pe_offset < len(head):
            if head[pe_offset:pe_offset+4] == b"PE\x00\x00":
                machine = struct.unpack_from("<H", head, pe_offset + 4)[0]
                machine_map = {0x14c: "x86 (32位)", 0x8664: "x86-64 (64位)",
                               0x1c0: "ARM", 0xaa64: "AArch64", 0x1c4: "ARM Thumb"}
                lines.append(f"格式: PE (Windows)")
                lines.append(f"指令集: {machine_map.get(machine, f'未知 (0x{machine:04x})')}")

    # Mach-O
    elif head[:4] in (b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe"):
        lines.append("格式: Mach-O (32-bit) — macOS")
    elif head[:4] in (b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"):
        lines.append("格式: Mach-O (64-bit) — macOS")

    else:
        lines.append("未知二进制格式")

    return "\n".join(lines)


# ── 工具类 ──────────────────────────────────────────────────────

class BinaryAnalysisTool(BaseTool):
    """二进制分析工具 — ELF 保护检测、pwntools 封装、架构识别。"""
    modes = {"ctf"}

    @property
    def tags(self):
        return ("pwn", "binary", "exploit")

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "")
        path = arguments.get("path", "")
        params = arguments.get("params", {})

        if action == "checksec":
            if not path:
                return "错误: 需要文件路径"
            if not os.path.exists(path):
                alt = os.path.join("attachments", path)
                path = alt if os.path.exists(alt) else path
            return _check_elf_protections(path)

        elif action == "arch":
            if not path:
                return "错误: 需要文件路径"
            if not os.path.exists(path):
                alt = os.path.join("attachments", path)
                path = alt if os.path.exists(alt) else path
            return _identify_arch(path)

        elif action == "pwntools":
            return _pwntools_wrapper(
                params.get("sub_action", ""),
                params,
            )

        elif action == "ropgadget":
            return (
                "ROPgadget 是一个外部工具。用法:\n"
                "  ROPgadget --binary <file> [--only 'ret|pop|xor']\n"
                "  ROPgadget --binary <file> --depth 10\n"
                "请确保在安装了 ROPgadget 的环境中运行。\n"
                "安装: pip install ROPgadget"
            )

        elif action == "one_gadget":
            return (
                "one_gadget 是一个外部工具，用于查找 libc 中的 one-gadget RCE 地址。\n"
                "用法: one_gadget <libc.so>\n"
                "请确保在安装了 one_gadget 的环境中运行。\n"
                "安装: gem install one_gadget"
            )

        elif action == "patchelf":
            return (
                "patchelf 用于修改 ELF 的动态链接器和 RPATH。\n"
                "常见用法:\n"
                "  切换 libc: patchelf --set-interpreter <ld_path> --set-rpath <libc_dir> <binary>\n"
                "安装: apt install patchelf 或 pacman -S patchelf"
            )

        else:
            return (
                f"未知 action: {action}\n"
                "可用: checksec, arch, pwntools, ropgadget, one_gadget, patchelf"
            )

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "binary_analysis",
                "description": (
                    "二进制/PWN 分析工具。支持: "
                    "1) checksec — ELF 保护检测 (NX/Canary/PIE/RELRO); "
                    "2) arch — 二进制文件架构识别 (ELF/PE/Mach-O); "
                    "3) pwntools — cyclic/offset/pack/unpack, 需安装 pwntools; "
                    "4) ropgadget — ROPgadget 使用说明; "
                    "5) one_gadget — one_gadget 使用说明; "
                    "6) patchelf — patchelf 使用说明。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["checksec", "arch", "pwntools",
                                     "ropgadget", "one_gadget", "patchelf"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "二进制文件路径 (checksec/arch)",
                        },
                        "params": {
                            "type": "object",
                            "description": (
                                "pwntools 参数: {sub_action: 'cyclic'/'offset'/'pack'/'unpack', "
                                "length, value, bits, data, endian}"
                            ),
                        },
                    },
                    "required": ["action"],
                },
            },
        }
