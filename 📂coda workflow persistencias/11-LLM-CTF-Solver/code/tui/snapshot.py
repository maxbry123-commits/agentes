"""StepSnapshot — 每步执行结果的不可变快照，从 solve() worker 线程推送到 TUI 主线程。"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StepSnapshot:
    step_num: int
    phase: str = "recon"               # recon / exploit / report
    think: str = ""                    # LLM 思考内容 (截断到 500 字符)
    tool_calls: list = field(default_factory=list)  # [{tool_name, arguments}]
    output: str = ""                   # 工具输出 (截断到 8192)
    analysis: str = ""                 # LLM 分析结果 (截断到 1024)
    flag_found: bool = False
    flag_value: str = ""
    vulnerability: Optional[dict] = None  # 渗透模式的漏洞 dict
    cache_stats: dict = field(default_factory=dict)  # {l1, l2, rag}
    stuck_warning: bool = False
    attack_surface_summary: str = ""   # get_summary() 截断到 2048
    token_stats: dict = field(default_factory=dict)  # {prompt, completion, total, cost, calls}
