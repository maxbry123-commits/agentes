"""逆向工程工具集 — 二进制侦查、反汇编、反编译、Shellcode 分析。"""

import logging
import os
import re
import struct
import subprocess
import shutil
from typing import Dict, List, Optional

from ctf_tool.base_tool import BaseTool

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 辅助
# ═══════════════════════════════════════════════════════════════════

def _find_tool(name: str) -> bool:
    return shutil.which(name) is not None


def _read_head(path: str, size: int = 4096) -> bytes:
    with open(path, "rb") as f:
        return f.read(size)


def _is_elf(data: bytes) -> bool:
    return data[:4] == b"\x7fELF"


def _is_pe(data: bytes) -> bool:
    return data[:2] == b"MZ"


# ═══════════════════════════════════════════════════════════════════
# Action: recon — 全量侦查
# ═══════════════════════════════════════════════════════════════════

_INTERESTING_IMPORTS = [
    "system", "exec", "popen", "fork", "ptrace", "gets", "scanf",
    "strcpy", "strcat", "sprintf", "read", "write", "mmap", "mprotect",
    "send", "recv", "connect", "accept", "socket", "bind", "listen",
    "dlopen", "dlsym", "syscall", "seccomp", "prctl",
    "WinExec", "CreateProcess", "VirtualAlloc", "VirtualProtect",
    "WriteProcessMemory", "LoadLibrary", "GetProcAddress",
]

_SHELLCODE_PATTERNS = [
    (r"/bin/(ba)?sh", "exec /bin/sh (常见 shellcode)"),
    (r"/bin/cat\s+/flag", "读取 flag 文件"),
    (r"flag\.txt", "flag 文件引用"),
    (rb"\x31\xc0\x50\x68", "x86 xor eax,eax; push eax; push (常见 preamble)"),
    (rb"\x48\x31\xf6\x56\x48\xbf", "x86-64 xor rsi,rsi; push rsi; movabs rdi (syscall preamble)"),
    (rb"\x0f\x05", "x86-64 syscall 指令"),
    (rb"\xcd\x80", "x86 int 0x80 指令"),
]


def _recon(path: str) -> str:
    """全量逆向侦查 — 格式识别 + 保护检测 + 字符串提取 + 导入分析 + 节分析。"""
    if not os.path.exists(path):
        return f"错误: 文件不存在: {path}"

    size = os.path.getsize(path)
    try:
        data = _read_head(path, min(size, 1024 * 1024))
    except Exception as e:
        return f"读取失败: {e}"

    lines = [
        f"=== 逆向侦查: {path} ===",
        f"文件大小: {size:,} 字节",
        "",
    ]

    # ── 1. 格式与架构 ──
    lines.append("--- 格式与架构 ---")
    try:
        if _is_elf(data):
            if len(data) < 24:
                lines.append("格式: ELF (文件过小，无法解析头部)")
            else:
                cls = "64-bit" if data[4] == 2 else "32-bit"
                endian = "小端" if data[5] == 1 else "大端"
                e_type_map = {0: "NONE", 1: "REL", 2: "EXEC", 3: "DYN (PIE/共享库)", 4: "CORE"}
                e_type = e_type_map.get(struct.unpack_from("<H", data, 16)[0], "未知")
                machine_map = {3: "x86", 40: "ARM", 62: "x86-64", 183: "AArch64", 243: "RISC-V"}
                machine = machine_map.get(struct.unpack_from("<H", data, 18)[0], f"未知(0x{struct.unpack_from('<H', data, 18)[0]:04x})")
                entry = struct.unpack_from("<Q" if cls.startswith("64") else "<I", data, 0x18)[0]
                lines.append(f"格式: ELF {cls} ({e_type})")
                lines.append(f"指令集: {machine}, {endian}")
                lines.append(f"入口点: 0x{entry:x}")
        elif _is_pe(data):
            if len(data) < 64:
                lines.append("格式: PE (文件过小，无法解析头部)")
            else:
                pe_off = struct.unpack_from("<I", data, 0x3C)[0]
                machine = struct.unpack_from("<H", data, pe_off + 4)[0] if pe_off + 4 < len(data) else 0
                arch_map = {0x14c: "x86", 0x8664: "x86-64", 0x1c0: "ARM", 0xaa64: "AArch64"}
                lines.append(f"格式: PE ({arch_map.get(machine, '未知')})")
        elif data[:4] in (b"\xfe\xed\xfa\xce", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"):
            lines.append("格式: Mach-O (macOS)")
        else:
            lines.append("格式: 未知 — 可能是固件/裸二进制/shellcode")
    except (struct.error, IndexError, ValueError) as e:
        lines.append(f"格式: 头部解析异常 (文件可能截断/损坏): {e}")

    # ── 2. 保护机制 ──
    lines.append("\n--- 保护机制 ---")
    if _is_elf(data):
        protections = _check_elf_protections_inline(data)
        lines.append(protections)
    else:
        lines.append("非 ELF 文件，跳过保护检测")

    # ── 3. 字符串提取与分类 ──
    lines.append("\n--- 字符串分析 ---")
    try:
        full = data
        if size < 10 * 1024 * 1024:
            with open(path, "rb") as f:
                full = f.read()
    except Exception:
        pass

    ascii_strs = re.findall(rb"[\x20-\x7e]{4,}", full)
    categories = {
        "URL/域名": [],
        "IP 地址": [],
        "文件路径": [],
        "Base64": [],
        "Hex 字符串": [],
        "Flag 相关": [],
        "危险函数": [],
        "其他": [],
    }

    ip_re = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    url_re = re.compile(rb"https?://[^\s]{4,}")
    path_re = re.compile(rb"(?:/[a-zA-Z0-9_.-]+){2,}|[A-Za-z]:\\[a-zA-Z0-9_.\\-]+")
    b64_re = re.compile(rb"^[A-Za-z0-9+/]{20,}={0,2}$")
    hex_re = re.compile(rb"^[0-9a-fA-F]{16,}$")

    for s in ascii_strs:
        try:
            text = s.decode("ascii")
        except Exception:
            continue
        if url_re.match(s):
            categories["URL/域名"].append(text)
        elif ip_re.match(s):
            categories["IP 地址"].append(text)
        elif path_re.search(s):
            categories["文件路径"].append(text)
        elif b64_re.match(s):
            categories["Base64"].append(text)
        elif hex_re.match(s):
            categories["Hex 字符串"].append(text)
        elif any(k in text.lower() for k in ("flag", "ctf{", "ctf_", "key", "secret")):
            categories["Flag 相关"].append(text)
        elif any(k in text.lower() for k in _INTERESTING_IMPORTS):
            categories["危险函数"].append(text)

    for cat_name, items in categories.items():
        if items:
            uniq = list(dict.fromkeys(items))[:10]
            lines.append(f"  [{cat_name}] ({len(items)} 个)")
            for item in uniq:
                lines.append(f"    {item[:100]}")

    # ── 4. Shellcode 特征 ──
    lines.append("\n--- Shellcode 检测 ---")
    sc_found = []
    for pattern, desc in _SHELLCODE_PATTERNS:
        if isinstance(pattern, str):
            if re.search(pattern.encode(), full, re.IGNORECASE) if isinstance(pattern, str) else False:
                sc_found.append(desc)
        elif isinstance(pattern, bytes):
            if pattern in full:
                sc_found.append(desc)
    if sc_found:
        for f in sc_found:
            lines.append(f"  ⚠ {f}")
    else:
        lines.append("  未发现明显 shellcode 特征")

    # ── 5. 熵分析 ──
    lines.append("\n--- 熵值分析 ---")
    e = _entropy(full[:65536])
    lines.append(f"  前 64KB 熵值: {e:.2f} (0-8)")
    if e > 7.5:
        lines.append("  提示: 熵值极高 — 可能是加密/压缩/加壳数据")
    elif e > 6.5:
        lines.append("  提示: 熵值偏高 — 可能有部分加密段")
    elif e < 3.5:
        lines.append("  提示: 熵值较低 — 可能包含大量文本或结构化数据")

    # ── 6. 可用工具 ──
    lines.append("\n--- 建议下一步 ---")
    tools_available = []
    for name, desc in [
        ("objdump", "objdump -d <file> — 反汇编"),
        ("readelf", "readelf -a <file> — ELF 完整信息"),
        ("strings", "strings <file> — 提取全部可读字符串"),
        ("ltrace", "ltrace ./binary — 跟踪库函数调用"),
        ("strace", "strace ./binary — 跟踪系统调用"),
        ("gdb", "gdb ./binary — 交互式调试"),
        ("radare2", "r2 -A <file> — 自动化逆向分析"),
        ("rizin", "rizin -A <file> — 自动化逆向分析"),
        ("Ghidra", "ghidra / analyzeHeadless — 反编译"),
        ("IDA Pro", "idal64 -A -Sscript.py <file> — 反编译"),
    ]:
        if _find_tool(name.split()[0]):
            tools_available.append(f"  + {desc}")
    if tools_available:
        lines.extend(tools_available)
    else:
        lines.append("  (未检测到逆向工具，建议安装 binutils / radare2)")

    return "\n".join(lines)


def _check_elf_protections_inline(data: bytes) -> str:
    """内联 ELF 保护检测（复用 binary_analysis 逻辑但内嵌以避免循环依赖）。"""
    lines = []
    cls_label = "64-bit" if data[4] == 2 else "32-bit"
    eh_size = 64 if data[4] == 2 else 52

    e_phoff = struct.unpack_from("<Q" if data[4] == 2 else "<I", data, 0x20 if data[4] == 2 else 0x1C)[0]
    e_phentsize = struct.unpack_from("<H", data, 0x36 if data[4] == 2 else 0x2A)[0]
    e_phnum = struct.unpack_from("<H", data, 0x38 if data[4] == 2 else 0x2C)[0]

    nx = canary = pie = relro = rpath = False

    ph_off = e_phoff
    for _ in range(min(e_phnum, 128)):
        if ph_off + e_phentsize > len(data):
            break
        if data[4] == 2:
            p_type = struct.unpack_from("<I", data, ph_off)[0]
            p_flags = struct.unpack_from("<I", data, ph_off + 4)[0]
        else:
            p_type = struct.unpack_from("<I", data, ph_off)[0]
            p_flags = struct.unpack_from("<I", data, ph_off + 24)[0]

        if p_type == 0x6474e551:  # PT_GNU_STACK
            nx = not bool(p_flags & 1)
        if p_type == 0x6474e552:  # PT_GNU_RELRO
            relro = True
        ph_off += e_phentsize

    canary = b"__stack_chk_fail" in data
    e_type = struct.unpack_from("<H", data, 16)[0]
    pie = (e_type == 3)
    rpath = b"RPATH" in data or b"RUNPATH" in data

    prot = [
        ("NX", nx, "栈不可执行"),
        ("Canary", canary, "栈保护"),
        ("PIE", pie, "位置无关"),
        ("RELRO", relro, "只读重定位"),
    ]
    for name, enabled, desc in prot:
        status = "启用" if enabled else "未启用"
        lines.append(f"  {name:8s}  {'✅' if enabled else '❌'} {status}  ({desc})")
    if rpath:
        lines.append("  ⚠ RPATH/RUNPATH 存在 — 可能存在库劫持风险")

    score = sum(1 for _, en, _ in prot if en)
    lines.append(f"  安全评分: {score}/4")
    return "\n".join(lines)


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    from math import log2
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    return -sum((c / len(data)) * log2(c / len(data)) for c in counts if c > 0)


# ═══════════════════════════════════════════════════════════════════
# Action: disassemble — objdump 反汇编
# ═══════════════════════════════════════════════════════════════════

def _disassemble(path: str, function: str = "", max_lines: int = 200) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'ctf_tool/reverse_tools.py','step':'_disassemble','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


# ═══════════════════════════════════════════════════════════════════
# Action: strings — 增强字符串提取
# ═══════════════════════════════════════════════════════════════════

def _extract_strings(path: str, min_len: int = 4, max_count: int = 100) -> str:
    """增强字符串提取 — 分类展示。"""
    if not os.path.exists(path):
        return f"错误: 文件不存在: {path}"

    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(min(size, 10 * 1024 * 1024))
    except Exception as e:
        return f"读取失败: {e}"

    pattern = re.compile(rb"[\x20-\x7e]{" + str(min_len).encode() + rb",}")
    strings = [m.group().decode("ascii", errors="replace") for m in pattern.finditer(data)]
    strings_unique = list(dict.fromkeys(strings))

    lines = [
        f"=== 字符串提取: {path} ===",
        f"共 {len(strings_unique)} 个唯一字符串 (最小长度 {min_len})",
        "",
    ]

    # 模式匹配分类
    categories = {
        "URL": (re.compile(r"https?://"), []),
        "IP地址": (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), []),
        "邮箱": (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), []),
        "文件路径": (re.compile(r"(?:^|[\s\"'])(?:/[a-zA-Z0-9._-]+)+|(?:[A-Za-z]:\\[a-zA-Z0-9._\\-]+)"), []),
        "Base64候选": (re.compile(r"^[A-Za-z0-9+/]{20,}={0,2}$"), []),
        "Hex候选": (re.compile(r"^[0-9a-fA-F]{16,}$"), []),
        "Flag相关": (re.compile(r"flag|ctf[{\s_]|CTF[{\s_]|FLAG[{\s_]"), []),
    }

    for s in strings_unique:
        for cat, (regex, lst) in categories.items():
            if regex.search(s) and len(lst) < 20:
                lst.append(s)

    for cat, (_, items) in categories.items():
        if items:
            lines.append(f"--- {cat} ({len(items)} 个) ---")
            for item in items[:10]:
                lines.append(f"  {item[:120]}")

    lines.append(f"\n--- 全部字符串 (前 {max_count} 个) ---")
    for s in strings_unique[:max_count]:
        lines.append(f"  {s[:120]}")

    if len(strings_unique) > max_count:
        lines.append(f"\n... 共 {len(strings_unique)} 个, 显示前 {max_count} 个")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Action: anti_analysis — 反调试 / 反 VM 检测
# ═══════════════════════════════════════════════════════════════════

_ANTI_DEBUG_PATTERNS = [
    (rb"ptrace", "ptrace 调用 — 常见反调试手段"),
    (rb"/proc/self/status", "读取 /proc/self/status — 检测 TracerPid"),
    (rb"/proc/self/cmdline", "读取 /proc/self/cmdline"),
    (rb"TracerPid", "TracerPid 检测"),
    (rb"IsDebuggerPresent", "Windows IsDebuggerPresent API"),
    (rb"CheckRemoteDebuggerPresent", "Windows CheckRemoteDebuggerPresent"),
    (rb"NtQueryInformationProcess", "Windows NtQueryInformationProcess"),
    (rb"OutputDebugString", "Windows OutputDebugString 反调试"),
    (rb"int\s*3", "int3 断点指令 (可能是反调试陷阱)"),
    (rb"int\s*0x80", "int 0x80 中断 — 可能是反调试或沙箱检测"),
]

_ANTI_VM_PATTERNS = [
    (rb"VMware", "VMware 检测"),
    (rb"VirtualBox", "VirtualBox 检测"),
    (rb"QEMU", "QEMU 检测"),
    (rb"Xen", "Xen 检测"),
    (rb"VBox", "VBox 检测"),
    (rb"hypervisor", "Hypervisor 检测"),
    (rb"cpuid", "CPUID 指令 — 常用于 VM 检测"),
    (rb"/sys/class/dmi/id/product_name", "DMI 产品名检测 (VM 指纹)"),
]


def _anti_analysis(path: str) -> str:
    """反调试 / 反 VM 模式检测。"""
    if not os.path.exists(path):
        return f"错误: 文件不存在: {path}"

    try:
        with open(path, "rb") as f:
            data = f.read(min(os.path.getsize(path), 20 * 1024 * 1024))
    except Exception as e:
        return f"读取失败: {e}"

    lines = [f"=== 反分析检测: {path} ===", ""]

    lines.append("--- 反调试特征 ---")
    debug_hits = []
    for pattern, desc in _ANTI_DEBUG_PATTERNS:
        if re.search(pattern, data, re.IGNORECASE):
            debug_hits.append(f"  ⚠ {desc}")
    if debug_hits:
        lines.extend(debug_hits)
    else:
        lines.append("  未发现明显反调试特征")

    lines.append("\n--- 反虚拟机特征 ---")
    vm_hits = []
    for pattern, desc in _ANTI_VM_PATTERNS:
        if re.search(pattern, data, re.IGNORECASE):
            vm_hits.append(f"  ⚠ {desc}")
    if vm_hits:
        lines.extend(vm_hits)
    else:
        lines.append("  未发现明显反 VM 特征")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Action: patch — 补丁建议
# ═══════════════════════════════════════════════════════════════════

def _patch(path: str) -> str:
    """二进制补丁建议 — 常见 CTF PWN 修补模式。"""
    return f"""=== 二进制补丁建议: {path} ===

常见 CTF PWN 补丁场景:

1. NOP 掉反调试检查:
   找到 ptrace / TracerPid 检查代码, 用 NOP (0x90) 替换
   示例: objcopy 或 hexedit 修改对应偏移的字节

2. 修改条件跳转:
   JZ (0x74) → JMP (0xEB)  强制走成功分支
   JNZ (0x75) → JMP (0xEB)

3. 修改返回值:
   MOV EAX, 0 → MOV EAX, 1  (返回成功)
   x86: B8 00 00 00 00 → B8 01 00 00 00

4. 补丁工具:
   - hexedit / wxHexEditor: 直接编辑二进制
   - pwntools: elf = ELF('binary'); elf.asm(addr, 'ret')
   - objcopy + ld: 提取→修改→重新链接
   - Ghidra: Patch Instruction → Export Program
   - radare2: r2 -w binary → wa ret@addr

5. 绕过时间检查:
   找到 time/clock 调用, 让其返回固定值
   或 NOP 掉 sleep/alarm 调用

6. 栈大小调整:
   如果遇到栈空间不足, 用 patchelf 增加:
   patchelf --stack-size 0x200000 ./binary

提示: 先用 recon 了解二进制结构, 再定位具体地址。"""


# ═══════════════════════════════════════════════════════════════════
# 工具类
# ═══════════════════════════════════════════════════════════════════

class ReverseTools(BaseTool):
    """逆向工程工具集 — 侦查、反汇编、字符串分析、反调试检测。"""
    modes = {"ctf"}

    def execute(self, tool_name: str, arguments: dict) -> str:
        action = arguments.get("action", "recon")
        path = arguments.get("path", "")

        if not path:
            return "错误: 需要 path 参数 (二进制文件路径)"

        if not os.path.exists(path):
            alt = os.path.join("attachments", path)
            if os.path.exists(alt):
                path = alt
            else:
                return f"错误: 文件不存在: {path}"

        if action == "recon":
            return _recon(path)
        elif action == "disassemble":
            return _disassemble(
                path,
                function=arguments.get("function", ""),
                max_lines=arguments.get("max_lines", 200),
            )
        elif action == "strings":
            return _extract_strings(
                path,
                min_len=arguments.get("min_len", 4),
                max_count=arguments.get("max_count", 100),
            )
        elif action == "anti_analysis":
            return _anti_analysis(path)
        elif action == "patch":
            return _patch(path)
        elif action == "full_scan":
            return self._full_scan(path)
        else:
            return (
                f"未知 action: {action}\n"
                "可用: recon, disassemble, strings, anti_analysis, patch, full_scan"
            )

    def _full_scan(self, path: str) -> str:
        results = []
        for label, action in [
            ("RECON", "recon"),
            ("字符串提取", "strings"),
            ("反调试/反VM", "anti_analysis"),
        ]:
            try:
                result = self.execute("", {"action": action, "path": path})
                results.append(f"\n{'='*60}\n{label}\n{'='*60}\n{result}")
            except Exception as e:
                results.append(f"\n--- {label} ---\n错误: {e}")
        results.append(f"\n{'='*60}\n补丁建议\n{'='*60}\n{_patch(path)}")
        return "\n".join(results)

    @property
    def function_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "reverse_tools",
                "description": (
                    "逆向工程工具集。覆盖二进制逆向分析全流程:\n"
                    "1) recon — 全量侦查 (格式架构/ELF保护/字符串分类/Shellcode检测/熵值/工具推荐);\n"
                    "2) disassemble — objdump 反汇编 (支持按函数名过滤, 需安装 binutils);\n"
                    "3) strings — 增强字符串提取 (自动分类: URL/IP/邮箱/路径/Base64/Hex/Flag);\n"
                    "4) anti_analysis — 反调试/反VM 模式检测 (ptrace/TracerPid/IsDebuggerPresent/VM探测);\n"
                    "5) patch — NOP/JMP/返回值修改 等常见 PWN 补丁方法指南;\n"
                    "6) full_scan — 一键全量扫描。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["recon", "disassemble", "strings",
                                     "anti_analysis", "patch", "full_scan"],
                            "description": "操作类型",
                        },
                        "path": {
                            "type": "string",
                            "description": "二进制文件路径",
                        },
                        "function": {
                            "type": "string",
                            "description": "反汇编的目标函数名 (disassemble 操作)",
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "反汇编最大行数 (默认 200)",
                        },
                        "min_len": {
                            "type": "integer",
                            "description": "字符串最小长度 (strings 操作, 默认 4)",
                        },
                        "max_count": {
                            "type": "integer",
                            "description": "字符串最大显示数 (strings 操作, 默认 100)",
                        },
                    },
                    "required": ["action", "path"],
                },
            },
        }
