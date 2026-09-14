"""基准测试用例定义 — 描述一个 CTF 题目或渗透测试场景。"""

import os
import re
import yaml
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkCase:
    """单个基准测试用例。"""

    id: str
    name: str
    description: str
    flag_regex: str = r"flag\{[^}]+\}"
    category: str = "unknown"
    difficulty: str = "medium"
    mode: str = "ctf"
    timeout: int = 600
    files: dict = field(default_factory=dict)
    tags: list = field(default_factory=list)

    @property
    def flag_pattern(self) -> re.Pattern:
        return re.compile(self.flag_regex, re.IGNORECASE)

    def matches_flag(self, text: Optional[str]) -> bool:
        """判断文本是否匹配预期的 flag 格式。"""
        if not text:
            return False
        return bool(self.flag_pattern.search(text))


def load_case(path: str) -> BenchmarkCase:
    """从 YAML 文件加载单个用例。"""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    required = ("id", "name", "description")
    for key in required:
        if key not in data:
            raise ValueError(f"{path}: 缺少必填字段 '{key}'")
    return BenchmarkCase(**data)


def discover_cases(cases_dir: str = None) -> list[BenchmarkCase]:
    """扫描目录下的所有 .yaml/.yml 用例文件。"""
    if cases_dir is None:
        cases_dir = os.path.join(os.path.dirname(__file__), "cases")
    if not os.path.isdir(cases_dir):
        logger.warning("用例目录不存在: %s", cases_dir)
        return []

    cases = []
    for fname in sorted(os.listdir(cases_dir)):
        if not (fname.endswith(".yaml") or fname.endswith(".yml")):
            continue
        fpath = os.path.join(cases_dir, fname)
        try:
            case = load_case(fpath)
            cases.append(case)
            logger.info("加载用例: %s (%s)", case.id, case.name)
        except Exception as e:
            logger.error("加载用例失败 %s: %s", fname, e)
    return cases
