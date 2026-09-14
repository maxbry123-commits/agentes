"""技能加载器 — 扫描 skills/ 目录，生成索引和提取内容。"""

import os
import re
import yaml
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")


def _parse_skill_md(filepath: str) -> Optional[Dict]:
    """解析 SKILL.md 文件的 YAML frontmatter 和 markdown 正文。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"读取 {filepath} 失败: {e}")
        return None

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not m:
        logger.warning(f"{filepath} 缺少有效的 YAML frontmatter")
        return None

    try:
        frontmatter = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        logger.warning(f"{filepath} YAML 解析失败: {e}")
        return None

    return {
        "name": frontmatter.get("name", ""),
        "description": frontmatter.get("description", ""),
        "body": m.group(2).strip(),
    }


def list_skills() -> List[str]:
    """列出所有可用的 skill 名称。"""
    if not os.path.isdir(SKILLS_DIR):
        return []
    skills = []
    for dirname in sorted(os.listdir(SKILLS_DIR)):
        filepath = os.path.join(SKILLS_DIR, dirname, "SKILL.md")
        if os.path.isfile(filepath):
            skills.append(dirname)
    return skills


def load_skill_index() -> str:
    """生成轻量技能索引（注入 Prompt 用，约 50 行）。"""
    if not os.path.isdir(SKILLS_DIR):
        return ""

    lines = []
    for dirname in sorted(os.listdir(SKILLS_DIR)):
        filepath = os.path.join(SKILLS_DIR, dirname, "SKILL.md")
        if not os.path.isfile(filepath):
            continue
        parsed = _parse_skill_md(filepath)
        if not parsed:
            continue
        desc = parsed["description"].replace("\n", " ").strip()
        if len(desc) > 120:
            desc = desc[:117] + "..."
        lines.append(f"- {parsed['name']}: {desc}")

    if not lines:
        return ""
    return "\n".join(lines)


def load_hack_router() -> str:
    """加载 hack/SKILL.md 的现象→漏洞类型路由表。"""
    filepath = os.path.join(SKILLS_DIR, "hack", "SKILL.md")
    if not os.path.isfile(filepath):
        return ""

    parsed = _parse_skill_md(filepath)
    if not parsed:
        return ""

    body = parsed["body"]
    m = re.search(
        r"(\| 现象 \| 优先方向 \|.*?)(?:\n\n##|\n###|\n\n\*\*|\Z)",
        body, re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return ""


def load_skill_context() -> str:
    """组装完整的技能上下文块（索引 + 路由表 + 使用说明），注入到 Prompt。"""
    index = load_skill_index()
    router = load_hack_router()

    if not index:
        return ""

    parts = [
        "## 可用安全技能库",
        "",
        "以下技能库包含结构化的漏洞检测和利用方法论。",
        "需要某个技能的详细知识时，在知识库中搜索对应技能名即可获取完整的手册。",
        "",
        index,
    ]

    if router:
        parts.extend([
            "",
            "## 现象→漏洞路由表",
            "",
            "根据观察到的现象，优先选择对应的攻击方向:",
            "",
            router,
        ])

    parts.extend([
        "",
        "使用原则:",
        "1. 先根据现象查路由表，确定最可能的漏洞类型",
        "2. 再加载对应技能的方法论指导具体测试步骤",
        "3. 不要盲目尝试所有技能——优先测试与已观察到的现象匹配的方向",
        "4. 如果当前方向连续 2 次无进展，查阅路由表切换到下一个可能方向",
    ])

    return "\n".join(parts)


def load_all_skills() -> List[Dict]:
    """加载所有 skill 的完整数据（供 seed 使用）。"""
    if not os.path.isdir(SKILLS_DIR):
        return []

    skills = []
    for dirname in sorted(os.listdir(SKILLS_DIR)):
        filepath = os.path.join(SKILLS_DIR, dirname, "SKILL.md")
        if not os.path.isfile(filepath):
            continue
        parsed = _parse_skill_md(filepath)
        if not parsed:
            continue
        skills.append(parsed)
    return skills
