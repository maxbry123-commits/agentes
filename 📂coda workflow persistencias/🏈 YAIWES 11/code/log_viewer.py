"""日志查看器 — 从 checkpoint / log 文件中读取并展示 Agent 执行过程。

Usage:
    python log_viewer.py list          # 列出所有会话
    python log_viewer.py last          # 查看最近会话
    python log_viewer.py show <index>  # 查看指定会话详情
    python log_viewer.py show <index> --steps 1-5   # 只看第 1-5 步
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ── 终端编码适配 ────────────────────────────────────────────────────────
if sys.stdout.encoding and "UTF" not in sys.stdout.encoding.upper():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── 路径 ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ── ANSI 颜色 / 样式 ─────────────────────────────────────────────────
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR_LINE = "\033[K"

W = 72  # 分隔线宽度


def e(s: str = "") -> str:
    """去除颜色标记，用于计算可见宽度。"""
    return re.sub(r"\033\[[0-9;]*m", "", s)


def c(text: str, *styles: str) -> str:
    """给文本上色。"""
    return f"{''.join(styles)}{text}{RESET}"


def separator(char: str = "─", title: str = "") -> str:
    """带标题的分隔线。"""
    if title:
        mid = f" {title} "
        left = char * ((W - len(e(mid))) // 2)
        right = char * (W - len(e(mid)) - len(left))
        return c(f"{left}{mid}{right}", DIM)
    return c(char * W, DIM)


def truncate(text: str, max_len: int = 200) -> str:
    """截断文本。"""
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "..."


def fmt_time(ts: int) -> str:
    """Unix 时间戳 → 本地时间字符串。"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


# ── 数据加载 ──────────────────────────────────────────────────────────

def load_all_sessions() -> List[Dict]:
    """从 checkpoint 目录加载所有会话。"""
    sessions = []
    if not os.path.isdir(CHECKPOINT_DIR):
        return sessions

    for fname in sorted(os.listdir(CHECKPOINT_DIR), reverse=True):
        if not fname.startswith("checkpoint_") or not fname.endswith(".json"):
            continue
        fpath = os.path.join(CHECKPOINT_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            agent_state = data.get("agent_state", {})
            memory = data.get("memory", {})
            history = memory.get("history", [])

            sessions.append({
                "file": fname,
                "path": fpath,
                "mode": meta.get("mode", "?"),
                "step_count": meta.get("step_count", 0),
                "created_at": meta.get("created_at", 0),
                "problem_text": meta.get("problem_text", ""),
                "current_phase": agent_state.get("current_phase", ""),
                "history": history,
                "journal_entries": memory.get("journal_entries", []),
                "consolidated_narrative": memory.get("consolidated_narrative", ""),
                "data": data,
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return sessions


# ── 命令: list ────────────────────────────────────────────────────────

def cmd_list(_args):
    sessions = load_all_sessions()
    if not sessions:
        print(f"\n  {c('暂无会话记录。', DIM)}")
        print(f"  运行 python main.py 解题后，checkpoint 会自动保存在 {CHECKPOINT_DIR}")
        return

    print(f"\n  {c('可用会话', BOLD)} ({len(sessions)} 个)\n")

    # 表头
    header = f"  {c('ID', BOLD):>3s}  {c('模式', BOLD):<8s}  {c('步数', BOLD):>5s}  {c('阶段', BOLD):<8s}  {c('时间', BOLD):<20s}  {c('题目', BOLD)}"
    print(header)
    print(c("  " + "─" * (len(e(header)) - 2), DIM))

    for i, s in enumerate(sessions, 1):
        mode_tag = c("CTF", CYAN) if s["mode"] == "ctf" else c("PENTEST", RED)
        phase_tag = {
            "recon": c("recon", BLUE),
            "exploit": c("exploit", YELLOW),
            "report": c("report", GREEN),
        }.get(s["current_phase"], c(s["current_phase"] or "-", DIM))

        problem_preview = truncate(s["problem_text"].replace("\n", " "), 60)
        ts = fmt_time(s["created_at"]) if s["created_at"] else "-"

        print(
            f"  {c(str(i), BOLD):>3s}  "
            f"{mode_tag:<8s}  "
            f"{c(str(s['step_count']), BOLD):>5s}  "
            f"{phase_tag:<8s}  "
            f"{c(ts, DIM):<20s}  "
            f"{problem_preview}"
        )
    print()


# ── 命令: show ────────────────────────────────────────────────────────

def extract_analysis_summary(analysis: dict) -> str:
    """从分析结果中提取关键信息。"""
    if not analysis or not isinstance(analysis, dict):
        return ""

    parts = []
    analysis_text = analysis.get("analysis", "")
    if analysis_text:
        parts.append(truncate(analysis_text, 200))

    if analysis.get("vulnerability_found"):
        vuln = analysis.get("vulnerability", {})
        sev = vuln.get("severity", "?")
        vtype = vuln.get("type", "?")
        parts.append(f"{c('漏洞发现', RED)}: [{sev}] {vtype}")

    if analysis.get("flag_found"):
        parts.append(f"{c('Flag发现!', BOLD)}{c(analysis.get('flag', ''), YELLOW)}")

    if analysis.get("no_progress"):
        parts.append(c("[无进展]", YELLOW))

    if analysis.get("terminate") or analysis.get("terminate_all"):
        parts.append(c("[建议终止]", RED))

    if analysis.get("new_info"):
        parts.append(c("[新信息]", GREEN))

    return " | ".join(parts)


def format_tool_args(tool_args) -> str:
    """格式化工具参数为可读字符串。"""
    if not tool_args:
        return "-"

    if isinstance(tool_args, list):
        items = []
        for tc in tool_args:
            name = tc.get("tool_name") or tc.get("name", "?")
            args = tc.get("arguments", {})
            args_str = ", ".join(f"{k}={v}" for k, v in args.items() if v)
            items.append(f"{name}({args_str})" if args_str else name)
        return ", ".join(items)

    if isinstance(tool_args, dict):
        return json.dumps(tool_args, ensure_ascii=False)

    return str(tool_args)


def show_step(step: dict, step_num: int):
    """打印单个步骤。"""
    tool_name = step.get("tool_name", "")
    think = step.get("think", "")
    tool_args = step.get("tool_args", "")
    output = step.get("output", "")
    analysis = step.get("analysis", {})

    # 步骤标题
    step_title = f"Step {step_num}"
    if tool_name:
        step_title += f"  [{tool_name}]"

    print(f"\n  {c(step_title, BOLD)}")
    print(f"  {separator('─')}")

    # Think
    if think:
        print(f"  {c('思考:', BLUE)} {truncate(think, 500)}")

    # 工具参数
    args_str = format_tool_args(tool_args)
    if args_str and args_str != "-":
        print(f"  {c('参数:', DIM)} {args_str}")

    # 输出（截断）
    if output:
        truncated = truncate(output, 600)
        # 对过长的输出做进一步截断，但显示行数
        lines = truncated.split("\n")
        if len(lines) > 12:
            lines = lines[:12] + [c("  ... (输出已截断, 共 {len(output)} 字符)", DIM)]
        print(f"  {c('输出:', DIM)}")
        for line in lines:
            print(f"    {line}")

    # 分析摘要
    analysis_summary = extract_analysis_summary(analysis)
    if analysis_summary:
        print(f"  {c('分析:', GREEN)} {analysis_summary}")


def cmd_show(args):
    sessions = load_all_sessions()
    if not sessions:
        print(f"\n  {c('暂无会话记录。', DIM)}")
        return

    # 确定索引
    if args.show == "last" or (not args.show and sessions):
        idx = 0
    elif args.show:
        try:
            idx = int(args.show) - 1
            if idx < 0 or idx >= len(sessions):
                print(f"\n  {c('错误:', RED)} 索引超出范围 (1-{len(sessions)})")
                return
        except ValueError:
            print(f"\n  {c('错误:', RED)} 无效索引: {args.show}")
            return

    s = sessions[idx]

    # ── 会话头部信息 ──
    mode_label = "CTF 解题" if s["mode"] == "ctf" else "渗透测试"
    phase_label = s["current_phase"] or "未知"

    print(f"\n  {c('会话详情', BOLD)} (ID: {idx + 1})")
    print(f"  {separator('=')}")
    print(f"  {c('模式:', BOLD)} {mode_label}")
    print(f"  {c('阶段:', BOLD)} {phase_label}")
    print(f"  {c('总步数:', BOLD)} {s['step_count']}")
    print(f"  {c('时间:', BOLD)} {fmt_time(s['created_at'])}")
    print(f"  {c('文件:', DIM)} {os.path.basename(s['path'])}")
    if s["problem_text"]:
        problem_preview = truncate(s["problem_text"].replace("\n", " "), 80)
        print(f"  {c('题目:', BOLD)} {problem_preview}")

    # ── 解题叙事 ──
    narrative = s.get("consolidated_narrative", "")
    if narrative:
        print(f"\n  {c('解题叙事', BOLD)}")
        print(f"  {separator('─')}")
        print(f"  {truncate(narrative, 500)}")
    # ── 最近日志 ──
    entries = s.get("journal_entries", [])
    if entries:
        print(f"\n  {c('最近日志条目', BOLD)}")
        print(f"  {separator('─')}")
        for entry in entries[-3:]:
            print(f"  {c('•', DIM)} {truncate(entry.replace(chr(10), ' '), 200)}")

    # ── 步骤列表 ──
    history = s["history"]
    if not history:
        print(f"\n  {c('暂无步骤记录。', DIM)}")
        return

    print(f"\n  {c(f'执行步骤 ({len(history)} 步)', BOLD)}")
    print(f"  {separator('=')}")

    # 步骤范围过滤
    step_start = 0
    step_end = len(history)

    if args.steps:
        try:
            parts = args.steps.split("-")
            if len(parts) == 1:
                step_start = max(0, int(parts[0]) - 1)
                step_end = step_start + 1
            elif len(parts) == 2:
                step_start = max(0, int(parts[0]) - 1)
                step_end = min(len(history), int(parts[1]))
        except ValueError:
            pass

    for i in range(step_start, step_end):
        show_step(history[i], i + 1)

    print(f"\n  {separator('=')}")
    print(f"  {c(f'共 {len(history)} 步, 显示 {step_start+1}-{step_end}', DIM)}")
    print()


# ── 入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CTF Agent 日志查看器 — 从 checkpoint 回溯 Agent 执行过程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python log_viewer.py list              # 列出所有会话\n"
            "  python log_viewer.py last              # 查看最近会话\n"
            "  python log_viewer.py show 2            # 查看第 2 个会话\n"
            "  python log_viewer.py show 1 --steps 3-8  # 只看第 3-8 步\n"
        ),
    )
    parser.add_argument(
        "command", nargs="?", default="list",
        choices=["list", "show", "last"],
        help="操作: list=列出会话, show=查看详情, last=最近会话",
    )
    parser.add_argument(
        "--steps", "-s",
        help="步骤范围 (如: 3 或 3-8)",
    )
    parser.add_argument(
        "show", nargs="?", default=None,
        help="会话 ID (show 命令用)",
    )
    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command in ("show", "last"):
        cmd_show(args)


if __name__ == "__main__":
    main()
